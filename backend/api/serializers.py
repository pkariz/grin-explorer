from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from .models import (
    Blockchain,
    Block,
    BlockHeader,
    Kernel,
    Input,
    Output,
    Reorg,
    Node,
    NodeGroup,
    DramatiqTask,
)
from .node import NodeV2API


class DramatiqTaskSimpleSerializer(serializers.ModelSerializer):

    class Meta:
        model = DramatiqTask
        fields = '__all__'


class DramatiqTaskSerializer(serializers.ModelSerializer):
    content_object = serializers.SerializerMethodField()

    class Meta:
        model = DramatiqTask
        fields = (
            'id',
            'message_id',
            'type',
            'status',
            'failure_reason',
            'content_object',
        )

    def get_content_object(self, task):
        from .serializers import BlockchainSerializer
        serializer_mapper = {
            'Blockchain': BlockchainSerializer,
        }
        klass = task.content_object.__class__
        return {
            'model': klass._meta.model_name,
            'data': serializer_mapper[klass.__name__](task.content_object).data,
        }


class NodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Node
        fields = '__all__'


class NodeGroupSerializer(serializers.ModelSerializer):
    nodes = NodeSerializer(many=True, read_only=True)

    class Meta:
        model = NodeGroup
        fields = '__all__'


class BlockchainSerializer(serializers.ModelSerializer):
    node = serializers.PrimaryKeyRelatedField(queryset=Node.objects.all(), write_only=True)

    class Meta:
        model = Blockchain
        fields = ('name', 'slug', 'default', 'node', 'load_progress', 'fetch_price')


class BlockchainExtendedSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Blockchain
        fields = ('name', 'slug', 'node', 'default', 'load_progress', 'fetch_price', 'tasks')

    def to_representation(self, obj):
        self.fields['node'] = NodeSerializer()
        return super().to_representation(obj)

    def get_tasks(self, blockchain):
        content_type = ContentType.objects.get_for_model(blockchain)
        tasks = DramatiqTask.objects.filter(
            content_type=content_type,
            object_id=blockchain.id,
        )
        return DramatiqTaskSimpleSerializer(tasks, many=True).data


class BlockHeaderSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlockHeader
        fields = '__all__'


class BlockSerializer(serializers.ModelSerializer):
    blockchain = BlockchainSerializer()
    header = BlockHeaderSerializer()
    starting_reorg_blocks = serializers.SerializerMethodField()

    class Meta:
        model = Block
        fields = (
            'hash',
            'height',
            'timestamp',
            'header',
            'prev_hash',
            'reorg',
            'nr_kernels',
            'nr_inputs',
            'nr_outputs',
            'blockchain',
            'starting_reorg_blocks',
        )

    def get_starting_reorg_blocks(self, block):
        reorgs = Reorg.objects.filter(start_main_block=block)
        reorgs = list(filter(
            lambda reorg: reorg.end_reorg_block.height - \
                    reorg.start_reorg_block.height + 1 >= settings.MIN_REORG_LEN,
            reorgs
        ))
        return BlockSerializer(
            [reorg.start_reorg_block for reorg in reorgs], many=True).data


class KernelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kernel
        fields = '__all__'


class InputSerializer(serializers.ModelSerializer):
    created_in = serializers.SerializerMethodField()

    class Meta:
        model = Input
        fields = '__all__'

    def get_created_in(self, input):
        output = input.output
        if not output:
            return None
        return (output.block.height, output.block.hash)


class OutputSerializer(serializers.ModelSerializer):
    spent_in = serializers.SerializerMethodField()

    class Meta:
        model = Output
        fields = '__all__'

    def get_spent_in(self, output):
        try:
            # we use .all and then manually filter so that prefetched data gets used
            input = list(filter(
                lambda input: input.block.reorg is None,
                output.inputs.all())
            )[0]
        except IndexError:
            return None
        return (input.block.height, input.block.hash)


class BlockDetailSerializer(serializers.ModelSerializer):
    header = BlockHeaderSerializer()
    kernels = KernelSerializer(many=True)
    inputs = InputSerializer(many=True)
    outputs = OutputSerializer(many=True)
    blockchain = BlockchainSerializer()
    confirmations = serializers.SerializerMethodField()
    next_hash = serializers.SerializerMethodField()
    next_block_reorgs = serializers.SerializerMethodField()

    class Meta:
        model = Block
        fields = (
            'hash',
            'height',
            'timestamp',
            'header',
            'prev_hash',
            'kernels',
            'inputs',
            'outputs',
            'blockchain',
            'confirmations',
            'next_hash',
            'reorg',
            'next_block_reorgs',
        )

    def get_confirmations(self, block):
        # in reorged blocks we show confirmations based on the reorged chain!
        tip_height = block.blockchain.blocks\
            .filter(reorg=block.reorg)\
            .order_by('-height')\
            .first().height
        return tip_height - block.height + 1

    def get_next_hash(self, block):
        try:
            return Block.objects.get(
                blockchain=block.blockchain,
                reorg=block.reorg,
                prev_hash=block.hash
            ).hash
        except Block.DoesNotExist:
            return None

    def get_next_block_reorgs(self, block):
        from .serializers import ReorgSerializer
        reorgs = Reorg.objects.filter(start_main_block__prev_hash=block.hash)
        reorgs = list(filter(
            lambda reorg: reorg.end_reorg_block.height - \
                    reorg.start_reorg_block.height + 1 >= settings.MIN_REORG_LEN,
            reorgs
        ))
        return ReorgSerializer(reorgs, many=True).data


class ReorgSerializer(serializers.ModelSerializer):
    blockchain = BlockchainSerializer()
    start_reorg_block = BlockSerializer()

    class Meta:
        model = Reorg
        fields = (
            'id',
            'blockchain',
            'start_reorg_block',
        )

