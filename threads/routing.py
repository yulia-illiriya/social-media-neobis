from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from . import consumers

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
    ]),
})