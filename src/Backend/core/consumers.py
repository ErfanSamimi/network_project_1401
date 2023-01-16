import base64
import json
import os
import pathlib
import time
import traceback

from channels.auth import login, logout
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth import authenticate
from django.db.models import Q
from django.core.files import File

from chat_app import settings
from chat_app.settings import TESTING, BASE_DIR
from core.models import ChatRoom, Message, User, ChatRoom_Member
from core.serializer import serialize_message
from email_verification.views import send_email_confirmation


class RegisterUser(WebsocketConsumer):

    def receive(self, text_data):

        """
            text_data = {
            "email": "test@test.com",
            "phone_number": "09131234567",
            "password": "password"
        }
        """
        text_data_json = json.loads(text_data)

        user = User.objects.filter(
            Q(email=text_data_json['email']) |
            Q(phone_number=text_data_json['phone_number'])
        )
        if user.exists():
            self.send(text_data=json.dumps({'evnet': 'error', 'description': "A user exists with this values"}))


        else:
            try:
                user = User.objects.create_user(
                    email=text_data_json['email'],
                    phone_number=text_data_json['phone_number'],
                    password=text_data_json['password']
                )
                # send_email_confirmation(user_id=user.id, user_email=user.email)
                self.send(text_data=json.dumps({'event': 'add_user', 'description': "User created"}))

            except:
                traceback.print_exc()
                self.send(text_data=json.dumps({'event': 'error', 'description': "Bad Parameters!"}))


class SendMedia(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user']
        temp = ChatRoom_Member.objects.filter(chat_room__chat_room_id=self.room_name, member=self.user)
        if temp:
            self.chatroom = temp.first().chat_room
            self.accept()

    def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)
        message_id = json_data['message_id']
        messages = Message.objects.filter(chat_room__chat_room_id=self.room_name, id=message_id)
        if messages.exists() and messages.first().type in ['voice', 'image']:
            message = messages.first()
            if message.type == 'voice':
                file = message.voice
            else:
                file = message.image

            file_data = file.read()

            base64_bytes = base64.b64encode(file_data)
            base64_string = base64_bytes.decode('utf-8')
            data = {'event': 'file_contents',
                    'message_id': message.id,
                    'file_name': pathlib.PurePath(file.path).name,
                    'data': base64_string
                    }

            self.send(text_data=json.dumps(data))
        else:
            self.send(text_data=json.dumps({'event': 'error', 'description': "Invalid message id"}))


class DeleteMessage(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user']

        temp = ChatRoom_Member.objects.filter(chat_room__chat_room_id=self.room_name, member=self.user)

        if temp.exists():

            self.chatroom = temp.first().chat_room
            self.room_group_name = f'{self.chatroom.chat_room_type}_{self.room_name}'

            async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
            print("Accepted...")
            self.accept()

        else:
            print("Rejected...")
            self.close()


    def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)
        message_id = json_data['message_id']
        messages = Message.objects.filter(chat_room=self.chatroom, sender=self.user, id=message_id)

        if messages.exists():
            message = messages.first()
            message.delete()
            context = {
                'type': 'delete_message',
                'message_id': message_id,
            }
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, context)

        else:
            data = {'event': 'error', 'description': 'No message found with this id !'}
            self.send(text_data=json.dumps(data))

    def delete_message(self, event):
            message_id = event['message_id']
            data = {'event': "delete_message", 'message_id': message_id}

            text_data = json.dumps(data)
            self.send(text_data=text_data)

    def chatroom_message(self, event):
        message = event['message']

        messages = serialize_message(message)
        data = {
            'event': "message",
            'messages': [messages]
        }

        text_data = json.dumps(data)
        self.send(text_data=text_data)


class UserSearch(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']

        if settings.TESTING:
            self.accept()

        if not self.user:
            self.close()
        else:
            self.accept()


    def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)
        keyword = json_data.get('keyword')

        if keyword and keyword[0] == '@':
            users = User.objects.filter(user_id__contains=keyword[1:])
            data = {
                'event': 'search-result',
                'users': [
                    {'username': u.user_id, 'phone_number': u.phone_number} for u in users
                ]
            }
            self.send(json.dumps(data))

        elif keyword:
            users = User.objects.filter(phone_number__contains=keyword, show_phone_number=True)
            data = {
                'event': 'search-result',
                'users': [
                    {'username': u.user_id, 'phone_number': u.phone_number} for u in users
                ]
            }
            self.send(json.dumps(data))

        else:
            self.send(json.dumps({'event': "error", 'description': "invalid keyword"}))


class EditProfile(WebsocketConsumer):

    def send_user_data(self):
        profile_photo = None
        profile_photo_name = None
        if self.user.profile_image:
            pic = self.user.profile_image.read()
            # with open(self.user.profile_image.path, 'rb') as file:
            #     pic = file.read()
            base64_bytes = base64.b64encode(pic)
            profile_photo = base64_bytes.decode('utf-8')
            profile_photo_name = pathlib.PurePath(self.user.profile_image.path).name

        data = {
            'profile_image': profile_photo,
            'profile_photo_name': profile_photo_name,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'user_id': self.user.user_id,
            'email': self.user.email,
            'phone_number': self.user.phone_number,
            'show_profile_pic': self.user.show_profile_pic,
            'show_phone_number': self.user.show_phone_number,
        }
        self.send(text_data=json.dumps(data))



    def connect(self):
        self.user = self.scope['user']

        if not self.user:
            self.close()
        else:
            self.accept()
            self.send_user_data()

    def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)
        update_fields = ['first_name', 'last_name', 'user_id', 'show_profile_pic', 'show_phone_number']
        print(json_data)
        if json_data.get('profile_image', None):
            file_extension = json_data['file_name'].split('.')[-1]
            base64_file_data = json_data['profile_image'].split(';base64,')[1]
            print(base64_file_data)
            base64_bytes = base64_file_data.encode('utf-8')
            temp_file_path = os.path.join(
                BASE_DIR, 'temp', f'{self.user.id}-{round(time.time() * 1000)}.{file_extension}'
            )
            with open(temp_file_path, 'wb') as file:
                file.write(base64.decodebytes(base64_bytes))

            with open(temp_file_path, 'rb') as file:
                self.user.profile_image = File(file)
                self.user.save(update_fields=['profile_image'])
            os.remove(temp_file_path)


        self.user.first_name = json_data['first_name']
        self.user.last_name = json_data['last_name']
        self.user.user_id = json_data['user_id']
        self.user.show_profile_pic = json_data['show_profile_pic']
        self.user.show_phone_number = json_data['show_phone_number']
        try:
            self.user.save(update_fields=update_fields)
        except:
            pass

        self.send_user_data()


class UserInfo(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']

        if not self.user:
            self.close()
        else:
            self.accept()

    def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)
        user_email = json_data['user_email']
        user = User.objects.filter(email=user_email)

        if user.exists():
            user = user.first()
            profile_pic = None
            profile_pic_name = None
            if user.profile_image and user.show_profile_pic:
                pic = user.profile_image.read()
                base64_bytes = base64.b64encode(pic)
                profile_pic = base64_bytes.decode('utf-8')
                profile_pic_name = pathlib.PurePath(user.profile_image.path).name

            data = {
                'event': 'user_info',
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': None if not user.show_phone_number else user.phone_number,
                'email': user.email,
                'profile_pic': profile_pic,
                'profile_pic_name': profile_pic_name
            }

            self.send(text_data=json.dumps(data))
        else:
            self.send(text_data=json.dumps({'event': 'error', 'description': 'Bad user email'}))


