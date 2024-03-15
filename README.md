# Django-OpenAI-Chatbot

This project is a Django-based application that integrates with OpenAI to provide a chatbot service. It uses Gunicorn as the WSGI HTTP Server to serve the Django application with NGINX as a reverse proxy for handling static files. 
To enable HTTPS support, add SSL configuration to your NGINX settings. This involves obtaining SSL certificates and adding `ssl_certificate` and `ssl_certificate_key` directives to your NGINX server block. For detailed instructions, refer to the NGINX documentation on SSL/TLS configuration.

The repository has basic Dockerfile for your Django application and a basic NGINX configuration in the ./nginx directory. You might need to adjust paths and settings according to your project's specific setup.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Docker and Docker Compose are installed on your machine.
- You have a basic understanding of Docker container management.

## Installation

To install Django-OpenAI-Chatbot, follow these steps:

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/yourgithubusername/django-openai-chatbot.git
   cd django-openai-chatbot
   ```

2. Build and start your containers with Docker Compose:

   ```bash
   docker-compose up --build
   ```

## Usage

After installation, you can access the Django-OpenAI-Chatbot by navigating to `http://localhost:8000` in your web browser.

## Configuration

The primary configuration is done through the `docker-compose.yml` file. You can adjust service settings, such as ports and volume mounts, as needed.

## Development

For development purposes, you can override the command in the docker-compose.yml file to use Django's development server:

```
services:
  django_app:
    command: python manage.py runserver 0.0.0.0:8000
```
Then, start your containers with Docker Compose:

```
docker-compose up
```

## Contributing to Django-OpenAI-Chatbot

To contribute to Django-OpenAI-Chatbot, follow these steps:

1. Fork this repository.
2. Create a new branch: `git checkout -b branch_name`.
3. Make your changes and commit them: `git commit -m 'commit_message'`
4. Push to the original branch: `git push origin django-openai-chatbot/<location>`
5. Create the pull request.

Alternatively, see the GitHub documentation on [creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

## License

This project uses the following license: [MIT License - Open Source Initiative](https://opensource.org/licenses/MIT)