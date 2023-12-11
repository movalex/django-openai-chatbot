from django.shortcuts import render, redirect
from django.http import JsonResponse
import os
import openai

from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat, ChatSession

from django.utils import timezone


openai_api_key = os.getenv("OPENAI_API_KEY")

openai.api_key = openai_api_key


def ask_openai(message, chat_context):
    response = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=chat_context + [{"role": "user", "content": message}],
    )
    return response


# Create your views here.
def chatbot(request):
    chats = []

    if not request.user.is_authenticated:
        return redirect(
            "login"
        )  # Redirect to the login page if the user is not authenticated

    chats = Chat.objects.filter(user=request.user)
    if request.user.is_authenticated:
        chats = Chat.objects.filter(user=request.user)

    if request.method == "POST":
        message = request.POST.get("message")
        # Retrieve or create a chat session
        session_id = str(request.user.id)  # Using user ID as session identifier
        chat_session, created = ChatSession.objects.get_or_create(session_id=session_id)

        # Get current chat context
        chat_context = eval(chat_session.context) if chat_session.context else []

        # Get response from OpenAI
        response = ask_openai(message, chat_context)
        assistant_response = response.choices[
            0
        ].message.content.strip()  # Extracting the text from the response

        # Update chat context
        chat_context.append({"role": "user", "content": message})
        chat_context.append(
            {
                "role": "assistant",
                "content": assistant_response,
            }
        )

        # Save the updated context
        chat_session.context = str(chat_context)
        chat_session.save()

        # Save the chat message and response
        chat = Chat(
            user=request.user,
            message=message,
            response=assistant_response,
            created_at=timezone.now(),
        )
        chat.save()

        return JsonResponse({"message": message, "response": assistant_response})

    chats = Chat.objects.filter(user=request.user)

    return render(request, "chatbot.html", {"chats": chats})


def login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("chatbot")
        else:
            error_message = "Invalid username or password"
            return render(request, "login.html", {"error_message": error_message})
    else:
        return render(request, "login.html")


def register(request):
    return redirect("login")

    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect("chatbot")
            except:
                error_message = "Error creating account"
                return render(
                    request, "register.html", {"error_message": error_message}
                )
        else:
            error_message = "Password dont match"
            return render(request, "register.html", {"error_message": error_message})
    return render(request, "register.html")


def logout(request):
    auth.logout(request)
    return redirect("login")
