from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from dramatiq import get_broker
from dramatiq_abort import Abortable, backends
from .bootstrap import update_blockchain_progress
from .exceptions import UpdateBlockchainProgressError
from .graphs import get_transaction_graph_data
from .models import Blockchain
from .helpers import (
    get_func_from_dotted_path,
    store_data_in_redis,
    load_data_from_redis,
)

import dramatiq
import logging
import redis


logger = logging.getLogger(__name__)


# enable task abort
redis = redis.Redis(host='redis')
event_backend = backends.RedisBackend(client=redis)
# set 1 year ttl for keys
abortable = Abortable(backend=event_backend, abort_ttl=1000*60*60*24*365)
get_broker().add_middleware(abortable)


# NOTE: django-dramatiq auto-discovers tasks in app/tasks.py
@dramatiq.actor(max_retries=0, time_limit=float("inf"))
def bootstrap_blockchain(blockchain_slug):
    # import here to avoid cyclic import
    from .models import Blockchain
    Blockchain.objects.get(slug=blockchain_slug).bootstrap()


@dramatiq.actor(max_retries=0)
def update_blockchains_progress_task():
    for blockchain in Blockchain.objects.all():
        try:
            update_blockchain_progress(blockchain)
        except UpdateBlockchainProgressError:
            continue


@dramatiq.actor(max_retries=0)
def update_price_task():
    price_datas = {}
    blockchains = list(Blockchain.objects.all())
    # refetch price
    for blockchain in filter(lambda bc: bc.fetch_price, blockchains):
        try:
            price_fn = get_func_from_dotted_path(settings.GET_PRICE_FN)
            price_datas[blockchain.slug] = price_fn(blockchain)
        except Exception as e:
            logger.exception(
                'Failed to get price data',
                extra={'blockchain': blockchain.slug}
            )
            # we don't update the value in redis otherwise it might cause
            # unnecessary panic when a single request fails for some reason
            current_data = load_data_from_redis(settings.REDIS_PRICE_KEY)
            if current_data and current_data.get(blockchain.slug):
                price_datas[blockchain.slug] = current_data[blockchain.slug]
    # set default 0 price for blockchains with fetch_price set to false
    for blockchain in filter(lambda bc: not bc.fetch_price, blockchains):
        price_datas[blockchain.slug] = {
            'btc_value': '0',
            'percent_change': '0.00',
        }
    # store in redis so that when a new user visits the page we can get
    # that data from somewhere
    store_data_in_redis(settings.REDIS_PRICE_KEY, price_datas)
    # send info through websocket
    async_to_sync(get_channel_layer().group_send)(
        'default_group',
        {
            'type': 'price_update',
            'message': price_datas,
        }
    )


@dramatiq.actor(max_retries=0, time_limit=float("inf"))
def delete_blockchain(blockchain_slug):
    # import here to avoid cyclic import
    from .models import Blockchain
    Blockchain.objects.get(slug=blockchain_slug).delete()
    async_to_sync(get_channel_layer().group_send)(
        'admin_group',
        {
            'type': 'blockchain_deleted',
            'message': {
                'slug': blockchain_slug,
            },
        }
    )


@dramatiq.actor(max_retries=0)
def update_graphs():
    graph_name_to_fn_mapper = {
        'tx_graph__{}': get_transaction_graph_data,
    }
    for blockchain in Blockchain.objects.all():
        for graph_key, get_graph_fn in graph_name_to_fn_mapper.items():
            store_data_in_redis(
                graph_key.format(blockchain.slug),
                get_graph_fn(blockchain.slug)
            )

