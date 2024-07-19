from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

import json
import logging
import openai
import os
import uuid

from .templatetags.custom_filters import markdown_to_html, inline_code_formatting

from .models import Chat, ChatSession, ChatRoom, UserProfile

openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

MAX_CONTEXT_SIZE = 2000
MAX_USED_CONTEXT = 8
TRIM_CONTEXT = True
GPT_MODELS = {
    "GPT4o": "gpt-4o",
    "GPT4o Mini": "gpt-4o-mini",
    "GPT4 Turbo": "gpt-4-turbo-preview",
}


logger = logging.getLogger(__name__)


def format_output(value):
    html_content = markdown_to_html(value)
    result = inline_code_formatting(html_content)
    return mark_safe(result)


def ask_openai(message, chat_context, model):
    response = openai.chat.completions.create(
        model=model,
        messages=chat_context + [{"role": "user", "content": message}],
        max_tokens=4000,
    )
    return response


def get_chat_rooms(request):
    # Ensure the user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    # Get chat rooms associated with the user
    chat_rooms = (
        ChatRoom.objects.filter(user=request.user, is_hidden=False)
        .order_by("-created_at")
        .values("id", "name")
    )
    # Return the chat rooms as JSON
    return JsonResponse({"chat_rooms": list(chat_rooms)})


@login_required(login_url="login")
def chatbot(request, chat_room_id=None):
    # Retrieve user profile to update last opened chatroom
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if chat_room_id:
        try:
            chat_room = ChatRoom.objects.get(id=chat_room_id, user=request.user.id)
            # Update last opened chatroom in user profile
            user_profile.last_opened_chat = chat_room
            user_profile.save()
        except ChatRoom.DoesNotExist:
            return HttpResponse("Chat room not found or access denied", status=404)
    else:
        # Default chat room logic
        # Redirect to last opened chatroom if it exists
        if user_profile.last_opened_chat:
            return redirect("chat_room", chat_room_id=user_profile.last_opened_chat.id)
        else:
            # If no last opened chatroom, find or create a default chat room
            chat_room = ChatRoom.objects.filter(user=request.user).first()
            if chat_room:
                # Update last opened chatroom in user profile
                user_profile.last_opened_chat = chat_room
                user_profile.save()
                return redirect("chat_room", chat_room_id=chat_room.id)
            # TODO: Handle the case where no chatrooms exist for the user

    if request.method == "POST":
        return handle_post_request(request, chat_room=chat_room)
    elif request.method == "GET":
        return handle_get_request(request, chat_room=chat_room)
    else:
        error_message = "Only GET and POST are allowed"
        logger.error(error_message)
        return HttpResponseNotAllowed(["GET", "POST"], error_message)


def handle_post_request(request, chat_room):
    user_message = request.POST.get("message")

    logger.debug(request.POST)

    selected_model = request.POST.get("model_id")
    if selected_model is None:
        return JsonResponse({"error": "Model ID not provided"}, status=400)

    session_id = f"{request.user.id}-{chat_room.id}"  # Unique for each user-room pair
    chat_session, created = ChatSession.objects.get_or_create(
        session_id=session_id, chat_room=chat_room, user=request.user
    )
    chat_context = get_chat_context(chat_session, request)

    response, error_msg = get_openai_response(
        user_message, chat_context, selected_model
    )
    if response is None and error_msg:
        return JsonResponse({"error": error_msg}, status=403)

    chat_context, safe_formatted_reply = update_chat_context(
        chat_context, user_message, response
    )

    trim_chat_context_if_needed(chat_context)

    save_chat_session(chat_session, chat_context)
    save_chat_message(request.user, user_message, response, chat_room)

    return JsonResponse({"message": user_message, "response": safe_formatted_reply})


def handle_get_request(request, chat_room):
    chats = Chat.objects.filter(user=request.user, chat_room=chat_room)
    default_model = GPT_MODELS["GPT4o"]  # This should be driven by chatroom settings
    return render(
        request,
        "chatbot.html",
        {"chats": chats, "gpt_models": GPT_MODELS, "default_model": default_model},
    )


def get_chat_context(chat_session, request):
    try:
        return json.loads(chat_session.context) if chat_session.context else []
    except json.JSONDecodeError:
        return request.session.get("chat_context", [])


def get_openai_response(user_message, chat_context, selected_model):
    chat_used_context = chat_context[-MAX_USED_CONTEXT * 2 :]
    try:
        response = ask_openai(user_message, chat_used_context, selected_model)
        return response, None
    except openai.PermissionDeniedError:
        error_message = "Permission denied to OpenAI services"
        logger.error(error_message)
        return None, error_message
    except Exception as e:
        err = f"Unknown Error: {str(e)}"
        logger.error(err)
        return None, err


def update_chat_context(chat_context, user_message, response):
    assistant_response = response.choices[0].message.content.strip()
    safe_formatted_reply = format_output(assistant_response)

    chat_context.append({"role": "user", "content": user_message})
    chat_context.append({"role": "assistant", "content": assistant_response})
    return chat_context, safe_formatted_reply


def trim_chat_context_if_needed(chat_context):
    if TRIM_CONTEXT and len(chat_context) > MAX_CONTEXT_SIZE * 2:
        chat_context = chat_context[-MAX_CONTEXT_SIZE * 2 :]


def save_chat_session(chat_session, chat_context):
    chat_session.context = json.dumps(chat_context)
    chat_session.save()


def save_chat_message(user, user_message, response, chat_room):
    assistant_response = response.choices[0].message.content.strip()
    chat = Chat(
        user=user,
        message=user_message,
        chat_room=chat_room,  # Associate the message with the chat_room
        response=assistant_response,
        created_at=timezone.now(),
    )
    chat.save()


def create_chat_room(user, room_name=None):
    # If no room name is specified, use a default name based on the user's username
    room_name = room_name or "New Conversation"
    return ChatRoom.objects.create(name=room_name, user=user)


def create_chat_room_view(request):
    if request.method == "POST" and request.user.is_authenticated:
        chat_room = create_chat_room(request.user)
        return JsonResponse({"success": True, "room_id": chat_room.id})
    return JsonResponse({"success": False})


@require_POST
def save_chat_name(request):
    data = json.loads(request.body)
    print(data)
    chat_id = data.get("chatId")
    new_name = data.get("newName")
    print(new_name)
    try:
        chat_room = ChatRoom.objects.get(id=chat_id)
        chat_room.name = new_name
        chat_room.save()
        return JsonResponse({"success": True})
    except ChatRoom.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Chat room not found"}, status=404
        )


@require_POST
def archive_chat(request, chat_room_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    try:
        chat_room = ChatRoom.objects.get(id=chat_room_id, user=request.user)
        chat_room.is_hidden = True
        chat_room.save()
        return JsonResponse({"success": True})
    except ChatRoom.DoesNotExist:
        return JsonResponse({"error": "Chat room not found"}, status=404)


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember_me = request.POST.get(
            "remember-me"
        )  # Access the Remember Me checkbox value
        user = auth.authenticate(request, username=username, password=password)
        error_message = None
        if user is not None:
            auth.login(request, user)
            if remember_me:
                request.session.set_expiry(1209600)  # Sessions expire after 2 weeks
            else:
                request.session.set_expiry(0)  # Session expires at browser close
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            last_opened_chat = user_profile.last_opened_chat
            if last_opened_chat:
                return redirect("chat_room", chat_room_id=last_opened_chat.id)

            chat_rooms = ChatRoom.objects.filter(user=request.user)
            if chat_rooms.exists():
                first_room = chat_rooms.first()
                return redirect("chat_room", chat_room_id=first_room.id)

            default_room = create_chat_room(user)
            if not default_room:
                logger.error("Unable to create deafult chat room")
                return redirect("login")
            return redirect("chat_room", chat_room_id=default_room.id)
        else:
            error_message = "Invalid username or password"
            return render(request, "login.html", {"error_message": error_message})
    else:
        return render(request, "login.html")


def register(request):
    if not settings.DEBUG:
        logger.warn("Registration is temporary disabled")
        return render(request, "registration_disabled.html")

    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()

                # Create a default chat room for the new user
                default_room_name = f"{username}'s Default Chat"
                default_room = create_chat_room(user)
                default_room.save()

                auth.login(request, user)
                return redirect("chat_room", chat_room_id=default_room.id)
            except:
                error_message = "Error creating account"
                return render(
                    request, "register.html", {"error_message": error_message}
                )
        else:
            error_message = "Password dont match"
            logger.error(error_message)
            return render(request, "register.html", {"error_message": error_message})
    return render(request, "register.html")


def logout(request):
    auth.logout(request)
    return redirect("login")
