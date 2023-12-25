from datetime import datetime, timedelta
from itertools import groupby
from django.db.models import Count
from backend.api.models import Block

import pytz


def get_transaction_graph_data(blockchain_slug):
    # set time to zero so that you get blocks for full 'first' day
    today = datetime.utcnow()\
        .replace(hour=0, minute=0, second=0, microsecond=0)\
        .astimezone(pytz.utc)
    last_week = today - timedelta(days=7)
    res = list(Block.objects\
        .filter(
            blockchain__slug=blockchain_slug,
            reorg=None,
            timestamp__gte=last_week,
        )\
        .prefetch_related('kernels', 'inputs', 'outputs')\
        .annotate(
            kernels_count=Count('kernels', distinct=True),
            inputs_count=Count('inputs', distinct=True),
            outputs_count=Count('outputs', distinct=True),
        )\
        .order_by('timestamp')\
        .values('pk', 'timestamp', 'kernels_count', 'inputs_count', 'outputs_count'))
    tx_graph_data = []
    # group by day
    res = sorted(res, key=lambda x: x['timestamp'].date(), reverse=True)
    for key, group in groupby(res, lambda x: x['timestamp'].date()):
        kernels, inputs, outputs = 0, 0, 0
        for block in group:
            kernels += block['kernels_count']
            inputs += block['inputs_count']
            outputs += block['outputs_count']
        tx_graph_data.append({
            'date': str(key),
            'kernels': kernels,
            'inputs': inputs,
            'outputs': outputs,
        })
    # reverse it so that you have increasing by date
    return list(reversed(tx_graph_data))

