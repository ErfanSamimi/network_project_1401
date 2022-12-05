from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path('ws/user/register/', consumers.RegisterUser.as_asgi()),
    path('ws/image/<str:room_name>/<int:message_id>/', consumers.SendImage.as_asgi()),
    path('ws/voice/<str:room_name>/<int:message_id>/', consumers.SendVoice.as_asgi()),
    path('ws/delete/<str:room_name>/<int:message_id>/', consumers.DeleteMessage.as_asgi()),
]
