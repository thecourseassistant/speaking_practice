import os
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from whispercpp import Whisper
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)  # allow cross-origin requests from your website

# Load WhisperCPP model
model = Whisper("model/tiny.en.bin")  # path to your downloaded model


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']

    # Generate unique filenames
    uid = str(uuid.uuid4())
    os.makedirs("temp", exist_ok=True)
    webm_path = f"temp/{uid}.webm"
    wav_path = f"temp/{uid}.wav"

    # Save uploaded WebM file
    audio_file.save(webm_path)

    try:
        # Convert WebM -> WAV (mono, 16kHz)
        audio = AudioSegment.from_file(webm_path, format="webm")
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio.export(wav_path, format="wav")

        # Transcribe with WhisperCPP
        result = model.transcribe(wav_path)
        text = result["text"]

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Cleanup temporary files
        if os.path.exists(webm_path):
            os.remove(webm_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

    return jsonify({"text": text})


if __name__ == "__main__":
    # Use host 0.0.0.0 for cloud deployment (Render/VPS)
    app.run(host="0.0.0.0", port=5000)
