# ===== BUILD STAGE =====
FROM python:3.10-slim AS builder

# Install build tools + curl (to download model)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Download the official Whisper tiny.en model
RUN mkdir -p model/tiny.en && \
    curl -L -o model/tiny.en/model.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin

# Install Python dependencies (build whispercpp from source)
COPY requirements.txt .
RUN pip install --user --no-cache-dir --no-binary=whispercpp -r requirements.txt


# ===== FINAL STAGE =====
FROM python:3.10-slim

# Install only runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy model from builder
COPY --from=builder --chown=app:app /app/model ./model

# Copy Python dependencies
COPY --from=builder --chown=app:app /root/.local /home/app/.local

# Add user-local bin to PATH
ENV PATH=/home/app/.local/bin:$PATH

# Copy application code
COPY --chown=app:app . .

# Expose port
EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]