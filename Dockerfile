# Use a base image with Python and build tools
FROM python:3.10-slim AS builder

# Install system dependencies needed to build whispercpp (if needed)
# whispercpp is a Python wrapper around a C++ library, so we may need gcc, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies (including whispercpp)
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# --- Final stage ---
FROM python:3.10-slim

# Install runtime dependencies: ffmpeg (for audio conversion) and ca-certificates
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user for security (optional but recommended)
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy Python dependencies from builder stage
COPY --from=builder --chown=app:app /root/.local /home/app/.local

# Add local bin to PATH
ENV PATH=/home/app/.local/bin:$PATH

# Copy your application code
COPY --chown=app:app . .

# Expose the port your app runs on
EXPOSE 5000

# Run the app using Gunicorn (recommended for production)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]