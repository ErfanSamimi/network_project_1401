from django.urls import path
from core.views import authentication_view, chatbox_view

urlpatterns = [
    path('user/auth/', authentication_view, name='authentication'),
    path('chat/chatpage/', chatbox_view, name='chat_page'),
]