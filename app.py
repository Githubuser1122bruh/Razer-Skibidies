from flask import Flask, jsonify, send_file
import subprocess
from flask import render_template
import logging
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    filename = "server.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/run-script', methods=['POST'])
def run_script():
    try:
        app.logger.info("Running audio_processor.py script")
        subprocess.run(["python3", "/Users/samhithpola/Documents/GitHub/Razer-Skibidies#/audio_processor.py"], check=True)
        app.logger.info("script executed normally")
        return jsonify({"message": "Script executed successfully"}), 200
    except Exception as e:
        app.logger.error(f"error:{e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stop-script', methods=['POST'])
def stop_script():
    try:
        app.logger.info("stopping script as user has requested")
        with open("stop_flag.txt", "w") as f:
            f.write("stop")
        return jsonify({"message": "stop script triggered"}), 200
    except Exception as e:
        app.logger.error(f"error in stop_script: {e}")
        return jsonify({"error": str(e)}), 200

@app.route('/download-audio/<filename>', methods=['GET'])
def download_audio(filename):
    recordings_dir = os.path.join(os.getcwd(), "recordings")
    file_path = os.path.join(recordings_dir, filename)

    if os.path.exists(file_path):
        response = send_file(file_path, as_attachment=True)
        try:
            os.remove(file_path)
            app.logger.info(f"File {file_path} deleted")
        except Exception as e:
            app.logger.error(f"Error deleting the file {e}")

        return response
    else:
        return jsonify({"error": "File not found"}), 404
    
    

@app.route('/get-latest-audio', methods=['GET'])
def get_latest_audio():
    recordings_dir = os.path.join(os.getcwd(), "recordings")
    latest_audio_file = os.path.join(recordings_dir, "latest_audio.txt")

    if os.path.exists(latest_audio_file):
        with open(latest_audio_file, "r") as f:
            filename = f.read().strip()
        file_path = os.path.join(recordings_dir, filename)
        if os.path.exists(file_path):
            return jsonify({"filename": filename}), 200
        else:
            return jsonify({"error": "No audio file found, please record."}), 404
    else:
        return jsonify({"error": "No audio file found, please record."}), 404
    
if __name__ == "__main__":
    app.run(host="0.0.0.0" ,port=5001 ,debug=True)