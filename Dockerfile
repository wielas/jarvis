# Base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# portaudio19-dev: Required for sounddevice
# gcc: Required for compiling some python packages
# ffmpeg: Required for audio processing
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Command to run the application
CMD ["python", "main.py"]
