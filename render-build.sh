#!/bin/bash
# render-build.sh

set -e  # Exit on error

echo "🔧 Installing system dependencies..."
apt-get update && apt-get install -y \
    build-essential \
    git \
    ffmpeg \
    libsndfile1

echo "📥 Cloning whisper.cpp..."
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp

echo "🔨 Building whisper.cpp..."
make

echo "✅ Build completed. whisper.cpp is ready."