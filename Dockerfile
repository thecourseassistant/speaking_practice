# ===== Build Stage =====
FROM python:3.10-slim AS builder

# Install build dependencies for whispercpp (C++ compilation)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (build whispercpp from source for compatibility)
COPY requirements.txt .
RUN pip install --user --no-cache-dir --no-binary=whispercpp -r requirements.txt


# ===== Final Stage =====
FROM python:3.10-slim

# Install runtime deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy Python deps
COPY --from=builder --chown=app:app /root/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

# Download official Whisper tiny.en model → save as model/tiny.en/model.bin
RUN mkdir -p model/tiny.en && \
    curl -L -o model/tiny.en/model.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin

# Copy app code (in case you have other files)
COPY --chown=app:app . .

EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]