import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from chatbot.models import ChatRoom, Chat, ChatSession, UserProfile


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class ChatRoomFactory(DjangoModelFactory):
    """Factory for creating ChatRoom instances."""

    class Meta:
        model = ChatRoom

    name = factory.Sequence(lambda n: f"Chat Room {n}")
    user = factory.SubFactory(UserFactory)
    is_hidden = False


class ChatFactory(DjangoModelFactory):
    """Factory for creating Chat instances."""

    class Meta:
        model = Chat

    chat_room = factory.SubFactory(ChatRoomFactory)
    user = factory.LazyAttribute(lambda obj: obj.chat_room.user)
    message = factory.Faker("sentence")
    response = factory.Faker("paragraph")


class ChatSessionFactory(DjangoModelFactory):
    """Factory for creating ChatSession instances."""

    class Meta:
        model = ChatSession

    user = factory.SubFactory(UserFactory)
    chat_room = factory.SubFactory(ChatRoomFactory, user=factory.SelfAttribute("..user"))
    session_id = factory.LazyAttribute(lambda obj: f"{obj.user.id}-{obj.chat_room.id}")
    context = "[]"


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating UserProfile instances."""

    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    last_opened_chat = None
