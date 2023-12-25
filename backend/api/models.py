from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.core.validators import (
    MinLengthValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models, transaction
from django.db.models import Q
from model_utils.models import TimeStampedModel
from slugify import slugify
from requests.exceptions import (
    Timeout as RequestsTimeout,
    ConnectionError as RequestsConnectionError,
    HTTPError as RequestsHTTPError,
    ReadTimeout as RequestsReadTimeout
)
from .node import NodeV2API, NodeError


import logging


logger = logging.getLogger(__name__)


class NodeGroup(models.Model):
    """
    NodeGroup represents a group of nodes. These nodes should be on the same
    network.:
    """
    id = models.BigAutoField(primary_key=True)
    # name is probably mainnet, testnet or smth similar
    name = models.CharField(max_length=255, unique=True)
    # by default that's slug of the name
    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, to_lower=True)
        else:
            self.slug = self.slug.lower()
        self.full_clean()
        return super().save(*args, **kwargs)


class Node(TimeStampedModel):
    """Node on the network. Currently it only supports grin-rust."""
    id = models.BigAutoField(primary_key=True)
    # name can be whatever
    name = models.CharField(max_length=255, unique=True)
    # by default that's slug of the name
    slug = models.SlugField(max_length=255, unique=True)
    group = models.ForeignKey(
        NodeGroup, related_name='nodes', on_delete=models.PROTECT)
    # foreign api url of the grin-rust node
    api_url = models.URLField()
    # username of the grin-rust node
    api_username = models.CharField(max_length=255)
    # foreign api secret of the grin-rust node
    api_password = models.CharField(max_length=255)
    # if archive is true then we fetch every block when we bootstrap, otherwise
    # we fetch only latest 1440 blocks (1 day)
    archive = models.BooleanField(default=False)

    def __str__(self):
        repr = f'{self.name}'
        if self.archive:
            repr += ' (archive)'
        return repr

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, to_lower=True)
        else:
            self.slug = self.slug.lower()
        return super().save(*args, **kwargs)

    def is_reachable(self):
        try:
            NodeV2API(self).get_tip()
            return True
        except (
            RequestsConnectionError,
            RequestsTimeout,
            RequestsHTTPError,
            RequestsReadTimeout
        ):
            logger.exception('Node unreachable', extra={'node': self.slug})
            return False


class Blockchain(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    # testnet, mainnet etc
    name = models.CharField(max_length=255, unique=True)
    # slug of the name, we use it in url
    slug = models.SlugField(max_length=255, unique=True)
    # node from which the data is fetched
    node = models.ForeignKey(
        Node, related_name='blockchains', on_delete=models.PROTECT)
    # the default blockchain will be picked on the gui by default
    default = models.BooleanField(default=False)
    # if fetch_price is False then the shown price will always be 0.
    # Testnets and localnets should have this set to false.
    fetch_price = models.BooleanField(default=True)
    # load_progress shows current % of loaded blocks. If archive is True then
    # load_progress will represent % of missing all blocks, otherwise % of
    # missing blocks from the latest 1440 blocks
    load_progress = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    def __str__(self):
        return f'{self.name} - {self.load_progress} [Node<{self.node}>]'

    def bootstrap(self, skip_reorg_check=False):
        # import here to avoid cyclic import
        from .bootstrap import load_blocks

        start_height, end_height = self.get_bootstrap_heights()
        load_blocks(self, start_height, end_height, skip_reorg_check)

    def get_tip_height(self):
        node_api = NodeV2API(self.node)
        try:
            end_block = node_api.get_tip()['height']
        except NodeError as e:
            logger.exception('Bootstrap failed - failed to get node tip')
            raise e
        return end_block

    def get_progress_decimal_places(self):
        if self.node.archive:
            return 2
        return 0

    def get_bootstrap_heights(self):
        node_api = NodeV2API(self.node)
        end_height = self.get_tip_height()
        try:
            start_height = node_api.get_blocks(0, end_height, 1, False)['blocks'][0]['header']['height']
        except IndexError:
            raise Exception('Node has no blocks.')
        except NodeError as e:
            logger.exception('Bootstrap failed - failed to get first block height')
            raise e
        return start_height, end_height

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, to_lower=True)
        else:
            self.slug = self.slug.lower()
        if self.default:
            # set other blockchain.default to False
            other_blockchains = Blockchain.objects.all()
            if self.pk:
                other_blockchains = other_blockchains.exclude(pk=self.pk)
            other_blockchains.update(default=False)
        # blockchain doesn't change much so this call doesn't hurt
        old_instance = Blockchain.objects.get(pk=self.pk) if self.pk else None
        res = super().save(*args, **kwargs)
        if old_instance and self.load_progress != old_instance.load_progress:
            # load progress changed, send info
            async_to_sync(get_channel_layer().group_send)(
                'admin_group',
                {
                    'type': 'blockchain_progress_changed',
                    'message': {
                        'slug': self.slug,
                        # convert to float since Decimal is not serializable
                        'load_progress': float(self.load_progress),
                    },
                }
            )
        return res

    def full_print(self):
        """Used for developing and debugging."""
        print('MAIN CHAIN:')
        for block in self.blocks.filter(reorg=None).order_by('height'):
            print('  --> ' + block.hash)
        for reorg in Reorg.objects.filter(blockchain=self):
            print('REORG:')
            for block in Block.objects.filter(reorg=reorg).order_by('height'):
                print('  --> ' + block.hash)
        print('------------------------------------------------------')

    def reset(self):
        """Used for developing and debugging."""
        from .models import Block, BlockHeader, Input, Output, Kernel, DramatiqTask, Reorg
        from django.contrib.contenttypes.models import ContentType
        from decimal import Decimal

        Input.objects.filter(block__blockchain=self).delete()
        Output.objects.filter(block__blockchain=self).delete()
        Kernel.objects.filter(block__blockchain=self).delete()
        self.reorgs.all().delete()

        content_type = ContentType.objects.get_for_model(self)
        DramatiqTask.objects.filter(
            content_type=content_type,
            object_id=self.id,
        ).delete()
        # removing header will also remove the block
        BlockHeader.objects.filter(block__blockchain=self).delete()
        self.load_progress = Decimal('0')
        self.save()


class BlockHeader(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    # same as with 'Block', we want to keep 'same' headers separate if they're
    # a part of a different chain.
    blockchain = models.ForeignKey(
        Blockchain, related_name='headers', on_delete=models.CASCADE)
    version = models.IntegerField()
    kernel_root = models.CharField(max_length=64)
    output_root = models.CharField(max_length=64)
    range_proof_root = models.CharField(max_length=64)
    kernel_mmr_size = models.IntegerField()
    output_mmr_size = models.IntegerField()
    nonce = models.TextField()
    edge_bits = models.IntegerField()
    # cuckoo_solution could be an ArrayField(models.BigIntegerField) but that
    # would make syncing a few times slower
    cuckoo_solution = models.TextField(db_index=True) # ArrayField(models.BigIntegerField())
    secondary_scaling = models.IntegerField()
    # sum of the target difficulties, not the sum of the actual block difficulties
    total_difficulty = models.BigIntegerField()
    total_kernel_offset = models.CharField(max_length=64)


class Block(TimeStampedModel):
    blockchain = models.ForeignKey(
        Blockchain, related_name='blocks', on_delete=models.CASCADE)
    hash = models.CharField(
        primary_key=True,
        max_length=64,
        validators=[MinLengthValidator(64)],
        db_index=True,
    )
    height = models.PositiveIntegerField(db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    header = models.ForeignKey(
        'BlockHeader', related_name='block', on_delete=models.CASCADE)
    prev_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        validators=[MinLengthValidator(64)],
    )
    nr_inputs = models.PositiveIntegerField(default=0)
    nr_outputs = models.PositiveIntegerField(default=0)
    nr_kernels = models.PositiveIntegerField(default=0)
    # when reorg is set it means this block is part of a reorg and not the main
    # chain
    reorg = models.ForeignKey(
        'Reorg', null=True, related_name='blocks', on_delete=models.CASCADE)

    def __str__(self):
        suffix = ''
        if self.reorg:
            suffix = ' Reorged: {}'.format(self.reorg.id)
        return '{}: {} (prev: {})'.format(
            self.height, self.hash, self.prev_hash)

    def get_next_block(self):
        return Block.objects.filter(prev_hash=self.hash).first()

    def get_previous_block(self):
        return Block.objects.filter(hash=self.prev_hash).first()

    def full_print(self, prefix=''):
        """Used for developing and debugging."""
        print('---------------------------------------------------------------')
        print(f'{prefix}Block {self.height}: {self.hash}, reorg: {self.reorg}')
        print(f'{prefix}  INPUTS:')
        for input in self.inputs.all():
            print(f'{prefix}    {input}, output: {input.output}')
        print(f'{prefix}  OUTPUTS:')
        for output in self.outputs.all():
            print(f'{prefix}    {output}')
        print(f'{prefix}  KERNELS:')
        for kernel in self.kernels.all():
            print(f'{prefix}    {kernel}')
        print('---------------------------------------------------------------')


class Output(TimeStampedModel):
    """
    The same output can be included in two different blocks if it's a part of a
    reorg. In this case there will be two identical Output instances, except for
    the referenced block.
    """
    id = models.BigAutoField(primary_key=True)

    OUTPUT_TYPE = (
        ("Transaction", "Transaction"),
        ("Coinbase", "Coinbase"),
    )

    block = models.ForeignKey(
        Block,
        related_name='outputs',
        on_delete=models.CASCADE,
    )

    output_type = models.TextField(
        choices=OUTPUT_TYPE
    )

    # pedersen commitment as hex
    commitment = models.CharField(
        max_length=66,
        db_index=True,
    )

    # on reorged blocks 'spent' is set based on the reorged chain, not main
    spent = models.BooleanField()

    # range proof as hex
    proof = models.TextField()

    # range proof hash as hex
    proof_hash = models.CharField(max_length=64)

    # coinbase transactions have merkle_proof None
    merkle_proof = models.TextField(null=True)

    mmr_index = models.IntegerField()

    def __str__(self):
        return (
            f'{self.commitment}({self.id}), spent: {self.spent}, '
            f'inputs: {self.inputs.all()}'
        )


class Input(TimeStampedModel):
    """
    The same input commitment can be included in two different blocks if it's a
    part of a reorg. In this case there will be two identical Input instances,
    except for the referenced block and possibly also with a different output.
    """
    id = models.BigAutoField(primary_key=True)
    block = models.ForeignKey(
        Block,
        related_name='inputs',
        on_delete=models.CASCADE,
    )
    # pedersen commitment as hex
    commitment = models.CharField(max_length=66, db_index=True)

    # output which corresponds to this input being spent
    output = models.ForeignKey(
        Output,
        blank=True,
        null=True,
        related_name='inputs',
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{self.commitment}({self.id})'


class Kernel(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)

    block = models.ForeignKey(
        Block,
        related_name='kernels',
        on_delete=models.CASCADE,
    )

    # plain, coinbase, heightlocked, norecentduplicate
    features = models.TextField()

    fee = models.BigIntegerField()

    fee_shift = models.IntegerField()

    lock_height = models.IntegerField()

    excess = models.CharField(max_length=66, db_index=True)

    excess_sig = models.CharField(max_length=142)

    def __str__(self):
        return f'{self.excess}'


class Reorg(TimeStampedModel):
    id = models.BigAutoField(primary_key=True)
    blockchain = models.ForeignKey(
        Blockchain, related_name='reorgs', on_delete=models.CASCADE)
    # start_reorg_block and end_reorg_block define starting and ending block,
    # which were reorged
    start_reorg_block = models.ForeignKey(
        Block, related_name='start_reorgs', on_delete=models.CASCADE)
    end_reorg_block = models.ForeignKey(
        Block, related_name='end_reorgs', on_delete=models.CASCADE)
    # start_main_block defines starting block which is the new start of the main
    # chain - the block that replaced start_reorg_block. We usually don't know
    # which the ending block is when we spot the reorg, so we don't store it
    # (we don't even have it in DB at that time yet since we usually get them
    # incrementally in the order they're accepted).
    start_main_block = models.ForeignKey(
        Block, related_name='start_mains', on_delete=models.CASCADE)

    def __str__(self):
        return '{}: start: {}, end: {}'.format(
            self.blockchain.slug, self.start_reorg_block, self.end_reorg_block)


class DramatiqTask(TimeStampedModel):
    """We store task's message_id so that we can abort the task."""

    class Type(models.TextChoices):
        BOOTSTRAP = 'bootstrap', 'Bootstrap'
        BLOCKCHAIN_DELETE = 'blockchain_delete', 'Blockchain delete'

    class Status(models.TextChoices):
        # NOTE: IN_PROGRESS doesn't really mean it's already in progress, just
        # that it has been sent
        IN_PROGRESS = 'in_progress', 'In progress'
        SKIPPED = 'skipped', 'Skipped'
        SUCCESS = 'success', 'Success'
        FAILURE = 'failure', 'Failure'

    id = models.BigAutoField(primary_key=True)
    message_id = models.CharField(max_length=255, unique=True)
    # type tells us what this task is doing, eg. 'bootstrap'
    type = models.CharField(max_length=255, choices=Type.choices)
    status = models.CharField(max_length=255, choices=Status.choices)
    # failure_reason should be short and concise
    failure_reason = models.TextField(null=True, default=None)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def save(self, *args, **kwargs):
        from .serializers import DramatiqTaskSerializer
        old_instance = DramatiqTask.objects.get(pk=self.pk) if self.pk else None
        res = super().save(*args, **kwargs)
        if old_instance and self.status != old_instance.status:
            # status changed, send info
            print('sending task status update')
            async_to_sync(get_channel_layer().group_send)(
                'admin_group',
                {
                    'type': 'task_status_changed',
                    'message': DramatiqTaskSerializer(self).data,
                }
            )
        return res

