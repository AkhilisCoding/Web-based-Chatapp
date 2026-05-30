from django.db import models
from django.conf import settings


class Room(models.Model):
    """A private chat room between two users."""
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='rooms')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def get_other_user(self, current_user):
        return self.participants.exclude(id=current_user.id).first()

    def get_last_message(self):
        return self.messages.order_by('-timestamp').first()

    def __str__(self):
        return f"Room {self.id}"


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    file = models.TextField(null=True, blank=True)  # stores full Cloudinary URL
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"
