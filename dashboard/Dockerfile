FROM nginx

LABEL maintainer="jparras1@my.bcit.ca"

# Copy files to the nginx
COPY . /usr/share/nginx/html

# Tells on which port the service listens in the container
EXPOSE 80

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh

# Make the script executable
RUN chmod +x /entrypoint.sh

# Set entrypoint to run the script
ENTRYPOINT ["/entrypoint.sh"]
