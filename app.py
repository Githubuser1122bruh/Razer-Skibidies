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

@app.route('/download-audio', methods=['GET'])
def download_audio():
    audio_file = os.path.join(BASE_DIR, "recorded_audio.mp3")
    if os.path.exists(audio_file):
        return send_file(audio_file, as_attachment=True)
    else:
        return jsonify({"error": "No audio file found, please record audio first"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0" ,port=5001 ,debug=True)