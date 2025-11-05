import os
import uuid
import audioop
from flask import Flask, request, jsonify
from whispercpp import Whisper
from pydub import AudioSegment

app = Flask(__name__)
model = Whisper("model/tiny.en.bin")  # path to your downloaded model


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file found"}), 400

    audio_file = request.files['audio']

    # Create unique temp filenames
    uid = str(uuid.uuid4())
    os.makedirs("temp", exist_ok=True)
    webm_path = f"temp/{uid}.webm"
    wav_path = f"temp/{uid}.wav"

    # Save uploaded WebM
    audio_file.save(webm_path)

    # Convert WebM -> WAV (16kHz, mono)
    audio = AudioSegment.from_file(webm_path, format="webm")
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio.export(wav_path, format="wav")

    # Optional: verify audio data using audioop (just for safety)
    with open(wav_path, "rb") as f:
        data = f.read()
        # Example: get RMS of first frame
        try:
            rms = audioop.rms(data[:16000], 2)  # 2 bytes per sample
        except Exception:
            rms = 0

    # Transcribe using WhisperCPP
    result = model.transcribe(wav_path)
    text = result["text"]

    # Cleanup
    os.remove(webm_path)
    os.remove(wav_path)

    return jsonify({"text": text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
