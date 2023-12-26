#!/bin/bash
#
# activate virtualenv
source $HOME/git/django-openai-chatbot/venv/bin/activate
# get the API keys
source ~/.zshrc

# Start Gunicorn
exec gunicorn -c ./gunicorn.conf.py django_chatbot.wsgi:application --bind 0.0.0.0:8000 --workers 3

