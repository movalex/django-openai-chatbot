import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chatbot.models import ChatRoom


class Command(BaseCommand):
    help = "Creating a default test user for debugging purposes"
    DJANGO_TEST_PASSWORD = os.getenv("DJANGO_TEST_PASSWORD")

    def handle(self, *args, **options):
        if not User.objects.filter(username="testuser").exists():
            user = User.objects.create_user(
                "alex", "testuser@example.com", DJANGO_TEST_PASSWORD
            )
            ChatRoom.objects.create(name="Alex's Default Chat", user=user)
        else:
            self.stdout.write(self.style.NOTICE("Test user already exists"))
