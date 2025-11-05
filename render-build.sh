#!/bin/bash
set -e

echo "🔧 Installing system dependencies..."
apt-get update && apt-get install -y build-essential git ffmpeg libsndfile1

echo "📥 Cloning whisper.cpp..."
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp

echo "🔨 Building main binary..."
make -j$(nproc)

echo "✅ whisper.cpp built successfully!"