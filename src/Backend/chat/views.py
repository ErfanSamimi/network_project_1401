from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def chatroom_creation(request):
    return render(request, 'chatroom-creation/chatroom_creation.html')

