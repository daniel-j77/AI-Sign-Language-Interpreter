from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

from text_to_sign.mapper import text_to_sign_mapper
from speech.speech_to_text import speech_to_text
from speech.text_to_speech import text_to_speech

app = Flask(__name__)
CORS(app)

# -------------------------------------------------
# HOME
# -------------------------------------------------
@app.route("/")
def home():
    return "AI Sign Language Interpreter Backend Running"

# -------------------------------------------------
# SERVE SIGN GIFS (IMPORTANT)
# -------------------------------------------------
@app.route("/signs/<path:filename>")
def serve_signs(filename):
    # ../signs because backend/ is one level inside project
    return send_from_directory("../signs", filename)

# -------------------------------------------------
# TEXT → SIGN
# -------------------------------------------------
@app.route("/text-to-sign", methods=["POST"])
def text_to_sign():
    data = request.json
    text = data.get("text", "")
    signs = text_to_sign_mapper(text)
    return jsonify({"signs": signs})

# -------------------------------------------------
# VOICE → TEXT
# -------------------------------------------------
@app.route("/speech-to-text", methods=["GET"])
def voice_to_text():
    text = speech_to_text()
    return jsonify({"text": text})

# -------------------------------------------------
# TEXT → VOICE
# -------------------------------------------------
@app.route("/text-to-speech", methods=["POST"])
def text_to_voice():
    data = request.json
    text = data.get("text", "")
    text_to_speech(text)
    return jsonify({"status": "spoken"})

# -------------------------------------------------
# RUN SERVER
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, threaded=True)
