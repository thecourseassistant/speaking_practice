import os
import uuid
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
from whispercpp import Whisper

app = Flask(__name__)
CORS(app)

# Load Whisper model
model = Whisper("model/tiny.en.bin")


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    uid = str(uuid.uuid4())
    os.makedirs("temp", exist_ok=True)
    webm_path = f"temp/{uid}.webm"
    wav_path = f"temp/{uid}.wav"

    try:
        # Save uploaded WebM
        audio_file.save(webm_path)

        # Convert WebM to WAV (mono, 16kHz) using ffmpeg
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", webm_path,
            "-ar", "16000",
            "-ac", "1",
            "-f", "wav",
            wav_path,
            "-y",  # overwrite if exists
            "-loglevel", "error"
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr.decode()}")

        # Transcribe
        result = model.transcribe(wav_path)
        text = result["text"]

        return jsonify({"text": text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Cleanup
        for path in [webm_path, wav_path]:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
