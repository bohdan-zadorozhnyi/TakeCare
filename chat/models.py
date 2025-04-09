from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class ChatRoom(models.Model):
    name = models.CharField(max_length=255)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chatrooms')

    def clean(self):
        # Skip validation when the instance is new
        if self.pk:
            if self.participants.count() > 2:
                raise ValidationError("ChatRoom can only have two participants")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    def get_participant_name(self, user):
        return user.name if user.name else f"User {user.id}"

    def __str__(self):
        return self.name

class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.name}: {self.content[:20]}"
