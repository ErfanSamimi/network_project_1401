from django.core.mail import EmailMultiAlternatives
from django.db import models

# Create your models here.
from django.utils import timezone
from datetime import timedelta
from core.models import User
from chat_app import settings


class EmailVerifyToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=50)
    expire_time = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expire_time:
            self.expire_time = timezone.now() + timedelta(minutes=settings.EMAIL_VERIFY_EXPIRE_MINUTES)
        super(EmailVerifyToken, self).save(*args, **kwargs)

    def is_expire(self):
        return True if timezone.now() > self.expire_time else False

class Email(models.Model):
    TYPE_EMAIL_VERIFY = 1
    TYPE_FORGET_PASSWORD = 2

    EMAIL_TYPE = [
        (TYPE_EMAIL_VERIFY, 'EMAIL VERIFY'),
        (TYPE_FORGET_PASSWORD, 'FORGET PASSWORD'),
    ]
    receiver_email = models.EmailField()
    sender_email = models.EmailField()
    email_type = models.IntegerField(choices=EMAIL_TYPE)
    email_content = models.CharField(max_length=50000)
    email_subject = models.CharField(max_length=200)
    email_detail = models.CharField(max_length=500)
    is_send = models.BooleanField(default=False)

    def send_email(self):
        email = EmailMultiAlternatives(subject=self.email_subject, from_email=self.sender_email,
                                       to=[self.receiver_email])
        email.attach_alternative(self.email_content, "text/html")
        email.send()
        self.is_send = True
        self.save()

