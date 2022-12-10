from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http.response import HttpResponse, HttpResponseRedirect
from .forms import LoginForm

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
