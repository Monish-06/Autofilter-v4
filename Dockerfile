FROM python:3.10-slim-buster

# System packages and Python dependencies
RUN apt update && apt upgrade -y && apt install -y git

# Copy and install Python requirements
COPY requirements.txt /requirements.txt
RUN pip3 install -U pip && pip3 install -U -r /requirements.txt

# Setup working directory
RUN mkdir /Eva
WORKDIR /Eva

# Copy project files
COPY . .

# Make start.sh executable
RUN chmod +x /start.sh

# Start the bot
CMD ["/bin/bash", "/start.sh"]
