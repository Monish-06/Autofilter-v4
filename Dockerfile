FROM python:3.10-slim-buster

RUN apt update && apt upgrade -y
RUN apt install git -y

# Copy requirements file and install Python deps
COPY requirements.txt /app/requirements.txt
RUN pip3 install -U pip && pip3 install -U -r /app/requirements.txt

# Set up working directory
WORKDIR /app

# Copy all files into the image
COPY . .

# Make start.sh executable
RUN chmod +x start.sh

# Run the startup script
CMD ["/bin/bash", "start.sh"]
