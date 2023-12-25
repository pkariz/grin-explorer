from django.db.models.signals import post_save
from django.dispatch import receiver
from backend.api.models import Block, Reorg
from backend.api.helpers import fix_outputs_and_inputs_from_reorg

import logging


logger = logging.getLogger(__name__)


@receiver(
    post_save,
    sender=Block,
    dispatch_uid="on_block_create",
)
def on_block_create(sender, instance, created, **kwargs):
    if created:
        logger.info(
            'Created block',
            extra={
                'blockchain': instance.blockchain.slug,
                'height': instance.height,
                'hash': instance.hash,
            },
        )


@receiver(
    post_save,
    sender=Reorg,
    dispatch_uid="on_reorg_create_fix_state",
)
def on_reorg_create_fix_state(sender, instance, created, **kwargs):
    if created:
        logger.info(
            'Created reorg',
            extra={
                'pk': instance.pk,
                'blockchain': instance.blockchain.slug,
                'length': instance.end_reorg_block.height - instance.start_reorg_block.height + 1,
                'start_reorg_block.height': instance.start_reorg_block.height,
                'start_reorg_block.hash': instance.start_reorg_block.hash,
                'end_reorg_block.height': instance.end_reorg_block.height,
                'end_reorg_block.hash': instance.end_reorg_block.hash,
                'start_main_block.height': instance.start_main_block.height,
                'start_main_block.hash': instance.start_main_block.hash,
            },
        )
        # add relation to Reorg instance for reorged blocks
        cur_block = instance.start_reorg_block
        while cur_block and cur_block.height <= instance.end_reorg_block.height:
            cur_block.reorg = instance
            cur_block.save()
            cur_block = cur_block.get_next_block()
        # make sure new main chain has no Reorg instances related to it
        cur_block = instance.start_main_block
        while cur_block:
            if cur_block.reorg is not None:
                reorg = cur_block.reorg
                # this block is not reorged anymore!
                cur_block.reorg = None
                cur_block.save()
                if not Block.objects.filter(reorg=reorg).exists():
                    # reorg is empty, we don't need it anymore
                    reorg.delete()
            cur_block = cur_block.get_next_block()
        # fix 'spent' for outputs and 'output' for inputs
        fix_outputs_and_inputs_from_reorg(instance)

