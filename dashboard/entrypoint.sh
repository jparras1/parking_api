#!/bin/sh

echo "Starting the substitution process..."

# Replace the placeholder in index.html with the value of API_BASE_URL environment variable
envsubst '${API_BASE_URL}' < /usr/share/nginx/html/index.html > /usr/share/nginx/html/index.html.tmp
mv /usr/share/nginx/html/index.html.tmp /usr/share/nginx/html/index.html

echo "Substitution complete. Starting Nginx..."

# Start Nginx
nginx -g "daemon off;"
