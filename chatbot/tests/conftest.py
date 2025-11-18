import pytest
from django.contrib.auth.models import User
from chatbot.models import ChatRoom, Chat, ChatSession, UserProfile


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )


@pytest.fixture
def another_user(db):
    """Create another test user for multi-user tests."""
    return User.objects.create_user(
        username="anotheruser",
        email="another@example.com",
        password="testpass123"
    )


@pytest.fixture
def user_profile(user):
    """Create a user profile."""
    return UserProfile.objects.create(user=user)


@pytest.fixture
def chat_room(user):
    """Create a test chat room."""
    return ChatRoom.objects.create(
        name="Test Chat Room",
        user=user,
        is_hidden=False
    )


@pytest.fixture
def hidden_chat_room(user):
    """Create a hidden chat room."""
    return ChatRoom.objects.create(
        name="Hidden Chat Room",
        user=user,
        is_hidden=True
    )


@pytest.fixture
def chat_session(user, chat_room):
    """Create a test chat session."""
    session_id = f"{user.id}-{chat_room.id}"
    return ChatSession.objects.create(
        user=user,
        chat_room=chat_room,
        session_id=session_id,
        context="[]"
    )


@pytest.fixture
def chat_message(user, chat_room):
    """Create a test chat message."""
    return Chat.objects.create(
        chat_room=chat_room,
        user=user,
        message="Hello, how are you?",
        response="I'm doing well, thank you for asking!"
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return a client with an authenticated user."""
    client.force_login(user)
    return client
