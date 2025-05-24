from flask import Flask, jsonify, send_file, render_template, request
import logging
from flask_cors import CORS
import os
import audio_processor
import threading
import multiprocessing
import sounddevice as sd

multiprocessing.set_start_method("spawn", force=True)

app = Flask(__name__)
CORS(app)
recording_thread = None

logging.basicConfig(
    filename="server.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOP_FLAG_PATH = os.path.join(BASE_DIR, "stop_flag.txt")

selected_device_id = None

def run_detection_loop():
    try:
        audio_processor.main_loop(selected_device_id)
    except Exception as e:
        app.logger.error(f"Error in detection loop: {e}", exc_info=True)

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

@app.route('/')
def index():
    return render_template("index.html")

@app.route("/run-script", methods=["POST"])
def run_script():
    global recording_thread, selected_device_id
    if recording_thread and recording_thread.is_alive():
        return jsonify({"message": "Already running"}), 400

    data = request.get_json()
    selected_device_id = data.get("deviceId") if data else None

    recording_thread = threading.Thread(target=run_detection_loop)
    recording_thread.start()
    return jsonify({"message": "Recording started"}), 200

@app.route("/stop", methods=["POST"])
def stop_script():
    global STOP_FLAG_PATH
    with open(STOP_FLAG_PATH, "w") as f:
        f.write("stop")
    app.logger.info("Stop flag file created.")
    return jsonify({"message": "Recording stopped."}), 200

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

        if score == -1:
            return jsonify({'status': 'waiting', 'message': 'Waiting for valid audio input...'}), 200

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

    
@app.route('/is-recording', methods=['GET'])
def is_recording():
    global recording_thread
    status = bool(recording_thread and recording_thread.is_alive())
    app.logger.info(f"Recording thread status checked: {'alive' if status else 'not running'}")
    return jsonify({"is_recording": status}), 200