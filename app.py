from flask import Flask, jsonify, send_file, render_template
import subprocess
import logging
from flask_cors import CORS
import os
import audio_processor
import threading
import time
from app import app

app = Flask(__name__)
CORS(app)
recording_thread = None

logging.basicConfig(
    filename="server.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def run_detection_loop():
    audio_processor.main_loop()  # your long-running function

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return render_template("index.html")

@app.route("/run-script", methods=["POST"])
def run_script():
    global recording_thread
    if recording_thread and recording_thread.is_alive():
        return jsonify({"message": "Already running"}), 400

    recording_thread = threading.Thread(target=run_detection_loop)
    recording_thread.start()
    return jsonify({"message": "Recording started"}), 200


@app.route("/stop", methods=["POST"])
def stop_script():
    with open("stop_flag.txt", "w") as f:
        f.write("stop")
    return jsonify({"message": "Recording stopped"}), 200


@app.route('/download-audio/<filename>', methods=['GET'])
def download_audio(filename):
    recordings_dir = os.path.join(BASE_DIR, "recordings")
    file_path = os.path.join(recordings_dir, filename)

    if os.path.exists(file_path):
        try:
            response = send_file(file_path, as_attachment=True)
            os.remove(file_path)
            app.logger.info(f"Downloaded and deleted file: {filename}")
            return response
        except Exception as e:
            app.logger.error(f"Error handling file: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/predict', methods=['GET'])
def predict():
    try:
        score = audio_processor.detect_brainrot()
        label = "brainrot" if score > audio_processor.THRESHOLD else "normal"
        return jsonify({'score': round(score, 3), 'label': label})
    except Exception as e:
        app.logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get-latest-audio', methods=['GET'])
def get_latest_audio():
    try:
        latest_path = os.path.join(BASE_DIR, "recordings", "latest_audio.txt")
        if not os.path.exists(latest_path):
            raise FileNotFoundError("No audio file found.")

        with open(latest_path, "r") as f:
            filename = f.read().strip()

        file_path = os.path.join(BASE_DIR, "recordings", filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError("Audio file listed not found on disk.")

        return jsonify({"filename": filename})
    except Exception as e:
        app.logger.error(f"Error fetching latest audio: {e}")
        return jsonify({"error": str(e)}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
