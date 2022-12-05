import base64
import json
import pathlib

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db.models import Q
from chat_app.settings import TESTING
from core.models import ChatRoom, Message, User, ChatRoom_Member


class RegisterUser(WebsocketConsumer):

    def receive(self, text_data):
        text_data_json = json.loads(text_data)

        user = User.objects.filter(
            Q(email=text_data_json['email']) |
            Q(phone_number=text_data_json['phone_number']) |
            Q(user_id=text_data_json['user_id'])
        )
        if user.exists():
            self.send(text_data=json.dumps({'evnet': 'error', 'description': "A user exists with this values"}))

        else:
            try:
                user = User.objects.create_user(**text_data_json)
                self.send(text_data=json.dumps({'event': 'add_user', 'description': "User created"}))
            except:
                self.send(text_data=json.dumps({'event': 'error', 'description': "Bad Parameters!"}))



class SendImage(WebsocketConsumer):


    def get_message_queryset(self, chatroom, message_id):
        return Message.objects.filter(chat_room=chatroom, id=message_id, type='image')

    def get_file(self, message):
        return message.image

    def connect(self):
        room_name = self.scope['url_route']['kwargs']['room_name']
        message_id = self.scope['url_route']['kwargs']['message_id']
        user = self.scope['user']

        if TESTING:
            user = User.objects.get(id=12)

        temp = ChatRoom_Member.objects.filter(chat_room__chat_room_id=room_name, member=user)

        if temp:
            chatroom = temp.first().chat_room
            print("Accepted...")
            self.accept()
            messages = self.get_message_queryset(chatroom, message_id)

            if not messages:
                data = {'event': 'error', 'description': 'No file found with this id for given chatroom'}
                self.send(text_data=json.dumps(data))
            else:
                message = messages.first()
                file = self.get_file(message)
                img = file.read()

                base64_bytes = base64.b64encode(img)
                base64_string = base64_bytes.decode('utf-8')
                data = {'event': 'file_contents',
                        'message_id': message.id,
                        'file_name': pathlib.PurePath(file.path).name,
                        'data': base64_string
                        }

                self.send(text_data=json.dumps(data))

        else:
            print("Rejected...")

        self.close()


class SendVoice(SendImage):
    def get_message_queryset(self, chatroom, message_id):
        return Message.objects.filter(chat_room=chatroom, id=message_id, type='voice')

    def get_file(self, message):
        return message.voice







class DeleteMessage(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.message_id = self.scope['url_route']['kwargs']['message_id']
        self.user = self.scope['user']

        if TESTING:
            self.user = User.objects.get(id=12)

        temp = ChatRoom_Member.objects.filter(chat_room__chat_room_id=self.room_name, member=self.user)

        if temp.exists():

            self.chatroom = temp.first().chat_room
            self.room_group_name = f'{self.chatroom.chat_room_type}_{self.room_name}'

            async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
            print("Accepted...")
            self.accept()

            messages = Message.objects.filter(chat_room=self.chatroom, sender=self.user, id=self.message_id)

            if messages.exists():
                message = messages.first()
                message.delete()
                context = {
                    'type': 'delete_message',
                    'message_id': self.message_id,
                }
                async_to_sync(self.channel_layer.group_send)(self.room_group_name, context)

            else:
                data = {'event': 'error', 'description': 'No message found with this id !'}
                self.send(text_data=json.dumps(data))

        else:
            print("Rejected...")
            self.close()




    def delete_message(self, event):
            message_id = event['message_id']
            data = {'event': "delete_message", 'message_id': message_id}

            text_data = json.dumps([data])
            self.send(text_data=text_data)
