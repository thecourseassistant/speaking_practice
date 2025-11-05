import os
import uuid
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from whispercpp import Whisper

# === Initialize Flask app ===
app = Flask(__name__)
CORS(app)

# === Load Whisper model at startup (with explicit path and error handling) ===
MODEL_DIR = Path("model/tiny.en")
MODEL_PATH = MODEL_DIR / "model.bin"

# Resolve to absolute path for clarity
ABS_MODEL_PATH = MODEL_PATH.resolve()

print(f"🔍 Attempting to load Whisper model from: {ABS_MODEL_PATH}")
print(f"📂 Model directory exists? {MODEL_DIR.exists()}")
print(f"📄 Model file exists? {MODEL_PATH.exists()}")

if not MODEL_PATH.exists():
    error_msg = (
        f"❌ Whisper model file NOT FOUND at: {ABS_MODEL_PATH}\n"
        f"Make sure the file 'model.bin' is in the 'model/tiny.en/' folder "
        f"and is committed to your Git repository."
    )
    print(error_msg)
    raise FileNotFoundError(error_msg)

try:
    print("🧠 Loading Whisper model...")
    model = Whisper(str(MODEL_PATH))
    print("✅ Whisper model loaded successfully!")
except Exception as e:
    print(f"💥 Failed to initialize Whisper model: {e}")
    raise


# === Flask route ===
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

        # Convert WebM to WAV (mono, 16kHz) using ffmpeg
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", str(webm_path),
            "-ar", "16000",
            "-ac", "1",
            "-f", "wav",
            str(wav_path),
            "-y",  # overwrite if exists
            "-loglevel", "error"
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True)
        if result.returncode != 0:
            stderr_msg = result.stderr.decode() if result.stderr else "Unknown FFmpeg error"
            raise Exception(f"FFmpeg conversion failed: {stderr_msg}")

        # Transcribe
        print(f"🗣️ Transcribing {wav_path}...")
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
                    print(f"⚠️ Failed to delete {path}: {cleanup_err}")


# === Entry point for local dev (not used in Docker/Gunicorn) ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
