from django.urls import path
from . import views

urlpatterns = [
    path("", views.chatbot, name="chatbot"),
    path("chatroom/<uuid:chat_room_id>/", views.chatbot, name="chat_room"),  # Handles specific chat rooms
    path("chatroom/", views.chatbot, name="default_chat_room"),
    path("create_chat_room/", views.create_chat_room_view, name="create_chat_room"),
    path("save_chat_name/", views.save_chat_name, name="save_chat_name"),
    path('get_chat_rooms/', views.get_chat_rooms, name='get_chat_rooms'),
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path("logout", views.logout, name="logout"),
]
