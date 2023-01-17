from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http.response import HttpResponse, HttpResponseRedirect
from .forms import LoginForm
from .models import ChatRoom, ChatRoom_Member


def authentication_view(request):
    if request.user.is_authenticated:
        return HttpResponse("Already logged in!")

    form = LoginForm(request.POST or None)

    if form.is_valid():
        user = authenticate(username=form.cleaned_data.get("phone_number"), password=form.cleaned_data.get('password'))
        if user:
            login(request, user=user)
            return redirect('chat_page')
            return HttpResponse(f"Logged In as {user.phone_number}")

    return render(request, 'auth/login & signup.html', {'login_form': form})


@login_required
def chatbox_view(request):
    return render(request, 'chatbox/index.html', {"user_email": request.user.email})


def user_profile_change_view(request):
    return render(request, 'user-profile/UserProfileChange.html')


@login_required
def joinchat_view(request, chatroom_id):
    if request.user.is_email_verified:
        chatroom = ChatRoom.objects.filter(chat_room_id=chatroom_id, chat_room_type__in=['channel', 'group'])
        if chatroom.exists():
            chatroom = chatroom.first()
            chatmember = ChatRoom_Member.objects.filter(chat_room=chatroom, member=request.user)
            if not chatmember.exists():
                if chatroom.chat_room_type == 'channel':
                    ChatRoom_Member.objects.add_channel_member(chatroom, request.user, 'muted')
                else:
                    ChatRoom_Member.objects.add_group_member(chatroom, request.user, 'member')

    return redirect('chat_page')
