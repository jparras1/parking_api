#!/bin/sh
# Replace environment variables in the HTML file at runtime using envsubst
envsubst '${API_BASE_URL}' < /usr/share/nginx/html/index.html > /usr/share/nginx/html/index.html.tmp
mv /usr/share/nginx/html/index.html.tmp /usr/share/nginx/html/index.html

# Start Nginx
nginx -g "daemon off;"
