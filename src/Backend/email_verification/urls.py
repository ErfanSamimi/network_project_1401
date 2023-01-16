from django.urls import path, include
from .views import confirm_email

urlpatterns = [
    path('user/auth/confirm-email/<str:token>', confirm_email)
]
