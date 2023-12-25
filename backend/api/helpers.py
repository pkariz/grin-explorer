from decimal import Decimal
from django.conf import settings
from backend.api.models import Input, Output, Block, Reorg
from .mixins import DefaultMixin
from .node import NodeV2API, NodeBlockNotFoundException

import json
import logging
import redis
import requests


logger = logging.getLogger(__name__)

node_cache = {}


def get_blocks_between(start_block, end_block):
    """Returns sorted blocks from start_block to end_block, including both."""
    blocks = []
    cur_block = start_block
    while cur_block != end_block:
        blocks.append(cur_block)
        cur_block = cur_block.get_next_block()
    if start_block != end_block:
        blocks.append(cur_block)
    return blocks


def fix_outputs_and_inputs_from_reorg(reorg):
    """
    Fix Output.spent and Input.output on instances that were affected by the
    given reorg. Note that due to the order of block fetching (sometimes
    descending by height) we might have corrupted Output/Input instances also on
    the reorged block. For example if block 102.1 in a reorg creates output with
    commitment 'd' and the same commitment is created in block 102 but we first
    fetch block 103 which spends it, then it will update output 'd' from 102.1
    because it doesn't yet know that it's a part of a reorg (due to the way we
    implemented things). We also need to fix outputs which were spent in a reorg
    but not in the main chain and vice-versa.
    """
    # solve reorged part
    reorged_blocks = get_blocks_between(
        reorg.start_reorg_block, reorg.end_reorg_block)
    reorg_inputs = Input.objects.filter(block__in=reorged_blocks)
    reorg_outputs = Output.objects.filter(block__in=reorged_blocks)
    for output in reorg_outputs:
        matching_input = reorg_inputs\
            .filter(commitment=output.commitment)\
            .first()
        output.spent = False
        if matching_input:
            output.spent = True
            matching_input.output = output
            matching_input.save()
        output.save()

    # NOTE: some redundancy in this loop, but reorgs are rare so it's ok
    for input in reorg_inputs:
        matching_output = reorg_outputs\
            .filter(commitment=input.commitment)\
            .first()
        if not matching_output:
            # part of the main chain before the reorg happened, fix it there
            matching_output = Output.objects.filter(
                block__reorg=None, commitment=input.commitment).first()
            if matching_output:
                matching_output.spent = False
                matching_output.save()
                input.output = matching_output
                input.save()
    # solve main part
    main_blocks = Block.objects\
        .filter(height__gte=reorg.start_main_block.height, reorg=None)\
        .order_by('height')
    for block in main_blocks:
        for input in block.inputs.all():
            matching_output = Output.objects.filter(
                block__reorg=None, commitment=input.commitment).first()
            if matching_output:
                matching_output.spent = True
                matching_output.save()
                input.output = matching_output
                input.save()


def check_for_reorg(new_block, update_progress_fn, missing_heights, start_height):
    """
    Checks if new_block is part of a reorg. Return tuple (reorg, set<heights>)
    where reorg is Reorg instance or None, set<heights> is a set of heights of
    blocks that were fetched in during this reorg checking process.
    """
    # import here to avoid cyclic import
    from .bootstrap import fetch_and_store_block
    blockchain = new_block.blockchain
    fetched_heights = set()
    reorged_blocks = []
    reorg = None
    # find reorged blocks backward
    cur_block = new_block
    while True:
        prev_block = blockchain.blocks\
            .filter(height=cur_block.height - 1, reorg__isnull=True)\
            .first()
        if prev_block:
            if cur_block.prev_hash == prev_block.hash:
                break
            reorged_blocks.append(prev_block)
            # fetch the new block at this height
            cur_block = fetch_and_store_block(
                blockchain, prev_block.height)
            # mark height as reorged so that we don't go through it again
            # when looping through 'missing_heights'
            if prev_block.height in missing_heights:
                fetched_heights.add(prev_block.height)
                update_progress_fn(fetched_heights)
        else:
            try:
                # we still need to check for a case where current block
                # is at height X, we are missing height X-1 in our DB
                # but have height X-2 where X-2 in our DB has been
                # reorged
                if cur_block.height - 1 < start_height:
                    break
                cur_block = fetch_and_store_block(
                    blockchain, cur_block.height - 1)
                if cur_block:
                    # mark height as reorged so that we don't go through it
                    # again when looping through 'missing_heights'
                    if cur_block.height in missing_heights:
                        fetched_heights.add(cur_block.height)
                        update_progress_fn(fetched_heights)
                        # we assume the reorg is not bigger than 1000 blocks,
                        # so we break if needed (this check_for_reorg is much
                        # slower at fetching because it does a db lookup in each
                        # loop, that's why we want to leave it if possible)
                        if len(fetched_heights) > 1000 and not reorged_blocks:
                            break
            except NodeBlockNotFoundException:
                # the node probably dropped that height so that's where we stop
                logger.info(
                    'check reorg backward block not found',
                    extra={'height': cur_block.height - 1},
                )
                break
    # reverse reorged_blocks so that we have them ascending by height
    reorged_blocks.reverse()
    # store the first block in the new "main" chain
    start_main_block = cur_block
    # find reorged blocks forward
    cur_block = new_block
    # we know that we have fetched all the later blocks because we fetch
    # missing blocks in order (descending by height)
    next_block = blockchain.blocks\
        .filter(height=cur_block.height + 1, reorg__isnull=True)\
        .first()
    while next_block:
        if next_block.prev_hash == cur_block.hash:
            break
        # next_block has been reorged
        reorged_blocks.append(next_block)
        # fetch the new block at this height
        cur_block = fetch_and_store_block(blockchain, next_block.height)
        # mark height as reorged so that we don't go through it again when
        # looping through 'missing_heights'
        if cur_block.height in missing_heights:
            fetched_heights.add(cur_block.height)
            update_progress_fn(fetched_heights)
        next_block = blockchain.blocks\
            .filter(height=cur_block.height + 1, reorg__isnull=True)\
            .first()
    if reorged_blocks:
        reorg = Reorg.objects.create(
            blockchain=blockchain,
            start_reorg_block=reorged_blocks[0],
            end_reorg_block=reorged_blocks[-1],
            start_main_block=start_main_block,
        )
    return reorg, fetched_heights


def get_filter_backends(replacements):
    """
    Returns a tuple of filter backends where default ones, from DefaultMixin,
    are replaced with the given replacements.

    Args:
        replacements: dict where key is an existing filter backend class's
        __name__ and value is its replacement filter backend class
    """
    current_filters = DefaultMixin.filter_backends
    return tuple([
        filter if filter.__name__ not in replacements else replacements[filter.__name__]
        for filter in list(current_filters)
    ])


def store_data_in_redis(redis_key, data):
    r = redis.Redis(host='redis')
    json_data = json.dumps(data)
    r.set(redis_key, json_data)


def load_data_from_redis(redis_key):
    r = redis.Redis(host='redis')
    data = r.get(redis_key)
    if data is None:
        return
    return json.loads(data)


def default_fetch_price_fn(blockchain):
    """
    This function fetches grin-btc data from tradeogre.
    """
    # fetch data from tradeogre
    resp = requests.get('https://tradeogre.com/api/v1/ticker/grin-btc')
    data = resp.json()
    if not data['success']:
        raise Exception('Response from tradeogre had success false')
    percent_change = (Decimal(data['price']) / Decimal(data['initialprice']) - Decimal('1')) * Decimal('100')
    # returned data must have exactly those keys with exactly these types
    data = {
        'btc_value': data['price'],  # string
        'percent_change': '{0:.2f}'.format(percent_change),  # string
    }
    return data


def get_func_from_dotted_path(dotted_path):
    """Returns a function related to the given dotted path."""
    try:
        split_path = dotted_path.split('.')
        mod_path, func_name = '.'.join(split_path[:-1]), split_path[-1]
        mod = __import__(mod_path, fromlist=[func_name])
        return getattr(mod, func_name)
    except Exception as e:
        raise Exception('Failed to import function {}:{}'.format(dotted_path, e))


def get_missing_heights_repr(missing_heights):
    if not missing_heights:
        return None
    xs = sorted(list(missing_heights))
    # idea: find indexes of gaps, then you get [x1...x2],[x3...x4] and if x1 == x2 then
    # only one element is missing (x1), otherwise all elements between 'x1...x2' are missing
    res = []
    cur = []
    for i, x in enumerate(xs):
        if not cur:
            cur.append(x)
            if i == len(xs) - 1 or i == 0 and (len(xs) == 1 or xs[1] != x+1):
                cur.append(x)
                res.append(cur)
                cur = []
            continue
        if x != xs[i-1] + 1:
            cur.append(cur[0])
            res.append(cur)
            cur = [x]
            if i == len(xs) - 1:
                cur.append(cur[0])
                res.append(cur)
        elif i == len(xs) - 1 or xs[i+1] != x + 1:
            cur.append(x)
            res.append(cur)
            cur = []
    return list(map(
        lambda x: str(x[0]) if x[0] == x[1] else f'{x[0]}...{x[1]}',
        res
    ))


def get_prefetched_header_and_block_data(node, height):
    if node.slug not in node_cache or height not in node_cache[node.slug]:
        node_api = NodeV2API(node)
        fetched_blocks = node_api.get_blocks(max(0, height - 999), height)['blocks']
        # we also clear existing cache for this node because
        # it's likely not going to be used anymore
        node_cache[node.slug] = {
            block['header']['height']: block
            for block in fetched_blocks
        }
    if height not in node_cache[node.slug]:
        raise NodeBlockNotFoundException()
    return node_cache[node.slug][height]

