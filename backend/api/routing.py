from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    re_path(r'ws/socket-server/admin', consumers.AdminConsumer.as_asgi()),
    re_path(r'ws/socket-server', consumers.RegularConsumer.as_asgi()),
]
