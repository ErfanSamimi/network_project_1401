from django.shortcuts import render, redirect

# Create your views here.
from django.template.loader import render_to_string
from django.utils import timezone
from hashids import Hashids

from chat_app import settings
from core.models import User
from email_verification.models import EmailVerifyToken, Email


def send_email_confirmation(user_id, user_email):
    hashids_verify_email = Hashids(salt=settings.EMAIL_VERIFY_SALT, min_length=10)
    if EmailVerifyToken.objects.filter(user_id=user_id).first():
        email_verify_token = EmailVerifyToken.objects.filter(user=user_id).first()
        token = email_verify_token.token
    else:
        token = hashids_verify_email.encode(int(user_id), timezone.now().microsecond)
        print(user_id)
        email_verify_token = EmailVerifyToken(user=User.objects.get(id=user_id), token=token)
        email_verify_token.save()

    email_subject = "Activate your account"
    email_detail = {
        'first_name': 'User',
        'url': settings.EMAIL_VERIFY_URL + token
    }
    email_content = render_to_string("auth/email_confirmation.html", context=email_detail)
    email = Email(email_content=email_content, email_subject=email_subject, email_type=Email.TYPE_EMAIL_VERIFY,
                  receiver_email=user_email, email_detail=email_detail, sender_email=settings.EMAIL_HOST_USER)
    email.save()
    email.send_email()


def confirm_email(request, token):
    email_verify = EmailVerifyToken.objects.filter(token=token).first()
    if email_verify and not email_verify.is_expire():
        user = email_verify.user
        user.is_email_verified = True
        user.save()
        email_verify.delete()
    return redirect(settings.LOGIN_URL)

