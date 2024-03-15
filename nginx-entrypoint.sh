#!/bin/sh

# Directory where to save the self-signed certificate and key
SSL_DIR=/etc/ssl/djangoapp
mkdir -p ${SSL_DIR}

# Check if the SSL certificate and key files exist
if [ ! -f "${SSL_DIR}/selfsigned.crt" ] || [ ! -f "${SSL_DIR}/selfsigned.key" ]; then
    echo "Generating self-signed SSL certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ${SSL_DIR}/selfsigned.key \
        -out ${SSL_DIR}/selfsigned.crt \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
fi

# Start NGINX in the foreground
exec nginx -g 'daemon off;'