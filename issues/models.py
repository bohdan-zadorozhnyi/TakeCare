from django.db import models
from accounts.models import User
import uuid

class Issue(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    is_resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    admin_response = models.TextField(blank=True, null=True)
    resolved_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Issue'
        verbose_name_plural = 'Issues'

    def __str__(self):
        return f"{self.title} - {self.user.name}"
        
    def save(self, *args, **kwargs):
        if self.status == 'RESOLVED' and not self.is_resolved:
            self.is_resolved = True
            from django.utils import timezone
            self.resolved_date = timezone.now()
        super().save(*args, **kwargs)