import base64

from django.core.files import File
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import time
import os

from django.db.models import Count
from django.utils.crypto import get_random_string

from chat_app.settings import BASE_DIR
from core.exceptions import NotChannelError, AlreadyExistsInChatroom, InvalidRole, NotGroupError, ChatRoomExistsError


def validate_phone_number(value):
    for i in value:
        if not str.isdigit(i):
            return False

    return True


def profile_image_path(instance, filename):
    ext = filename.split('.')[-1]
    return os.path.join("profile_pics", str(instance.id), f'{round(time.time() * 1000)}.{ext}')


class UserManager(BaseUserManager):
    def create_user(self, email, phone_number, password, **extra_fields):
        if not email:
            raise ValueError("User must have a email")

        if not phone_number:
            raise ValueError("User must have a phone_number")

        if not password:
            raise ValueError("User must have a password")

        instance = self.model(
            email=email, phone_number=phone_number, **extra_fields)
        instance.set_password(password)
        instance.save()
        return instance

    def create_superuser(self, email, phone_number, password):
        user = self.create_user(
            email=email, phone_number=phone_number, password=password)
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        unique=True, max_length=11, validators=[validate_phone_number])
    user_id = models.CharField(max_length=20, unique=True, null=True)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True)

    profile_image = models.ImageField(upload_to=profile_image_path, null=True)

    register_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone_number'
    objects = UserManager()

    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    show_profile_pic = models.BooleanField(default=True)
    show_phone_number = models.BooleanField(default=True)

    def __str__(self):
        return self.email



class ChatroomManager(models.Manager):
    def create(self):
        chat_room_id = get_random_string(50)
        while super().get_queryset().filter(chat_room_id=chat_room_id).exists():
            chat_room_id = get_random_string(50)

        instance = self.model(chat_room_id=chat_room_id,
                              chat_room_type='direct')
        instance.save()
        return instance

    def create_direct_chat(self, member1, member2):
        temp = ChatRoom_Member.objects.filter(
            chat_room__chat_room_type='direct', member__in=[member1, member2]
        ).values('chat_room').annotate(count=Count('chat_room')).filter(count=2)

        if temp.exists():
            raise ChatRoomExistsError("A direct chat exists for these users")

        instance = self.create()
        ChatRoom_Member.objects.create(
            chat_room=instance, member=member1, role='member')
        ChatRoom_Member.objects.create(
            chat_room=instance, member=member2, role='member')
        return instance


class ChatRoom(models.Model):
    CHATROOM_TYPES = ['direct', 'group', 'channel']
    __type_choices = [(x, x) for x in CHATROOM_TYPES]
    chat_room_type = models.CharField(
        max_length=10, choices=__type_choices, default='direct')
    chat_room_id = models.CharField(max_length=50, unique=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    objects = ChatroomManager()

    def __str__(self):
        return self.chat_room_id


class GroupChatManager(ChatroomManager):
    def create(self, group_name, creator):
        instance = super().create()
        instance.chat_room_type = 'group'
        instance.title = group_name
        instance.save(update_fields=('chat_room_type', 'title'))
        ChatRoom_Member.objects.create(
            chat_room=instance, member=creator, role='creator')
        return instance

    def create_direct_chat(self, member1, member2):
        return None


class GroupChat(ChatRoom):
    title = models.CharField(max_length=50)
    objects = GroupChatManager()


class ChannelsManager(GroupChatManager):
    def create(self, channel_name, creator):
        instance = super().create(channel_name, creator)
        instance.chat_room_type = 'channel'
        instance.save(update_fields=('chat_room_type',))
        return instance


class Channels(ChatRoom):
    title = models.CharField(max_length=50)
    objects = ChannelsManager()


class ChatRoom_MemberManager(models.Manager):
    def add_channel_member(self, chat_room, user, role):
        if chat_room.chat_room_type != 'channel':
            raise NotChannelError('This chatroom is not a channel')

        if role not in ['admin', 'muted']:
            raise InvalidRole(
                "User must has on of these roles: ['admin', 'muted']")

        temp = super().get_queryset().filter(chat_room=chat_room, member=user, role__in=['admin', 'member', 'muted'])

        if temp.exists() and temp.first().role != role:
            instance = temp.first()
            instance.role = role
            instance.save(update_fields=('role',))
            return instance
        elif not temp.exists():
            instance = self.model(chat_room=chat_room, member=user, role=role)
            instance.save()
            return instance
        else:
            raise AlreadyExistsInChatroom(
                "This user exists in this channel with given role")

    def add_group_member(self, chat_room, user, role):
        if chat_room.chat_room_type != 'group':
            raise NotGroupError('This chatroom is not a group')

        if role not in ['admin', 'muted', 'member']:
            raise InvalidRole(
                "User must has on of these roles: ['admin', 'muted', 'member']")

        temp = super().get_queryset().filter(chat_room=chat_room, member=user, role__in=['admin', 'member', 'muted'])

        if temp.exists() and temp.first().role != role:
            instance = temp.first()
            instance.role = role
            instance.save(update_fields=('role',))
            return instance
        elif not temp.exists():
            instance = self.model(chat_room=chat_room, member=user, role=role)
            instance.save()
            return instance
        else:
            raise AlreadyExistsInChatroom(
                "This user exists in this group with given role")


class ChatRoom_Member(models.Model):
    MEMBER_ROLES = {'creator', 'admin', 'member', 'muted'}

    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    member = models.ForeignKey(User, on_delete=models.CASCADE)

    __role_choices = [(x, x) for x in MEMBER_ROLES]
    role = models.CharField(choices=__role_choices,
                            default='member', max_length=10)

    objects = ChatRoom_MemberManager()

    class Meta:
        unique_together = ('chat_room', 'member')

    def __str__(self):
        return self.chat_room.chat_room_id


def image_message_path(instance, filename):
    ext = filename.split('.')[-1]
    return os.path.join(
        "image_messages", str(instance.sender.id), str(
            instance.chat_room.id), f'{round(time.time() * 1000)}.{ext}'
    )


def file_message_path(instance, filename):
    ext = filename.split('.')[-1]
    return os.path.join(
        "file_messages", str(instance.sender.id), str(
            instance.chat_room.id), f'{round(time.time() * 1000)}.{ext}'
    )


class MessageManager(models.Manager):

    def __create_media_message(self, sender, chat_room, base64_file_data: str, file_extension: str):
        instance = self.model(sender=sender, chat_room=chat_room)
        base64_bytes = base64_file_data.encode('utf-8')
        temp_file_path = os.path.join(
            BASE_DIR, 'temp', f'{sender.id}-{round(time.time() * 1000)}.{file_extension}')
        with open(temp_file_path, 'wb') as file:
            file.write(base64.decodebytes(base64_bytes))

        return instance, temp_file_path

    def create_image_message(self, sender, chat_room, image_base64_data: str, file_extension: str):
        instance, temp_file_path = self.__create_media_message(
            sender, chat_room, image_base64_data, file_extension)
        instance.type = 'image'
        instance.text = None
        instance.voice = None
        with open(temp_file_path, 'rb') as file:
            instance.image = File(file)
            instance.save()
        print(temp_file_path)
        os.remove(temp_file_path)
        return instance

    def create_voice_message(self, sender, chat_room, voice_base64_data: str, file_extension: str):
        instance, temp_file_path = self.__create_media_message(
            sender, chat_room, voice_base64_data, file_extension)
        instance.type = 'voice'
        instance.text = None
        instance.image = None
        with open(temp_file_path, 'rb') as file:
            instance.voice = File(file)
            instance.save()
        os.remove(temp_file_path)
        return instance

    def create_text_message(self, sender, chat_room, text):
        instance = self.model(sender=sender, chat_room=chat_room,
                              text=text, type='text', voice=None, image=None)
        instance.save()
        return instance


class Message(models.Model):
    MESSAGE_TYPES = ['text', 'image', 'voice']

    __message_choices = [(x, x) for x in MESSAGE_TYPES]
    type = models.CharField(
        max_length=10, choices=__message_choices, default='text')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)

    text = models.TextField(null=True)
    image = models.ImageField(upload_to=image_message_path, null=True)
    voice = models.FileField(upload_to=file_message_path, null=True)

    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    send_date = models.DateTimeField(auto_now_add=True)

    objects = MessageManager()

    def __str__(self):
        return self.chat_room.chat_room_id
