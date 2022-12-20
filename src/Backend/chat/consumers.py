import json
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from asgiref.sync import async_to_sync
from core.models import ChatRoom, Message, User, ChatRoom_Member, Channels, GroupChat
from core.serializer import serialize_message
from chat_app.settings import TESTING
from django.db.models import Q


class GroupCreation(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated and self.user.is_email_verified:
            self.accept()

    def receive(self, text_data):
        data = json.loads(text_data)
        group_name = data['group_name']
        GroupChat.objects.create(group_name, creator=self.user)
        self.send(text_data=json.dumps(
            {'description': 'group creation was successful'}))


class ChatRoomConsumer(WebsocketConsumer):
    def connect(self):
        print(self.channel_name)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.user = self.scope['user']

        if TESTING:
            self.user = User.objects.get(id=12)

        temp = ChatRoom_Member.objects.filter(
            chat_room__chat_room_id=self.room_name, member=self.user)

        if temp:
            self.chatroom = temp.first().chat_room
            self.room_group_name = f'{self.chatroom.chat_room_type}_{self.room_name}'
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name, self.channel_name)
            print("Accepted...")
            self.accept()

            messages = Message.objects.filter(
                chat_room=self.chatroom).order_by('send_date')
            message_list = {'event': 'message', 'messages': [
                serialize_message(m) for m in messages]}
            self.send(text_data=json.dumps(message_list))

        else:
            print("Rejected...")
            self.close()

    def disconnect(self, close_code):
        try:
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name)
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
            self.send(text_data=json.dumps(
                {'event': 'error', 'description': "You are muted !"}))

        elif message_type not in Message.MESSAGE_TYPES:
            self.send(text_data=json.dumps(
                {'event': 'error', 'description': 'Bad message type !'}))

        else:
            if message_type == 'text':
                message = Message.objects.create_text_message(
                    self.user, self.chatroom, text_data_json['text'])

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
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name, context)

    def chatroom_message(self, event):
        message = event['message']

        messages = serialize_message(message)
        data = {
            'event': "message",
            'messages': [messages]
        }

        text_data = json.dumps(data)
        self.send(text_data=text_data)

    def delete_message(self, event):
        message_id = event['message_id']
        data = {'event': "delete_message", 'message_id': message_id}

        text_data = json.dumps([data])
        self.send(text_data=text_data)


class UserChats(WebsocketConsumer):

    @staticmethod
    def get_channel_group_name(user):
        return f'user_chats_{user.phone_number}'

    @staticmethod
    def user_chat_rooms(user):
        channels = Channels.objects.filter(chatroom_member__member=user).values(
            'chat_room_id',
            'title',
            'chatroom_member__role'
        )
        groups = GroupChat.objects.filter(chatroom_member__member=user).values(
            'chat_room_id', 'title',
            'chatroom_member__role'
        )

        directs = ChatRoom_Member.objects.filter(
            member=user,
            chat_room__chat_room_type='direct',
        ).select_related('chat_room')

        chatrooms = list()
        for i in channels:
            data = {
                'chatroom_id': i['chat_room_id'],
                'chatroom_type': 'channel',
                'chatroom_title': i['title'],
                'user_role': i['chatroom_member__role']
            }
            chatrooms.append(data)

        for i in groups:
            data = {
                'chatroom_id': i['chat_room_id'],
                'chatroom_type': 'group',
                'chatroom_title': i['title'],
                'user_role': i['chatroom_member__role']
            }
            chatrooms.append(data)

        for i in directs:
            data = {
                'chatroom_id': i.chat_room.chat_room_id,
                'chatroom_type': 'direct',
                'chatroom_title': ChatRoom_Member.objects.filter(
                    Q(chat_room=i.chat_room) & ~Q(member=i.member)
                ).select_related('member').first().member.email,
                'user_role': i.role
            }
            chatrooms.append(data)

        return chatrooms

    def connect(self):
        self.user = self.scope['user']
        if not self.user:
            self.close()

        else:
            self.accept()
            async_to_sync(self.channel_layer.group_add)(
                UserChats.get_channel_group_name(self.user), self.channel_name)
            context = {
                'type': 'user_chat_list',
                'chats': UserChats.user_chat_rooms(self.user)
            }
            async_to_sync(self.channel_layer.group_send)(
                UserChats.get_channel_group_name(self.user), context)

    def user_chat_list(self, event):
        chats = event['chats']
        data = {
            'event': 'chat_list',
            'chats': chats
        }
        text_data = json.dumps(data)
        print(text_data)
        self.send(text_data=text_data)

    def disconnect(self, close_code):
        try:
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name)
        except AttributeError:
            pass
        self.close()
class ChannelCreation(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated and self.user.is_email_verified:
            self.accept()

    def receive(self, text_data):
        data = json.loads(text_data)
        channel_name = data['channel_name']
        Channels.objects.create(channel_name, creator=self.user)
        self.send(text_data=json.dumps(
            {'description': 'channel creation was successful'}))
