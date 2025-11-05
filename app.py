import os
import sys
import uuid
import subprocess
import traceback
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from whispercpp import Whisper

print("🚀 Initializing Flask app...")

# Load Whisper model by name (auto-downloads if needed)
try:
    print("🧠 Loading Whisper model 'tiny.en' (auto-download if missing)...")
    model = Whisper.from_pretrained("tiny.en")
    print("✅ Whisper model loaded successfully!")
except Exception as e:
    print("💥 FATAL: Failed to initialize Whisper model")
    traceback.print_exc()
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)
CORS(app)


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    uid = str(uuid.uuid4())
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    webm_path = temp_dir / f"{uid}.webm"
    wav_path = temp_dir / f"{uid}.wav"

    try:
        # Save uploaded WebM
        audio_file.save(webm_path)

        # Convert WebM to WAV using ffmpeg
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", str(webm_path),
            "-ar", "16000",
            "-ac", "1",
            "-f", "wav",
            str(wav_path),
            "-y",
            "-loglevel", "error"
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True)
        if result.returncode != 0:
            stderr_msg = result.stderr.decode().strip() if result.stderr else "Unknown error"
            raise Exception(f"FFmpeg failed: {stderr_msg}")

        # Transcribe
        print(
            f"🗣️ Transcribing audio (length: {wav_path.stat().st_size} bytes)...")
        transcription = model.transcribe(str(wav_path))
        text = transcription.get("text", "").strip()

        return jsonify({"text": text})

    except Exception as e:
        print(f"🚨 Transcription error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Cleanup temporary files
        for path in [webm_path, wav_path]:
            if path.exists():
                try:
                    path.unlink()
                except Exception as cleanup_err:
                    print(f"⚠️ Cleanup warning: {cleanup_err}")


# For local development only
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
