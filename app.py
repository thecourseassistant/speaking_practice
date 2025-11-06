import os
import sys
import uuid
import subprocess
import shutil  # ← ADD THIS
from pathlib import Path
from flask import Flask, request, jsonify
import tempfile
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# Paths (Render clones repo to /app)
WHISPER_CPP_DIR = "/app/whisper.cpp"
MODEL_PATH = "/app/gglm.tiny.bin"

# Validate that model and binary exist


def ensure_model_ready():
    """Validate paths at runtime (not import time)."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
    if not os.path.exists(f"{WHISPER_CPP_DIR}/main"):
        raise FileNotFoundError(
            f"whisper.cpp 'main' not built at {WHISPER_CPP_DIR}/main")


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    uid = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as tmp_dir:
        webm_path = Path(tmp_dir) / "audio.webm"
        wav_path = Path(tmp_dir) / "audio.wav"
    txt_output = tmp_dir / f"{uid}.txt"  # whisper.cpp will create this

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

        # ✅ Run whisper.cpp via subprocess
        whisper_cmd = [
            f"{WHISPER_CPP_DIR}/main",
            "-m", MODEL_PATH,
            "-f", str(wav_path),
            "-otxt",
            "--output-file", str(tmp_dir / uid),  # outputs to {uid}.txt
            "-t", "4",
            "--print-colors", "0",
            "--print-progress", "0"
        ]

        print(f"🗣️ Running whisper.cpp on {wav_path}...")
        whisper_result = subprocess.run(
            whisper_cmd,
            cwd=WHISPER_CPP_DIR,
            capture_output=True,
            text=True
        )

        if whisper_result.returncode != 0:
            err = whisper_result.stderr or whisper_result.stdout
            raise Exception(f"whisper.cpp failed: {err}")

        # Read transcription
        txt_file = tmp_dir / f"{uid}.txt"
        if txt_file.exists():
            with open(txt_file, "r") as f:
                text = f.read().strip()
        else:
            text = ""

        return jsonify({"text": text})

    except Exception as e:
        print(f"🚨 Transcription error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        # Cleanup all temp files
        for path in [webm_path, wav_path, tmp_dir / f"{uid}.txt"]:
            if path.exists():
                try:
                    path.unlink()
                except Exception as cleanup_err:
                    print(f"⚠️ Cleanup warning: {cleanup_err}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
