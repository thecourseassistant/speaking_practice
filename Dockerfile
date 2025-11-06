# Dockerfile

# Use a slim Python base image
FROM python:3.11-slim

# Install system dependencies (including cmake and ffmpeg)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Clone and build whisper.cpp
WORKDIR /app
RUN git clone https://github.com/ggerganov/whisper.cpp
WORKDIR /app/whisper.cpp
RUN make -j$(nproc)

# ⬇️ THIS IS WHERE YOUR SNIPPET GOES ⬇️
# No chmod needed — whisper-cli is already executable

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code and model
COPY . .

# Verify files exist (optional but helpful for debugging)
RUN ls -lh /app/gglm.tiny.bin
RUN ls -l /app/whisper.cpp/build/bin/

# Expose port (optional; Render ignores this but good practice)
EXPOSE 8000

# Start the app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120", "app:app"]