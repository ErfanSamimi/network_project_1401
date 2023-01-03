import json
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from asgiref.sync import async_to_sync
from core.models import ChatRoom, Message, User, ChatRoom_Member, Channels, GroupChat
from core.serializer import serialize_message
from chat_app.settings import TESTING
from django.db.models import Q


class ChatroomCreation(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated and self.user.is_email_verified:
            self.accept()


    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        chatroom_type = data['chatroom_type']
        if chatroom_type not in ChatRoom.CHATROOM_TYPES:
            self.send(text_data=json.dumps({"event": "error", "description": "Invalid chatroom type."}))

        elif chatroom_type == 'group':
            group_name = data['group_name']
            GroupChat.objects.create(group_name, creator=self.user)
            self.send(text_data=json.dumps(
                {'event': 'group_creation', 'description': 'group creation was successful'})
            )
            UserChats.update_chat_list(self.user)
            UserChats.update_chat_list(self.user, ['admin', 'creator'])

        elif chatroom_type == 'channel':
            channel_name = data['channel_name']
            Channels.objects.create(channel_name, creator=self.user)
            self.send(text_data=json.dumps(
                {'event': 'channel_creation', 'description': 'channel creation was successful'})
            )
            UserChats.update_chat_list(self.user)
            UserChats.update_chat_list(self.user, ['admin', 'creator'])


        elif chatroom_type == 'direct':
            member2_phone_number = data['phone_number']
            member2 = User.objects.filter(phone_number=member2_phone_number, is_email_verified=True)
            if member2.exists():
                try:
                    ChatRoom.objects.create_direct_chat(self.user, member2.first())
                    self.send(text_data=json.dumps(
                        {'event': 'direct_creation', 'description': 'Direct chat creation was successful'})
                    )
                    UserChats.update_chat_list(member2.first())
                    UserChats.update_chat_list(member2.first(), ['admin', 'creator'])
                    UserChats.update_chat_list(self.user)
                    UserChats.update_chat_list(self.user, ['admin', 'creator'])

                except ChatRoomExistsError:
                    self.send(text_data=json.dumps(
                        {'event': 'error', 'description': 'A direct chat exists for these users'})
                    )

            else:
                self.send(text_data=json.dumps(
                    {'event': 'error', 'description': 'Invalid user!'})
                )


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
    def update_chat_list(user, user_roles=None):
        ch_layer = get_channel_layer(DEFAULT_CHANNEL_LAYER)
        context = {
            'type': 'user_chat_list',
            'event': 'chat_list_all' if not user_roles else 'chat_list_slice',
            'chats': UserChats.user_chat_rooms(user, user_roles)
        }
        async_to_sync(ch_layer.group_send)(UserChats.get_channel_group_name(user), context)

    @staticmethod
    def get_channel_group_name(user):
        return f'user_chats_{user.phone_number}'

    @staticmethod
    def user_chat_rooms(user, roles=None):
        member_role = ChatRoom_Member.MEMBER_ROLES if not roles else roles
        channels = Channels.objects.filter(chatroom_member__member=user, chatroom_member__role__in=member_role).values(
            'chat_room_id',
            'title',
            'chatroom_member__role'
        )
        groups = GroupChat.objects.filter(chatroom_member__member=user, chatroom_member__role__in=member_role).values(
            'chat_room_id', 'title',
            'chatroom_member__role'
        )

        directs = ChatRoom_Member.objects.filter(
            member=user,
            role__in=member_role,
            chat_room__chat_room_type='direct'
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


    def receive(self, text_data=None, bytes_data=None):
        json_data = json.loads(text_data)
        print(json_data)
        roles = json_data.get('roles', None)

        context = {
            'type': 'user_chat_list',
            'event': 'chat_list_all' if not roles else 'chat_list_slice',
            'chats': UserChats.user_chat_rooms(self.user, roles)
        }
        async_to_sync(self.channel_layer.group_send)(UserChats.get_channel_group_name(self.user), context)


    def user_chat_list(self, event):
        chats = event['chats']
        ev = event['event']
        data = {
            'event': ev,
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

class AddMember(WebsocketConsumer):

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.chat_room = None
        self.user = self.scope['user']
        if self.user.is_authenticated and self.user.is_email_verified:
            ch_member = ChatRoom_Member.objects.filter(member=self.user, role__in=['admin','creator'])
            if ch_member.exists():
                self.accept()
                self.chat_room = ch_member.first()

    def receive(self, text_data):
        data = json.loads(text_data)
        user_email = data ['email']
        user_role = data ['role']
        user = User.objects.filter(email = user_email)
        if self.chat_room.chat_room_type == 'group':
            ChatRoom_Member.objects.add_group_member(self.chat_room, user.first(), user_role)
        elif self.chat_room.chat_room_type == 'channels':
            ChatRoom_Member.objects.add_channel_member(self.chat_room, user.first(), user_role)
        self.send(text_data = json.dumps({'event' : 'member_added'}))

class RemoveMember(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.chatroom_member = None
        self.user = self.scope['user']

        if self.user.is_authenticated and self.user.is_email_verified:
            ch_member = ChatRoom_Member.objects.filter(
                member=self.user, role__in=['admin', 'creator'], chat_room__chat_room_id=self.room_name
            )
            if ch_member.exists() and ch_member.first().chat_room.chat_room_type in ['group', 'channel']:
                self.accept()
                self.chatroom_member = ch_member.first()

    def receive(self, text_data):
        data = json.loads(text_data)
        phone_numbers = data['phone_numbers']

        try:
            phone_numbers.remove(self.chatroom_member.member.phone_number)
        except:
            pass

        if self.chatroom_member.role == 'creator':
            members = ChatRoom_Member.objects.filter(
                member__phone_number__in=phone_numbers, chat_room__chat_room_id=self.room_name
            )
        else:
            members = ChatRoom_Member.objects.filter(
                ~Q(role__in=['admin']), member__phone_number__in=phone_numbers, chat_room__chat_room_id=self.room_name
            )

        if members:
            members.delete()