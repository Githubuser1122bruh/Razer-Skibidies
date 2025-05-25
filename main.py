from flask import Flask, jsonify, send_file, render_template, request
import logging
from flask_cors import CORS
import os
import audio_processor
import threading
import multiprocessing
import uuid
from flask_sock import Sock
import json

multiprocessing.set_start_method("spawn", force=True)

app = Flask(__name__)
CORS(app)
sock = Sock(app)

logging.basicConfig(
    filename="server.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOP_FLAG_PATH = os.path.join(BASE_DIR, "stop_flag.txt")

realtime_detection_process = None
realtime_detection_should_run = multiprocessing.Event()
prediction_queue = multiprocessing.Queue()

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

@app.route('/')
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_audio():
    try:
        audio = request.files.get("audio")
        if not audio:
            return jsonify({"error": "No audio file uploaded."}), 400
        filename = f"{uuid.uuid4()}.webm"
        filepath = os.path.join(audio_processor.RECORDINGS_DIR, filename)
        audio.save(filepath)
        with open(os.path.join(audio_processor.RECORDINGS_DIR, "latest_uploaded_audio.txt"), "w") as f:
            f.write(filename)
        score = audio_processor.predict_from_file(filepath)
        label = "brainrot" if score > audio_processor.THRESHOLD else "normal"
        app.logger.info(f"Uploaded audio processed: score={score:.3f}, label={label}")
        return jsonify({"score": round(score, 3), "label": label})
    except Exception as e:
        app.logger.error(f"Error in /upload: {e}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/download-audio/<filename>', methods=['GET'])
def download_audio(filename):
    recordings_dir = audio_processor.RECORDINGS_DIR
    file_path = os.path.join(recordings_dir, filename)

    if os.path.exists(file_path):
        try:
            response = send_file(file_path, as_attachment=True)
            app.logger.info(f"Downloaded file: {filename}")
            return response
        except Exception as e:
            app.logger.error(f"Error handling file: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "File not found"}), 404

@app.route('/get-latest-audio', methods=['GET'])
def get_latest_audio():
    try:
        latest_realtime_path = os.path.join(audio_processor.RECORDINGS_DIR, "latest_realtime_audio.txt")
        latest_uploaded_path = os.path.join(audio_processor.RECORDINGS_DIR, "latest_uploaded_audio.txt")

        filename = None
        if os.path.exists(latest_realtime_path):
            with open(latest_realtime_path, "r") as f:
                filename = f.read().strip()
            if os.path.exists(os.path.join(audio_processor.RECORDINGS_DIR, filename)):
                app.logger.info(f"Serving latest real-time audio: {filename}")
                return jsonify({"filename": filename})

        if os.path.exists(latest_uploaded_path):
            with open(latest_uploaded_path, "r") as f:
                filename = f.read().strip()
            if os.path.exists(os.path.join(audio_processor.RECORDINGS_DIR, filename)):
                app.logger.info(f"Serving latest uploaded audio: {filename}")
                return jsonify({"filename": filename})

        raise FileNotFoundError("No recent audio file found.")

    except Exception as e:
        app.logger.error(f"Error fetching latest audio: {e}")
        return jsonify({"error": str(e)}), 404

@sock.route('/ws/realtime-predictions')
def realtime_predictions(sock):
    global realtime_detection_process
    global realtime_detection_should_run
    global prediction_queue

    app.logger.info("WebSocket connection established for real-time predictions.")

    if realtime_detection_process and realtime_detection_process.is_alive():
        app.logger.warning("Existing real-time detection process found. Signaling it to stop.")
        realtime_detection_should_run.clear()
        realtime_detection_process.join(timeout=5)
        if realtime_detection_process.is_alive():
            app.logger.warning("Existing real-time detection process did not terminate gracefully. Terminating forcefully.")
            realtime_detection_process.terminate()
        realtime_detection_process = None
        if os.path.exists(audio_processor.STOP_FLAG_FILE):
            os.remove(audio_processor.STOP_FLAG_FILE)

    realtime_detection_should_run.set()
    if os.path.exists(audio_processor.STOP_FLAG_FILE):
        os.remove(audio_processor.STOP_FLAG_FILE)

    realtime_detection_process = multiprocessing.Process(
        target=audio_processor.main_loop_process,
        args=(prediction_queue, realtime_detection_should_run)
    )
    realtime_detection_process.start()
    app.logger.info("Real-time detection process started.")

    try:
        while True:
            if not prediction_queue.empty():
                result_str = prediction_queue.get()
                try:
                    sock.send(result_str)
                except Exception as send_e:
                    app.logger.error(f"Error sending WebSocket message: {send_e}. Closing connection.")
                    break
            threading.Event().wait(0.01)
            if not realtime_detection_process.is_alive() and realtime_detection_should_run.is_set():
                app.logger.warning("Real-time detection process terminated unexpectedly.")
                break

    except Exception as e:
        app.logger.error(f"WebSocket communication error: {e}", exc_info=True)
    finally:
        app.logger.info("WebSocket connection closed. Signaling real-time process to stop.")
        realtime_detection_should_run.clear()
        with open(audio_processor.STOP_FLAG_FILE, "w") as f:
            f.write("stop")

        realtime_detection_process.join(timeout=10)
        if realtime_detection_process.is_alive():
            app.logger.warning("Real-time detection process did not terminate gracefully. Terminating forcefully.")
            realtime_detection_process.terminate()
        realtime_detection_process = None
        if os.path.exists(audio_processor.STOP_FLAG_FILE):
            os.remove(audio_processor.STOP_FLAG_FILE)
        app.logger.info("Real-time detection process cleanup complete.")

@app.route('/is-recording', methods=['GET'])
def is_recording():
    global realtime_detection_process
    status = bool(realtime_detection_process and realtime_detection_process.is_alive())
    app.logger.info(f"Real-time detection process status checked: {'alive' if status else 'not running'}")
    return jsonify({"is_recording": status}), 200

if __name__ == "__main__":
    os.makedirs(audio_processor.RECORDINGS_DIR, exist_ok=True)
    if os.path.exists(audio_processor.STOP_FLAG_FILE):
        os.remove(audio_processor.STOP_FLAG_FILE)
    app.run(host="0.0.0.0", port=5001, debug=True)