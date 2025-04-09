from django.contrib import admin
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_participants')
    search_fields = ('name', 'participants__name')

    def get_participants(self, obj):
        return ", ".join([user.name or f"User {user.id}" for user in obj.participants.all()])
    get_participants.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('get_sender_name', 'chatroom', 'content', 'timestamp')
    list_filter = ('chatroom', 'sender', 'timestamp')
    search_fields = ('content', 'sender__name', 'chatroom__name')

    def get_sender_name(self, obj):
        return obj.sender.name or f"User {obj.sender.id}"
    get_sender_name.short_description = 'Sender'
