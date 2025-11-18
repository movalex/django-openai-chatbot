import pytest
import uuid
from django.contrib.auth.models import User
from chatbot.models import ChatRoom, Chat, ChatSession, UserProfile


@pytest.mark.unit
class TestChatRoomModel:
    """Test cases for ChatRoom model."""

    def test_create_chat_room(self, user):
        """Test creating a chat room."""
        chat_room = ChatRoom.objects.create(
            name="Test Room",
            user=user
        )
        assert chat_room.name == "Test Room"
        assert chat_room.user == user
        assert chat_room.is_hidden is False
        assert isinstance(chat_room.id, uuid.UUID)

    def test_chat_room_str(self, chat_room):
        """Test string representation of chat room."""
        assert str(chat_room) == chat_room.name

    def test_chat_room_default_visibility(self, user):
        """Test that chat rooms are visible by default."""
        chat_room = ChatRoom.objects.create(name="Visible Room", user=user)
        assert chat_room.is_hidden is False

    def test_chat_room_can_be_hidden(self, user):
        """Test that chat rooms can be hidden."""
        chat_room = ChatRoom.objects.create(
            name="Hidden Room",
            user=user,
            is_hidden=True
        )
        assert chat_room.is_hidden is True

    def test_chat_room_cascade_delete(self, user, chat_room):
        """Test that deleting user cascades to chat rooms."""
        room_id = chat_room.id
        user.delete()
        assert not ChatRoom.objects.filter(id=room_id).exists()

    def test_multiple_chat_rooms_per_user(self, user):
        """Test that a user can have multiple chat rooms."""
        room1 = ChatRoom.objects.create(name="Room 1", user=user)
        room2 = ChatRoom.objects.create(name="Room 2", user=user)

        user_rooms = ChatRoom.objects.filter(user=user)
        assert user_rooms.count() == 2
        assert room1 in user_rooms
        assert room2 in user_rooms

    def test_chat_room_ordering_by_created_at(self, user):
        """Test that chat rooms can be ordered by creation time."""
        room1 = ChatRoom.objects.create(name="First Room", user=user)
        room2 = ChatRoom.objects.create(name="Second Room", user=user)

        rooms = ChatRoom.objects.filter(user=user).order_by("-created_at")
        assert list(rooms) == [room2, room1]


@pytest.mark.unit
class TestChatModel:
    """Test cases for Chat model."""

    def test_create_chat(self, user, chat_room):
        """Test creating a chat message."""
        chat = Chat.objects.create(
            chat_room=chat_room,
            user=user,
            message="Hello",
            response="Hi there!"
        )
        assert chat.message == "Hello"
        assert chat.response == "Hi there!"
        assert chat.user == user
        assert chat.chat_room == chat_room

    def test_chat_str(self, chat_message):
        """Test string representation of chat."""
        expected = f"{chat_message.user.username}: {chat_message.message}"
        assert str(chat_message) == expected

    def test_chat_belongs_to_room(self, chat_message, chat_room):
        """Test that chat is linked to chat room."""
        assert chat_message.chat_room == chat_room
        assert chat_message in chat_room.messages.all()

    def test_chat_cascade_delete_with_room(self, chat_message, chat_room):
        """Test that deleting room cascades to chats."""
        chat_id = chat_message.id
        chat_room.delete()
        assert not Chat.objects.filter(id=chat_id).exists()

    def test_chat_cascade_delete_with_user(self, user, chat_message):
        """Test that deleting user cascades to chats."""
        chat_id = chat_message.id
        user.delete()
        assert not Chat.objects.filter(id=chat_id).exists()

    def test_multiple_chats_in_room(self, user, chat_room):
        """Test multiple chat messages in a room."""
        chat1 = Chat.objects.create(
            chat_room=chat_room,
            user=user,
            message="First message",
            response="First response"
        )
        chat2 = Chat.objects.create(
            chat_room=chat_room,
            user=user,
            message="Second message",
            response="Second response"
        )

        assert chat_room.messages.count() == 2
        assert chat1 in chat_room.messages.all()
        assert chat2 in chat_room.messages.all()


@pytest.mark.unit
class TestChatSessionModel:
    """Test cases for ChatSession model."""

    def test_create_chat_session(self, user, chat_room):
        """Test creating a chat session."""
        session_id = f"{user.id}-{chat_room.id}"
        session = ChatSession.objects.create(
            user=user,
            chat_room=chat_room,
            session_id=session_id,
            context="[]"
        )
        assert session.user == user
        assert session.chat_room == chat_room
        assert session.session_id == session_id
        assert session.context == "[]"

    def test_chat_session_str(self, chat_session):
        """Test string representation of chat session."""
        expected = f"{chat_session.user.username} - {chat_session.chat_room.name} - {chat_session.session_id}"
        assert str(chat_session) == expected

    def test_session_id_unique(self, user, chat_room):
        """Test that session_id must be unique."""
        session_id = f"{user.id}-{chat_room.id}"
        ChatSession.objects.create(
            user=user,
            chat_room=chat_room,
            session_id=session_id,
            context="[]"
        )

        with pytest.raises(Exception):  # IntegrityError
            ChatSession.objects.create(
                user=user,
                chat_room=chat_room,
                session_id=session_id,
                context="[]"
            )

    def test_chat_session_cascade_delete_with_user(self, chat_session, user):
        """Test that deleting user cascades to chat sessions."""
        session_id = chat_session.id
        user.delete()
        assert not ChatSession.objects.filter(id=session_id).exists()

    def test_chat_session_cascade_delete_with_room(self, chat_session, chat_room):
        """Test that deleting room cascades to chat sessions."""
        session_id = chat_session.id
        chat_room.delete()
        assert not ChatSession.objects.filter(id=session_id).exists()

    def test_chat_session_context_storage(self, user, chat_room):
        """Test storing context in chat session."""
        import json
        context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        session = ChatSession.objects.create(
            user=user,
            chat_room=chat_room,
            session_id=f"{user.id}-{chat_room.id}",
            context=json.dumps(context)
        )

        stored_context = json.loads(session.context)
        assert stored_context == context


@pytest.mark.unit
class TestUserProfileModel:
    """Test cases for UserProfile model."""

    def test_create_user_profile(self, user):
        """Test creating a user profile."""
        profile = UserProfile.objects.create(user=user)
        assert profile.user == user
        assert profile.last_opened_chat is None

    def test_user_profile_with_last_opened_chat(self, user, chat_room):
        """Test user profile with last opened chat."""
        profile = UserProfile.objects.create(
            user=user,
            last_opened_chat=chat_room
        )
        assert profile.last_opened_chat == chat_room

    def test_user_profile_cascade_delete(self, user_profile, user):
        """Test that deleting user cascades to profile."""
        profile_id = user_profile.id
        user.delete()
        assert not UserProfile.objects.filter(id=profile_id).exists()

    def test_user_profile_set_null_on_room_delete(self, user, chat_room):
        """Test that deleting chat room sets last_opened_chat to NULL."""
        profile = UserProfile.objects.create(
            user=user,
            last_opened_chat=chat_room
        )
        chat_room.delete()
        profile.refresh_from_db()
        assert profile.last_opened_chat is None

    def test_one_profile_per_user(self, user):
        """Test that each user can have only one profile."""
        UserProfile.objects.create(user=user)

        with pytest.raises(Exception):  # IntegrityError
            UserProfile.objects.create(user=user)

    def test_update_last_opened_chat(self, user):
        """Test updating last opened chat."""
        room1 = ChatRoom.objects.create(name="Room 1", user=user)
        room2 = ChatRoom.objects.create(name="Room 2", user=user)

        profile = UserProfile.objects.create(
            user=user,
            last_opened_chat=room1
        )
        assert profile.last_opened_chat == room1

        profile.last_opened_chat = room2
        profile.save()

        profile.refresh_from_db()
        assert profile.last_opened_chat == room2
