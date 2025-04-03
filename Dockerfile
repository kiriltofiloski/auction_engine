# Use Python 3.12.3 image based on Debian Bullseye in its slim variant as the base image
FROM python:3.12.3-slim-bullseye

# Set an environment variable to unbuffer Python output, aiding in logging and debugging
ENV PYTHONUNBUFFERED=1

# Set the working directory within the container to /app for any subsequent commands
WORKDIR /django

# Copy the rquirements to our imge
COPY requirements.txt requirements.txt

# Upgrade pip to ensure we have the latest version for installing dependencies
RUN pip install --upgrade pip

# Install dependencies from the requirements.txt file to ensure our Python environment is ready
RUN pip install -r requirements.txt