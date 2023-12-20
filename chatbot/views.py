from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import os
import openai
import json
import logging


from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat, ChatSession

from django.utils import timezone


openai_api_key = os.getenv("OPENAI_API_KEY")

openai.api_key = openai_api_key

logger = logging.getLogger(__name__)


def ask_openai(message, chat_context):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=chat_context + [{"role": "user", "content": message}],
    )
    return response


@login_required(login_url="login")
def chatbot(request):
    chats = []
    MAX_CONTEXT_SIZE = 200
    TRIM_CONTEXT = True
    MAX_USED_CONTEXT = 200

    if request.method == "POST":
        message = request.POST.get("message")
        print(message)
        # Retrieve or create a chat session
        session_id = str(request.user.id)  # Using user ID as session identifier
        chat_session, created = ChatSession.objects.get_or_create(session_id=session_id)

        # Get current chat context
        try:
            chat_context = (
                json.loads(chat_session.context) if chat_session.context else []
            )
        except json.JSONDecodeError:
            chat_context = request.session.get("chat_context", [])
        print(len(chat_context))
        # Get response from OpenAI
        chat_used_context = chat_context[-MAX_USED_CONTEXT*2:]
        print(f"current context size: {len(chat_used_context)}")
        try:
            response = ask_openai(message, chat_used_context)

        except openai.PermissionDeniedError:
            logger.error("Permission denied to OpenAI services")
            return JsonResponse(
                {"error": "Permission denied to OpenAI services."}, status=403
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        # Extracting the text from the response
        assistant_response = response.choices[0].message.content.strip()
        print(f"response: {assistant_response}")
        # Update chat context
        chat_context.append({"role": "user", "content": message})
        chat_context.append(
            {
                "role": "assistant",
                "content": assistant_response,
            }
        )
        # Trim the context if it exceeds the maximum size
        if (
            TRIM_CONTEXT and len(chat_context) > MAX_CONTEXT_SIZE * 2
        ):  # *2 because each interaction has 2 parts
            chat_context = chat_context[-MAX_CONTEXT_SIZE * 2 :]

        # Save the updated context
        chat_session.context = json.dumps(chat_context)
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
    # return redirect("login")

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
