FROM python:3.10-slim

# Install system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model using whispercpp (this avoids runtime download)
RUN python -c "from whispercpp import Whisper; Whisper.from_pretrained('tiny.en')"

# Copy app
COPY . .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]