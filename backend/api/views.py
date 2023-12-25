from asgiref.sync import async_to_sync
from django.contrib.contenttypes.models import ContentType
from django.db.models.deletion import ProtectedError
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from dramatiq_abort import abort
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from slugify import slugify

from .bootstrap import fetch_and_store_block, update_blockchain_progress
from .exceptions import UpdateBlockchainProgressError
from .helpers import get_filter_backends, load_data_from_redis
from .filters import (
    BlockFilter,
    CustomBlockSearchFilter,
    NodeFilter,
    NodeGroupFilter,
)
from .mixins import CustomModelViewSet
from .models import Blockchain, Block, Reorg, Node, NodeGroup, DramatiqTask
from .serializers import (
    BlockchainSerializer,
    BlockchainExtendedSerializer,
    BlockSerializer,
    BlockDetailSerializer,
    NodeSerializer,
    NodeGroupSerializer,
    DramatiqTaskSerializer,
)
from .tasks import bootstrap_blockchain, delete_blockchain

import channels
import logging
import pytz


logger = logging.getLogger(__name__)


# Serve Vue Application
index_view = never_cache(TemplateView.as_view(template_name='index.html'))


class NodeGroupViewSet(CustomModelViewSet):
    """API endpoint for NodeGroup."""
    queryset = NodeGroup.objects.all()
    filterset_class = NodeGroupFilter
    serializer_class = NodeGroupSerializer
    lookup_field = 'slug'
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        slug = request.data.get('slug')
        if not slug:
            request.data['slug'] = slugify(request.data['name'], to_lower=True)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as e:
            raise DRFValidationError(
                detail='Node group is related to nodes, delete them first')


class NodeViewSet(CustomModelViewSet):
    """API endpoint for Node."""
    queryset = Node.objects.all()
    filterset_class = NodeFilter
    serializer_class = NodeSerializer
    # currently all node views require authentication
    permission_classes = [IsAuthenticated]
    lookup_field = 'slug'

    def create(self, request, *args, **kwargs):
        slug = request.data.get('slug')
        if not slug:
            request.data['slug'] = slugify(request.data['name'], to_lower=True)
        request.data['group'] = NodeGroup.objects.get(slug=request.data['group']).pk
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # NOTE: super().partial_update calls update(..., partial=True)
        if not kwargs.get('partial'):
            # we don't allow full updates - aka PUT
            raise DRFPermissionDenied()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, slug=None):
        request.data['group'] = NodeGroup.objects.get(slug=request.data['group']).pk
        return super().partial_update(request, slug=slug)

    @action(detail=True, methods=['get'])
    def reachable(self, request, slug=None):
        node = self.get_object()
        try:
            res = node.is_reachable()
        except Exception as e:
            logger.exception('Unreachable node')
            res = False
        return Response(res, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError as e:
            raise DRFValidationError(
                detail='Node is related to blockchains, delete them first')


class BlockchainViewSet(CustomModelViewSet):
    """API endpoint for Blockchain."""
    queryset = Blockchain.objects.all()
    serializer_class = BlockchainSerializer
    lookup_field = 'slug'

    def get_serializer_class(self):
        # when authenticated we return also NodeSerializer data
        if self.request.user.is_authenticated:
            return BlockchainExtendedSerializer
        return BlockchainSerializer

    def create(self, request, *args, **kwargs):
        slug = request.data.get('slug')
        if not slug:
            request.data['slug'] = slugify(request.data['name'], to_lower=True)
        request.data['node'] = request.data['node']
        return super().create(request, *args, **kwargs)

    def destroy(self, request, slug=None):
        instance = self.get_object()
        message = delete_blockchain.send(instance.slug)
        task = DramatiqTask.objects.create(
            type=DramatiqTask.Type.BLOCKCHAIN_DELETE,
            status=DramatiqTask.Status.IN_PROGRESS,
            message_id=message.message_id,
            content_object=instance,
        )
        return Response(
            DramatiqTaskSerializer(task).data, status=status.HTTP_200_OK)

    def _abort_previous_tasks(self, blockchain):
        conflicting_message_ids = DramatiqTask.objects.filter(
            status=DramatiqTask.Status.IN_PROGRESS,
            object_id=blockchain.id,
            content_type=ContentType.objects.get_for_model(blockchain)
        ).values_list('message_id', flat=True)
        # abort previous conflicting tasks if they exist
        for conflicting_message_id in conflicting_message_ids:
            abort(conflicting_message_id)

    @action(detail=True, methods=['post'])
    def bootstrap(self, request, slug=None):
        blockchain = self.get_object()
        if not blockchain.node.is_reachable:
            raise APIException(detail='Node is unreachable')
        self._abort_previous_tasks(blockchain)
        # create a new task
        message = bootstrap_blockchain.send(blockchain.slug)
        task = DramatiqTask.objects.create(
            type=DramatiqTask.Type.BOOTSTRAP,
            status=DramatiqTask.Status.IN_PROGRESS,
            message_id=message.message_id,
            content_object=blockchain,
        )
        return Response(
            DramatiqTaskSerializer(task).data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post'],
        url_path='bootstrap/abort',
        url_name='bootstrap-abort',
    )
    def abort_bootstrap(self, request, slug=None):
        blockchain = self.get_object()
        self._abort_previous_tasks(blockchain)
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def graphs(self, request, slug=None):
        """Returns data for all graphs."""
        data = {
            'transaction_graph': load_data_from_redis(f'tx_graph__{slug}'),
        }
        return Response(data=data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def accepted(self, request, slug=None):
        # NOTE: if node is offline and then you start it again then it will
        # call this view for each block it will get. In this case there will be
        # many fast sequential calls to this view, there might be too many
        # postgres connections opened so view executions might actually fail.
        # The suggested solution is to comment out 'block_accepted_url' in
        # node's config file, run the node, wait for it to sync, uncomment 
        # 'block_accepted_url' and then manually bootstrap it.
        blockchain = self.get_object()
        # check if new block has been receiver when this blockchain is in the
        # process of being deleted.
        deleting = DramatiqTask.objects.filter(
            type=DramatiqTask.Type.BLOCKCHAIN_DELETE,
            object_id=blockchain.id,
            content_type=ContentType.objects.get_for_model(blockchain)
        ).exists()
        if deleting:
            # nothing to do, ignore the new block
            return Response(status=status.HTTP_404_NOT_FOUND)
        # get request data
        height = request.data['data']['header']['height']
        hash = request.data['hash']
        # prev_hash comes as list of int bytes, so we convert it to hex
        # NOTE: the same is true for some other data which we currently don't
        # need so we don't transform it, eg. data.header.kernel_root
        prev_hash = None
        if request.data['data']['header']['prev_hash']:
            prev_hash = bytes(request.data['data']['header']['prev_hash']).hex()
        logger.info(
            'Block accepted',
            extra={
                'height': height,
                'hash': hash,
                'prev_hash': prev_hash,
                'blockchain': blockchain.slug,
            },
        )

        web_socket_msg_type = 'send_block'
        # handle reorg case
        # we expect blocks to come ordered by height, there are some edge cases
        # here which are not handled, but they're unlikely to happen (eg. reorg
        # happens but websocket calls for first blocks fails while for later it
        # doesn't and then the code bellow wouldn't spot a reorg)
        block_at_this_height = blockchain.blocks\
            .filter(height=height, reorg__isnull=True)\
            .first()
        # we fetch here because anyone can call this view - we don't want to
        # work with fake data
        new_block = fetch_and_store_block(blockchain, height, prefetch=False)
        if block_at_this_height:
            if block_at_this_height.hash == new_block.hash:
                # probably have fetched this block while bootstraping, accepted
                # view got called a bit later so we already have it, noop
                return Response(status=status.HTTP_200_OK)
            logger.info(
                'Block accepted - reorg spotted',
                extra={
                    'block_at_this_height': block_at_this_height,
                    'block_at_this_height.hash': block_at_this_height.hash,
                    'block_at_this_height.reorg': block_at_this_height.reorg,
                    'hash': new_block.hash
                },
            )
            # reorg spotted
            reorged_blocks = list(blockchain.blocks\
                .filter(height__gte=height, reorg__isnull=True)
                .exclude(pk=new_block.pk)
                .order_by('height'))
            logger.info('reorged_blocks at start: {}'.format(reorged_blocks))
            # these reorged blocks are guaranteed to be reorged, now find any
            # previous blocks which were also reorged - aka get common
            # ancestor of the reorged block at 'height' and the new (main) block

            # find the common ancestor of this block and the reorged block at
            # the same height. We start with the current height to avoid more
            # logic for Reorg instance params
            if new_block.hash == block_at_this_height.hash:
                # at height X we got H1, then we got H2 (this call), but now it
                # reorged back to H1, so we don't do anything, no reorg is
                # stored since we didn't fetch the block in time from the node
                logger.info('Reorg cancelled out, noop')
                return Response(status=status.HTTP_200_OK)
            logger.info('new_block', extra={'hash': new_block.hash, 'prev_hash': new_block.prev_hash})
            prev_block_new_chain = new_block
            prev_block_old_chain = reorged_blocks[0]
            logger.info('prev_block_new_chain: {}, prev_block_old_chain: {}'.format(prev_block_new_chain, prev_block_old_chain))
            # remove the first one since it will get added again
            reorged_blocks = reorged_blocks[1:]
            logger.info('reorged_blocks after [1:]: {}'.format(reorged_blocks))
            main_blocks = []
            while True:
                # theoretically we might be missing the block in db but we don't
                # cover such cases currently
                if not prev_block_new_chain:
                    logger.info('reached break in IF NOT prev_block_new_chain')
                    # this means that prev_block_old_chain is also None, since
                    # they're both "previous" of their genesis block
                    break
                if prev_block_new_chain == prev_block_old_chain:
                    logger.info('reached break in IF NOT prev_block_new_chain == prev_block_old_chain')
                    # found the common ancestor
                    break
                # add to the left because we want to keep it sorted by height
                reorged_blocks.insert(0, prev_block_old_chain)
                main_blocks.insert(0, prev_block_new_chain)
                logger.info('new reorged_blocks: {}'.format(reorged_blocks))
                logger.info('new main_blocks: {}'.format(main_blocks))
                prev_block_new_chain = prev_block_new_chain.get_previous_block()
                prev_block_old_chain = prev_block_old_chain.get_previous_block()
                logger.info('new prev_block_new_chain: {}, prev_block_old_chain: {}'.format(prev_block_new_chain, prev_block_old_chain))

            logger.info('before reorg create: reorged_blocks: {}, main_blocks: {}'.format(reorged_blocks, main_blocks))
            reorg = Reorg.objects.create(
                blockchain=blockchain,
                start_reorg_block=reorged_blocks[0],
                end_reorg_block=reorged_blocks[-1],
                start_main_block=main_blocks[0],
            )
            # Reorg post_save signal fixes .reorg on new/old blocks and fixes
            # inputs/outputs
            web_socket_msg_type = 'reorged'
        web_socket_msg = BlockSerializer(new_block).data
        if web_socket_msg_type == 'reorged':
            web_socket_msg = blockchain.slug
        # TODO: check if channels-redis 4.x is fixed: https://github.com/django/channels_redis/issues/332
        channel_layer = channels.layers.get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'default_group',
            {
                'type': web_socket_msg_type,
                'message': web_socket_msg,
            }
        )
        # update the loading progress since it could be skewed due to the
        # periodic task updating it before this view has been called
        try:
            update_blockchain_progress(blockchain)
        except UpdateBlockchainProgressError:
            # ignore it, let it update itself the next time
            pass
        return Response(status=status.HTTP_200_OK)

    def get_permissions(self):
        """
        Add, delete and update require authentication, others don't.
        """
        # accepted view can currently be called by anyone, we ignore its data though
        # and fetch it from our node. Maybe in the future node could send some
        # header to prevent potential spam
        permission_classes = []
        if self.action not in ['list', 'retrieve', 'accepted', 'graphs']:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class BlockViewSet(CustomModelViewSet):
    """API endpoint for Block. This ViewSet is nested in BlockchainViewSet."""
    queryset = Block.objects\
        .order_by('-height')\
        .all()
    filter_backends = get_filter_backends({
        'SearchFilter': CustomBlockSearchFilter,
    })
    filterset_class = BlockFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return BlockSerializer
        if self.action == 'retrieve':
            return BlockDetailSerializer

    def get_queryset(self, *args, **kwargs):
        blockchain_slug = self.kwargs.get("blockchain_slug")
        try:
            blockchain = Blockchain.objects.get(slug=blockchain_slug)
        except Blockchain.DoesNotExist:
            raise NotFound('A blockchain with this slug does not exist.')
        # don't include reorged blocks on list-view unless explicitly asked to
        # if there's a reorg at height X then block at height X, which is on the
        # main chain, will have reorg info included in its serializer
        queryset = self.queryset.filter(blockchain=blockchain)
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'inputs__output__block',
                'outputs__inputs__block__reorg',
                'kernels',
            )
        elif (
            self.action == 'list' and
            not self.request.GET.get('include_reorgs', '0') == '1'
            and not self.request.GET.get('search')
        ):
            queryset = self.queryset.filter(blockchain=blockchain, reorg=None)
        return queryset

    def get_permissions(self):
        """
        Add, delete and update require authentication, others don't.
        """
        permission_classes = []
        if self.action not in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

