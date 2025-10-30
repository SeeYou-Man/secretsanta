FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Install system dependencies (if needed) and pip packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Ensure the bot token is provided via environment variable DISCORD_BOT_TOKEN
ENV PYTHONUNBUFFERED=1

# Run the package module
CMD ["python", "-m", "SecretSanta"]
