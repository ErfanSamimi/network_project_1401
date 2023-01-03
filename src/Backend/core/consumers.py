import base64
import json
import pathlib
from channels.auth import login, logout
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth import authenticate
from django.db.models import Q

from chat_app import settings
from chat_app.settings import TESTING
from core.models import ChatRoom, Message, User, ChatRoom_Member


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

                self.send(text_data=json.dumps({'event': 'add_user', 'description': "User created"}))
            except:
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

