from django.contrib import admin
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_participants')
    search_fields = ('name', 'participants__username')

    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'chatroom', 'content', 'timestamp')
    list_filter = ('chatroom', 'sender', 'timestamp')
    search_fields = ('content', 'sender__username', 'chatroom__name')
