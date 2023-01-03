from django.urls import path, re_path

from chat import consumers

websocket_urlpatterns = [
    path('ws/chat/chatroom/<str:room_name>/',
         consumers.ChatRoomConsumer.as_asgi()),
    path('ws/chatroom/create/', consumers.ChatroomCreation.as_asgi()),
    path('ws/chat/userchats/', consumers.UserChats.as_asgi()),
    path('ws/chatroom/create/', consumers.ChatroomCreation.as_asgi()),
    path('ws/join/<str:room_name>/', consumers.AddMember.as_asgi()),
    path('ws/remove/<str:room_name>/', consumers.RemoveMember.as_asgi()),
]
