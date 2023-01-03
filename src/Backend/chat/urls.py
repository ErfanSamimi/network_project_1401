from django.urls import path

from . import views

urlpatterns = [
    # path('<str:room_name>/', views.room, name='room'),
    path('create-chatroom/', views.chatroom_creation, name='chatroom_creation'),
    path('chatroom-management/', views.chatroom_management, name='chatroom_management'),
]
