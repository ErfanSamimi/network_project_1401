from django.urls import path, re_path

from chat import consumers

websocket_urlpatterns = [
    path('ws/chat/chatroom/<str:room_name>/',
         consumers.ChatRoomConsumer.as_asgi()),
    path('ws/chat/userchats/', consumers.UserChats.as_asgi()),
    path('ws/group/create/', consumers.GroupCreation.as_asgi()),
    path('ws/channel/create/', consumers.ChannelCreation.as_asgi()),
    path('ws/join/<str:room_name>/', consumers.AddMember.as_asgi()),
]
