from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message}"


class ChatSession(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    context = models.TextField()

    def __str__(self):
        return self.session_id
