from django.urls import path
from . import views

urlpatterns = [
    path("", views.chatbot, name="chatbot"),
    path("chatroom/<int:chat_room_id>/", views.chatbot, name="chat_room"),  # Handles specific chat rooms
    path('get_chat_rooms/', views.get_chat_rooms, name='get_chat_rooms'),
    path("login", views.login, name="login"),
    path("register", views.register, name="register"),
    path("logout", views.logout, name="logout"),
]
