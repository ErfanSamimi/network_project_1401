import json
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from asgiref.sync import async_to_sync
from core.models import ChatRoom, Message, User, ChatRoom_Member
from core.serializer import serialize_message
from chat_app.settings import TESTING



class ChatRoomConsumer(WebsocketConsumer):
    def connect(self):
        print(self.channel_name)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user']

        if TESTING:
            self.user = User.objects.get(id=12)

        temp = ChatRoom_Member.objects.filter(chat_room__chat_room_id=self.room_name, member=self.user)

        if temp:
            self.chatroom = temp.first().chat_room
            self.room_group_name = f'{self.chatroom.chat_room_type}_{self.room_name}'
            async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
            print("Accepted...")
            self.accept()

            messages = Message.objects.filter(chat_room=self.chatroom).order_by('send_date')
            message_list = {'event': 'total_messages', 'messages': [serialize_message(m) for m in messages]}
            self.send(text_data=json.dumps(message_list))

        else:
            print("Rejected...")
            self.close()


    def disconnect(self, close_code):
        try:
            async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
        except AttributeError:
            pass
        self.close()



    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        message_type = text_data_json['message_type']

        member_role = ChatRoom_Member.objects.filter(
            chat_room__chat_room_id=self.room_name,
            member=self.user
        ).first().role

        if member_role == 'muted':
            self.send(text_data=json.dumps({'event': 'error', 'description': "You are muted !"}))

        elif message_type not in Message.MESSAGE_TYPES:
            self.send(text_data=json.dumps({'event': 'error', 'description': 'Bad message type !'}))

        else:
            if message_type == 'text':
                message = Message.objects.create_text_message(self.user, self.chatroom, text_data_json['text'])

            elif message_type == 'image':
                message = Message.objects.create_image_message(
                    self.user,
                    self.chatroom, text_data_json['data'],
                    text_data_json['file_extension']
                )
            else:
                message = Message.objects.create_voice_message(
                    self.user,
                    self.chatroom, text_data_json['data'],
                    text_data_json['file_extension']
                )


            context = {
                'type': 'chatroom_message',
                'message': message,
            }
            async_to_sync(self.channel_layer.group_send)(self.room_group_name, context)



    def chatroom_message(self, event):
        message = event['message']

        data = serialize_message(message)
        data['event'] = "new_message"

        text_data = json.dumps([data])
        self.send(text_data=text_data)

    def delete_message(self, event):
            message_id = event['message_id']
            data = {'event': "delete_message", 'message_id': message_id}

            text_data = json.dumps([data])
            self.send(text_data=text_data)



