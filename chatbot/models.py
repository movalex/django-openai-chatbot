import uuid
from django.db import models
from django.contrib.auth.models import User


class ChatRoom(models.Model):
    name = models.CharField(max_length=255)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    # participants = models.ManyToManyField(User)  # if multiple human participants expected per chat room

    def __str__(self):
        return self.name


# Create your models here.
class Chat(models.Model):
    chat_room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message}"


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='chat_sessions', null=True)
    session_id = models.CharField(max_length=255, unique=True)
    context = models.TextField()

    def __str__(self):
        return f"{self.user.username} - {self.chat_room.name} - {self.session_id}"
