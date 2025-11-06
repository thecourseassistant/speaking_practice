import os
import uuid
import subprocess
import shutil
from pathlib import Path
from flask import Flask, request, jsonify
import tempfile
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ✅ Use the CORRECT path to whisper-cli
WHISPER_CLI = "/app/whisper.cpp/build/bin/whisper-cli"
MODEL_PATH = "/app/gglm.tiny.bin"


def ensure_model_ready():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
    if not os.path.exists(WHISPER_CLI):
        raise FileNotFoundError(f"whisper-cli not found at {WHISPER_CLI}")


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    uid = str(uuid.uuid4())

    # ✅ ENTIRE logic inside the with block
    with tempfile.TemporaryDirectory() as tmp_dir:
        webm_path = Path(tmp_dir) / "audio.webm"
        wav_path = Path(tmp_dir) / "audio.wav"
        output_base = Path(tmp_dir) / uid  # e.g., /tmp/xyz123

        try:
            audio_file.save(webm_path)

            # Convert to WAV
            ffmpeg_cmd = [
                "ffmpeg", "-i", str(webm_path),
                "-ar", "16000", "-ac", "1", "-f", "wav", str(wav_path),
                "-y", "-loglevel", "error"
            ]
            result = subprocess.run(ffmpeg_cmd, capture_output=True)
            if result.returncode != 0:
                stderr_msg = result.stderr.decode().strip(
                ) if result.stderr else "Unknown FFmpeg error"
                raise Exception(f"FFmpeg failed: {stderr_msg}")

            # ✅ Use WHISPER_CLI, not "main"
            whisper_cmd = [
                WHISPER_CLI,
                "-m", MODEL_PATH,
                "-f", str(wav_path),
                "-otxt",
                "--output-file", str(output_base),
                "-t", "2"
            ]

            print(f"🗣️ Running whisper-cli on {wav_path}...")
            whisper_result = subprocess.run(
                whisper_cmd,
                # cwd not strictly needed
                capture_output=True,
                text=True
            )

            if whisper_result.returncode != 0:
                err = whisper_result.stderr or whisper_result.stdout
                raise Exception(f"whisper-cli failed: {err}")

            # Read result
            txt_file = output_base.with_suffix(".txt")
            text = txt_file.read_text().strip() if txt_file.exists() else ""

            return jsonify({"text": text})

        except Exception as e:
            print(f"🚨 Transcription error: {e}")
            return jsonify({"error": str(e)}), 500

        # ❌ NO finally block needed — TemporaryDirectory auto-cleans up!


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
