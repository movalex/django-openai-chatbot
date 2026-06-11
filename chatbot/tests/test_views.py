import json
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.urls import reverse
from django.utils import timezone

from chatbot import views
from chatbot.models import Chat, ChatRoom, ChatSession, UserProfile


@pytest.mark.django_db
class TestLoginView:
    """Test cases for login view."""

    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get(reverse("login"))
        assert response.status_code == 200
        assert "login.html" in [t.name for t in response.templates]

    def test_successful_login(self, client, user, chat_room):
        """Test successful login redirects to chat room."""
        response = client.post(
            reverse("login"), {"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 302
        assert "chatroom" in response.url

    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials shows error."""
        response = client.post(reverse("login"), {"username": "invalid", "password": "wrong"})
        assert response.status_code == 200
        assert b"Invalid username or password" in response.content

    def test_login_redirects_to_last_opened_chat(self, client, user):
        """Test login redirects to last opened chat if it exists."""
        room = ChatRoom.objects.create(name="Last Room", user=user)
        UserProfile.objects.create(user=user, last_opened_chat=room)

        response = client.post(
            reverse("login"), {"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 302
        assert str(room.id) in response.url

    def test_login_creates_default_room_if_none_exist(self, client, user):
        """Test login creates default room if user has no rooms."""
        response = client.post(
            reverse("login"), {"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 302
        assert ChatRoom.objects.filter(user=user).exists()

    def test_login_remember_me_sets_session_expiry(self, client, user):
        """Test remember me checkbox sets longer session expiry."""
        client.post(
            reverse("login"),
            {"username": "testuser", "password": "testpass123", "remember-me": "on"},
        )
        assert client.session.get_expiry_age() == 1209600  # 2 weeks


@pytest.mark.django_db
class TestLogoutView:
    """Test cases for logout view."""

    def test_logout_redirects_to_login(self, authenticated_client):
        """Test logout redirects to login page."""
        response = authenticated_client.get(reverse("logout"))
        assert response.status_code == 302
        assert response.url == reverse("login")

    def test_logout_clears_session(self, authenticated_client):
        """Test logout clears user session."""
        authenticated_client.get(reverse("logout"))
        response = authenticated_client.get(reverse("chatbot"))
        assert response.status_code == 302
        assert "login" in response.url


@pytest.mark.django_db
class TestChatbotView:
    """Test cases for main chatbot view."""

    def test_chatbot_requires_authentication(self, client):
        """Test that chatbot view requires login."""
        response = client.get(reverse("chatbot"))
        assert response.status_code == 302
        assert "login" in response.url

    def test_chatbot_get_request(self, authenticated_client, chat_room):
        """Test GET request to chatbot view."""
        response = authenticated_client.get(reverse("chat_room", args=[chat_room.id]))
        assert response.status_code == 200
        assert "chatbot.html" in [t.name for t in response.templates]
        assert "gpt_models" in response.context
        assert "default_model" in response.context

    def test_chatbot_invalid_room_returns_404(self, authenticated_client):
        """Test accessing non-existent chat room returns 404."""
        import uuid

        fake_id = uuid.uuid4()
        response = authenticated_client.get(reverse("chat_room", args=[fake_id]))
        assert response.status_code == 404

    def test_chatbot_cannot_access_other_user_room(self, authenticated_client, another_user):
        """Test user cannot access another user's chat room."""
        other_room = ChatRoom.objects.create(name="Other Room", user=another_user)
        response = authenticated_client.get(reverse("chat_room", args=[other_room.id]))
        assert response.status_code == 404

    def test_chatbot_updates_last_opened_chat(self, authenticated_client, user, chat_room):
        """Test that opening a chat room updates user profile."""
        profile, _ = UserProfile.objects.get_or_create(user=user)
        authenticated_client.get(reverse("chat_room", args=[chat_room.id]))

        profile.refresh_from_db()
        assert profile.last_opened_chat == chat_room

    def test_chatbot_displays_existing_chats(self, authenticated_client, user, chat_room):
        """Test that existing chats are displayed."""
        Chat.objects.create(
            chat_room=chat_room, user=user, message="Test message", response="Test response"
        )

        response = authenticated_client.get(reverse("chat_room", args=[chat_room.id]))
        assert response.status_code == 200
        assert len(response.context["chats"]) == 1

    @patch("chatbot.views.ask_openai")
    def test_chatbot_post_request(self, mock_openai, authenticated_client, user, chat_room):
        """Test POST request to send a message."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="AI response here"))]
        mock_openai.return_value = mock_response

        response = authenticated_client.post(
            reverse("chat_room", args=[chat_room.id]), {"message": "Hello AI", "model_id": "gpt-4o"}
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert "message" in data
        assert "response" in data
        assert data["message"] == "Hello AI"

    def test_chatbot_post_without_model_id(self, authenticated_client, chat_room):
        """Test POST request without model_id returns error."""
        response = authenticated_client.post(
            reverse("chat_room", args=[chat_room.id]), {"message": "Hello"}
        )
        assert response.status_code == 400
        data = json.loads(response.content)
        assert "error" in data

    def test_chatbot_invalid_method(self, authenticated_client, chat_room):
        """Test invalid HTTP method returns 405."""
        response = authenticated_client.put(reverse("chat_room", args=[chat_room.id]))
        assert response.status_code == 405


@pytest.mark.django_db
class TestGetChatRooms:
    """Test cases for get_chat_rooms view."""

    def test_get_chat_rooms_requires_authentication(self, client):
        """Test that endpoint requires authentication."""
        response = client.get(reverse("get_chat_rooms"))
        assert response.status_code == 401

    def test_get_chat_rooms_returns_user_rooms(self, authenticated_client, user):
        """Test that endpoint returns only user's rooms."""
        ChatRoom.objects.create(name="Room 1", user=user)
        ChatRoom.objects.create(name="Room 2", user=user)

        response = authenticated_client.get(reverse("get_chat_rooms"))
        assert response.status_code == 200

        data = json.loads(response.content)
        assert "chat_rooms" in data
        assert len(data["chat_rooms"]) == 2

    def test_get_chat_rooms_excludes_hidden(self, authenticated_client, user):
        """Test that hidden rooms are excluded."""
        ChatRoom.objects.create(name="Visible", user=user, is_hidden=False)
        ChatRoom.objects.create(name="Hidden", user=user, is_hidden=True)

        response = authenticated_client.get(reverse("get_chat_rooms"))
        data = json.loads(response.content)

        assert len(data["chat_rooms"]) == 1
        assert data["chat_rooms"][0]["name"] == "Visible"

    def test_get_chat_rooms_ordered_by_created_at(self, authenticated_client, user):
        """Test that rooms are ordered by creation date (newest first)."""
        room1 = ChatRoom.objects.create(name="First", user=user)
        room2 = ChatRoom.objects.create(name="Second", user=user)
        # auto_now_add timestamps can collide in fast test runs, making the
        # -created_at ordering nondeterministic. Force an explicit gap so the
        # assertion is stable. (A model-level Meta.ordering with a stable
        # tiebreaker is introduced in a later phase.)
        now = timezone.now()
        ChatRoom.objects.filter(pk=room1.pk).update(created_at=now - timedelta(minutes=1))
        ChatRoom.objects.filter(pk=room2.pk).update(created_at=now)

        response = authenticated_client.get(reverse("get_chat_rooms"))
        data = json.loads(response.content)

        assert data["chat_rooms"][0]["name"] == "Second"
        assert data["chat_rooms"][1]["name"] == "First"


@pytest.mark.django_db
class TestCreateChatRoom:
    """Test cases for create_chat_room_view."""

    def test_create_chat_room_requires_authentication(self, client):
        """Test that creating room requires authentication."""
        response = client.post(reverse("create_chat_room"))
        data = json.loads(response.content)
        assert data["success"] is False

    def test_create_chat_room_success(self, authenticated_client, user):
        """Test successful chat room creation."""
        response = authenticated_client.post(reverse("create_chat_room"))
        assert response.status_code == 200

        data = json.loads(response.content)
        assert data["success"] is True
        assert "room_id" in data

        room = ChatRoom.objects.get(id=data["room_id"])
        assert room.user == user
        assert room.name == "New Conversation"

    def test_create_chat_room_only_post(self, authenticated_client):
        """Test that only POST method is allowed."""
        response = authenticated_client.get(reverse("create_chat_room"))
        data = json.loads(response.content)
        assert data["success"] is False


@pytest.mark.django_db
class TestSaveChatName:
    """Test cases for save_chat_name view."""

    def test_save_chat_name_success(self, authenticated_client, chat_room):
        """Test successfully renaming a chat room."""
        response = authenticated_client.post(
            reverse("save_chat_name"),
            json.dumps({"chatId": str(chat_room.id), "newName": "Updated Name"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

        chat_room.refresh_from_db()
        assert chat_room.name == "Updated Name"

    def test_save_chat_name_not_found(self, authenticated_client):
        """Test renaming non-existent chat room."""
        import uuid

        response = authenticated_client.post(
            reverse("save_chat_name"),
            json.dumps({"chatId": str(uuid.uuid4()), "newName": "New Name"}),
            content_type="application/json",
        )

        assert response.status_code == 404
        data = json.loads(response.content)
        assert data["success"] is False


@pytest.mark.django_db
class TestArchiveChat:
    """Test cases for archive_chat view."""

    def test_archive_chat_requires_authentication(self, client, chat_room):
        """Test that archiving requires authentication."""
        response = client.post(reverse("archive_chat", args=[chat_room.id]))
        assert response.status_code == 401

    def test_archive_chat_success(self, authenticated_client, chat_room):
        """Test successfully archiving a chat room."""
        response = authenticated_client.post(reverse("archive_chat", args=[chat_room.id]))

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["success"] is True

        chat_room.refresh_from_db()
        assert chat_room.is_hidden is True

    def test_archive_chat_not_found(self, authenticated_client):
        """Test archiving non-existent chat room."""
        import uuid

        response = authenticated_client.post(reverse("archive_chat", args=[uuid.uuid4()]))
        assert response.status_code == 404

    def test_archive_chat_cannot_archive_other_user_room(self, authenticated_client, another_user):
        """Test user cannot archive another user's room."""
        other_room = ChatRoom.objects.create(name="Other Room", user=another_user)
        response = authenticated_client.post(reverse("archive_chat", args=[other_room.id]))
        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.django_db
class TestChatContext:
    """Test cases for chat context management."""

    @patch("chatbot.views.ask_openai")
    def test_chat_context_persistence(self, mock_openai, authenticated_client, user, chat_room):
        """Test that chat context is persisted across messages."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_openai.return_value = mock_response

        # Send first message
        authenticated_client.post(
            reverse("chat_room", args=[chat_room.id]),
            {"message": "First message", "model_id": "gpt-4o"},
        )

        # Check session was created
        session_id = f"{user.id}-{chat_room.id}"
        session = ChatSession.objects.get(session_id=session_id)
        context = json.loads(session.context)

        assert len(context) == 2  # User message + assistant response
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "First message"
        assert context[1]["role"] == "assistant"

    @patch("chatbot.views.ask_openai")
    def test_chat_context_includes_history(
        self, mock_openai, authenticated_client, user, chat_room
    ):
        """Test that context includes message history."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_openai.return_value = mock_response

        # Send multiple messages
        for i in range(3):
            authenticated_client.post(
                reverse("chat_room", args=[chat_room.id]),
                {"message": f"Message {i}", "model_id": "gpt-4o"},
            )

        session_id = f"{user.id}-{chat_room.id}"
        session = ChatSession.objects.get(session_id=session_id)
        context = json.loads(session.context)

        # Should have 6 entries (3 user + 3 assistant)
        assert len(context) == 6

    def test_get_chat_context_handles_invalid_json(self, user, chat_room):
        """Test that invalid JSON in context is handled gracefully."""

        session_id = f"{user.id}-{chat_room.id}"
        session = ChatSession.objects.create(
            user=user, chat_room=chat_room, session_id=session_id, context="invalid json"
        )
        context = views.get_chat_context(session)

        assert context == []
