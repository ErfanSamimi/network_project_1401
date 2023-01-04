from django.urls import path
from core.views import authentication_view, chatbox_view, user_profile_change_view, joinchat_view

urlpatterns = [
    path('user/auth/', authentication_view, name='authentication'),
    path('chat/chatpage/', chatbox_view, name='chat_page'),
    path('join/<str:chatroom_id>', joinchat_view, name='join_chat'),
    path('user/profile_change/', user_profile_change_view, name='user_profile_change'),
]
