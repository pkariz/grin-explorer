from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from .helpers import load_data_from_redis

import json
import logging


logger = logging.getLogger(__name__)


class RegularConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
            'default_group',
            self.channel_name,
        )
        self.accept()
        self.send(text_data=json.dumps({
            'type': 'price_update',
            'message': load_data_from_redis(settings.REDIS_PRICE_KEY),
        }))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            'default_group',
            self.channel_name
        )
        super().disconnect(close_code)

    def send_block(self, event):
        block_data = event['message']
        self.send(text_data=json.dumps({
            'type': 'new_block',
            'message': block_data,
        }))

    def reorged(self, event):
        blockchain_slug = event['message']
        self.send(text_data=json.dumps({
            'type': 'reorged',
            'message': blockchain_slug,
        }))

    def price_update(self, event):
        price_data = event['message']
        self.send(text_data=json.dumps({
            'type': 'price_update',
            'message': price_data,
        }))


class AdminConsumer(WebsocketConsumer):
    def connect(self):
        logger.debug('WebSocketConsumer CONNECTED', extra={'channel_name': self.channel_name})
        async_to_sync(self.channel_layer.group_add)(
            'admin_group',
            self.channel_name,
        )
        self.accept()

    def disconnect(self, close_code):
        logger.debug('WebSocketConsumer DISCONNECTED', extra={'channel_name': self.channel_name})
        async_to_sync(self.channel_layer.group_discard)(
            'admin_group',
            self.channel_name
        )
        super().disconnect(close_code)

    def blockchain_progress_changed(self, event):
        logger.debug(
            'WebSocketConsumer PROGRESS_CHANGED',
            extra={
                'blockchain': event['message']['slug'],
                'load_progress': event['message']['load_progress'],
                'channel': self.channel_name,
            },
        )
        self.send(text_data=json.dumps({
            'type': 'blockchain_progress_changed',
            'message': event['message'],
        }))

    def task_status_changed(self, event):
        self.send(text_data=json.dumps({
            'type': 'task_status_changed',
            'message': event['message'],
        }))

    def blockchain_deleted(self, event):
        self.send(text_data=json.dumps({
            'type': 'blockchain_deleted',
            'message': event['message'],
        }))

