from django.db import models
from accounts.models import User
import uuid

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.receiver.name}"