from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.models import User
from django.conf import settings

import os
import openai
import json
import logging


from .templatetags.custom_filters import markdown_to_html, inline_code_formatting


from .models import Chat, ChatSession

from django.utils import timezone
from django.utils.safestring import mark_safe


openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

MAX_CONTEXT_SIZE = 2000
MAX_USED_CONTEXT = 5
TRIM_CONTEXT = True
GPT_MODELS = {"GPT4": "gpt-4-1106-preview", "GPT3.5": "gpt-3.5-turbo-1106"}


logger = logging.getLogger(__name__)


def format_output(value):
    html_content = markdown_to_html(value)
    result = inline_code_formatting(html_content)
    return mark_safe(result)


def ask_openai(message, chat_context, model):
    response = openai.chat.completions.create(
        # model="gpt-3.5-turbo-1106",
        model=model,
        messages=chat_context + [{"role": "user", "content": message}],
        max_tokens=4000,
    )
    return response


@login_required(login_url="login")
def chatbot(request):
    if request.method == "POST":
        return handle_post_request(request)
    elif request.method == "GET":
        return handle_get_request(request)
    else:
        error_message = "Only GET and POST are allowed"
        logger.error(error_message)
        return HttpResponseNotAllowed(["GET", "POST"], error_message)


def handle_post_request(request):
    user_message = request.POST.get("message")
    print(user_message)
    print(request.POST)
    selected_model = request.POST.get("model_id")
    if selected_model is None:
        return JsonResponse({"error": "Model ID not provided"}, status=400)
    session_id = str(request.user.id)
    chat_session, created = ChatSession.objects.get_or_create(session_id=session_id)
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
    save_chat_message(request.user, user_message, response)

    return JsonResponse({"message": user_message, "response": safe_formatted_reply})


def handle_get_request(request):
    chats = Chat.objects.filter(user=request.user)
    default_model = GPT_MODELS["GPT3.5"]  # This could be dynamic
    print(default_model)

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
        logger.error(f"Unknown Error: {str(e)}")
        return None, f"Unknown Error: {str(e)}"


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


def save_chat_message(user, user_message, response):
    assistant_response = response.choices[0].message.content.strip()
    chat = Chat(
        user=user,
        message=user_message,
        response=assistant_response,
        created_at=timezone.now(),
    )
    chat.save()


def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("chatbot")
        else:
            error_message = "Invalid username or password"
            return render(request, "login.html", {"error_message": error_message})
    else:
        return render(request, "login.html", {"body_class": "d-flex align-items-center py-4 bg-body-tertiary"})


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
    return render(request, "register.html", {"body_class": "d-flex align-items-center py-4 bg-body-tertiary"})


def logout(request):
    auth.logout(request)
    return redirect("login")
