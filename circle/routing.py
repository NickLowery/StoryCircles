from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/circle/(?P<circle_pk_string>\w+)/$',
            consumers.CircleConsumer.as_asgi()),
    re_path(r'ws/circle_index/$',
            consumers.CircleIndexConsumer.as_asgi()),
]
