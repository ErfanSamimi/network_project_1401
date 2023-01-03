from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path('ws/user/register/', consumers.RegisterUser.as_asgi()),
    path('ws/user/search/', consumers.UserSearch.as_asgi()),
    path('ws/user/edit-profile/', consumers.EditProfile.as_asgi()),
    path('ws/user/info/', consumers.UserInfo.as_asgi()),
    path('ws/media/<str:room_name>/', consumers.SendMedia.as_asgi()),
    path('ws/delete/<str:room_name>/', consumers.DeleteMessage.as_asgi()),
]
