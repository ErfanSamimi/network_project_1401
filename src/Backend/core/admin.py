from django.contrib import admin
from .models import ChatRoom, ChatRoom_Member, User, GroupChat, Channels, Message
# Register your models here.

class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'chat_room_type', 'chat_room_id', 'create_date']

class GroupChatAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'chat_room_type', 'chat_room_id', 'create_date', 'title']

class ChatRoomMemberAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'member', 'role']

class MessageAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'type', 'sender', 'send_date']

admin.site.register(ChatRoom, ChatRoomAdmin)
admin.site.register(ChatRoom_Member, ChatRoomMemberAdmin)
admin.site.register(User)
admin.site.register(GroupChat, GroupChatAdmin)
admin.site.register(Channels, GroupChatAdmin)
admin.site.register(Message, MessageAdmin)

