from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.dateparse import parse_datetime
from .helpers import check_for_reorg, get_missing_heights_repr, get_prefetched_header_and_block_data
from .models import Block, BlockHeader, Output, Kernel, Input
from .node import NodeV2API, NodeBlockNotFoundException
from .exceptions import UpdateBlockchainProgressError

import decimal
import math
import logging


Decimal = decimal.Decimal

logger = logging.getLogger(__name__)


def _get_percent_loaded(nr_missing_blocks, nr_all_blocks, decimal_places):
    missing_percent = Decimal('0')
    if nr_all_blocks:
        # we can calculate, otherwise we would get division by zero
        missing_percent = Decimal(str(nr_missing_blocks)) / Decimal(str(nr_all_blocks)) * Decimal('100')
    return (Decimal('100') - missing_percent).quantize(
        Decimal('1') / Decimal('10')**decimal_places,
        rounding=decimal.ROUND_DOWN
    )


def update_load_progress(
    blockchain, missing, total, step, modulo, decimal_places, verbose=False, source='default',
):
    if step % modulo == 0:
        logger.info('bc: {}, missing: {}, total: {}, step: {}, modulo: {}, decimal_places: {}, source: {}'.format(
            blockchain.slug, missing, total, step, modulo, decimal_places, source))
        # update Blockchain's load_progress
        blockchain.load_progress = _get_percent_loaded(
            missing,
            total,
            decimal_places
        )
        blockchain.save()
        if verbose:
            # option to get output in the shell if you bootstrap from there
            print('Blockchain: {} - load_progress: {}%'.format(
                blockchain.slug, blockchain.load_progress)
            )


def fetch_and_store_block(blockchain, block_height, prefetch=True):
    # initialize node api
    node_api = NodeV2API(blockchain.node)
    if block_height < 0:
        # no such block height
        raise NodeBlockNotFoundException()
    if prefetch:
        block_data = get_prefetched_header_and_block_data(blockchain.node, block_height)
    else:
        block_data = node_api.get_block(height=block_height)
    header_data = block_data['header']
    timestamp = parse_datetime(header_data['timestamp'])
    hash = header_data['hash']
    # create header instance
    cuckoo_solution = ','.join(map(str, header_data['cuckoo_solution']))
    with transaction.atomic():
        header, header_created = BlockHeader.objects.get_or_create(
            blockchain=blockchain,
            cuckoo_solution=cuckoo_solution,
            kernel_root=header_data['kernel_root'],
            defaults={
                'version': header_data['version'],
                'output_root': header_data['output_root'],
                'range_proof_root': header_data['range_proof_root'],
                'kernel_mmr_size': header_data['kernel_mmr_size'],
                'output_mmr_size': header_data['output_mmr_size'],
                'nonce': str(header_data['nonce']),
                'edge_bits': header_data['edge_bits'],
                'secondary_scaling': header_data['secondary_scaling'],
                'total_difficulty': header_data['total_difficulty'],
                'total_kernel_offset': header_data['total_kernel_offset'],
            }
        )
        # create block instance
        try:
            block, block_created = Block.objects.get_or_create(
                blockchain=blockchain,
                hash=hash,
                height=block_height,
                timestamp=timestamp,
                header=header,
                prev_hash=block_data['header']['previous'],
                reorg=None,
                nr_inputs=len(block_data['inputs']),
                nr_outputs=len(block_data['outputs']),
                nr_kernels=len(block_data['kernels']),
            )
        except IntegrityError as e:
            # race condition so it's a duplicate. We can skip creation process
            # and just return the block that we already have
            return Block.objects.get(blockchain=blockchain, hash=hash)

        if not block_created:
            # we have already fetched all the data since it's done in an atomic
            # transaction, so skip unnecessary work
            return block

        # bulk create kernels
        kernels = []
        for kernel_data in block_data['kernels']:
            kernels.append(
                Kernel(
                    block=block,
                    features=kernel_data['features'],
                    fee=kernel_data['fee'],
                    fee_shift=kernel_data['fee_shift'],
                    lock_height=kernel_data['lock_height'],
                    excess=kernel_data['excess'],
                    excess_sig=kernel_data['excess_sig'],
                )
            )
        Kernel.objects.bulk_create(kernels)

        inputs = []
        # create input instances
        outputs_data = Output.objects\
            .filter(
                commitment__in=block_data['inputs'],
                block__reorg__isnull=True,
                block__blockchain=block.blockchain,
            )\
            .values('id', 'commitment')
        outputs_mapper = { output_data['commitment'] : output_data['id'] for output_data in outputs_data }
        for input_data in block_data['inputs']:
            inputs.append(
                Input(
                    block=block,
                    commitment=input_data,
                    output_id=outputs_mapper.get(input_data),
                )
            )
        Input.objects.bulk_create(inputs)
        # mark the corresponding outputs as spent, but only on the main chain so
        # that we don't corrupt the reorged data
        Output.objects.filter(pk__in=outputs_mapper.values()).update(spent=True)

        # create output instances
        outputs = []
        inputs = Input.objects\
            .filter(
                commitment__in=list(map(lambda x: x['commit'], block_data['outputs'])),
                block__reorg__isnull=True,
                block__blockchain=block.blockchain,
            )
        inputs_mapper = { input.commitment : input for input in inputs }
        for output_data in block_data['outputs']:
            outputs.append(
                Output(
                    block=block,
                    output_type=output_data['output_type'],
                    commitment=output_data['commit'],
                    spent=output_data['spent'],
                    proof=output_data['proof'],
                    proof_hash=output_data['proof_hash'],
                    merkle_proof=output_data['merkle_proof'],
                    mmr_index=output_data['mmr_index'],
                )
            )
        outputs = Output.objects.bulk_create(outputs)
        # link inputs to created outputs, but only on the main chain so that we
        # don't corrupt the reorged data
        fixed_inputs = []
        for output in outputs:
            matching_input = inputs_mapper.get(output.commitment)
            if matching_input:
                matching_input.output = output
                fixed_inputs.append(matching_input)
        Input.objects.bulk_update(fixed_inputs, ['output'])
    return block


def load_blocks(
    blockchain, start_height, end_height, skip_reorg_check, verbose=False
):
    logger.info(
        'Loading blocks',
        extra={
            'blockchain': blockchain.slug,
            'start_height': start_height,
            'end_height': end_height,
            'skip_reorg_check': skip_reorg_check,
        },
    )
    existing_heights = set(list(
        blockchain.blocks\
            .filter(reorg__isnull=True)\
            .values_list('height', flat=True)
    ))
    missing_heights = set(range(start_height, end_height + 1)) - existing_heights
    decimal_places = 2
    node_step = 2 if blockchain.node.archive else 0
    update_loaded_step = math.floor(
        (end_height - start_height + 1) / (10**(2+node_step))
    )
    if update_loaded_step == 0:
        # less than 100 blocks in total, just set it to a big number so it only
        # updates at the end of this function
        update_loaded_step = 1000
    # we start from the last block
    checked_heights = set()
    # we store numbers so that we don't need to calculate big set diffs for
    # each block
    nr_checked_missing_heights = 0
    nr_missing_heights = len(missing_heights)
    skip_reorg_check = False
    for block_height in sorted(missing_heights, reverse=True):
        if block_height in checked_heights:
            continue
        if not skip_reorg_check and nr_checked_missing_heights > 1000:
            # we don't want to keep checking for reorgs forever since it's slow
            skip_reorg_check = True
        update_load_progress(
            blockchain, 
            # len(missing_heights - checked_heights),
            nr_missing_heights - nr_checked_missing_heights,
            end_height - start_height + 1,
            nr_checked_missing_heights,
            # len(checked_heights),
            update_loaded_step,
            decimal_places,
            verbose=True
        )
        try:
            new_block = fetch_and_store_block(blockchain, block_height)
            if block_height not in checked_heights and block_height in missing_heights:
                nr_checked_missing_heights += 1
            checked_heights.add(block_height)
        except NodeBlockNotFoundException:
            # seems like the node dropped that height so that's where we stop
            end_height = block_height - 1
            break
        # NOTE: we are fetching block at height X which means there is currently
        # no Block instance with that height in the DB. All height above X must
        # be in DB, since missing_heights are handled in reverse order
        if not skip_reorg_check:
            _, fetched_heights = check_for_reorg(
                new_block,
                lambda inner_heights: update_load_progress(
                    blockchain, 
                    len(missing_heights - checked_heights - inner_heights),
                    end_height - start_height + 1,
                    len(checked_heights | inner_heights),
                    update_loaded_step,
                    decimal_places,
                    verbose=True,
                    source='check_for_reorg',
                ),
                missing_heights,
                start_height
            )
            checked_heights |= fetched_heights
            nr_checked_missing_heights = len(checked_heights & missing_heights)
    # set loaded % to 100
    update_load_progress(
        blockchain, 
        0,
        end_height - start_height + 1,
        0,
        update_loaded_step,
        decimal_places,
        verbose=True
    )
    logger.info(
        'Loading blocks finished',
        extra={
            'blockchain': blockchain.slug,
            'start_height': start_height,
            'end_height': end_height,
            'skip_reorg_check': skip_reorg_check,
        },
    )


def update_blockchain_progress(blockchain):
    try:
        start_height, end_height = blockchain.get_bootstrap_heights()
    except Exception as e:
        logger.warning(
            'Failed to get bootstrap heights',
            extra={ 'blockchain': blockchain.slug },
        )
        raise UpdateBlockchainProgressError(blockchain.slug)
    expected_heights = set(range(start_height, end_height + 1))
    existing_heights = set(list(
        blockchain.blocks\
            .filter(reorg__isnull=True)\
            .values_list('height', flat=True)
    ))
    missing_heights = expected_heights - existing_heights
    update_load_progress(
        blockchain, 
        len(missing_heights),
        end_height - start_height + 1,
        1,
        1,
        2,
        verbose=True
    )

