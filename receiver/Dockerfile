FROM python:3

LABEL maintainer="jparras1@my.bcit.ca"

RUN mkdir /app
RUN useradd -m jonathan

# We copy just the requirements.txt first to leverage Docker cache
# on `pip install`
COPY ./requirements.txt /app/requirements.txt

# Set the working directory
WORKDIR /app
# Install dependencies
RUN pip3 install -r requirements.txt
# Copy the source code
COPY . /app

# Change permissions and become a non-privileged user
RUN chown -R jonathan:jonathan /app
USER jonathan

# Tells on which port the service listens in the container
EXPOSE 8080

# Entrypoint = run Python
ENTRYPOINT [ "python3" ]

# Default = run app.py
CMD [ "app.py" ]