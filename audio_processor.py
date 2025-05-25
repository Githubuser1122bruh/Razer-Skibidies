import os
import uuid
import wave
import numpy as np
import sounddevice as sd
import librosa
from pydub import AudioSegment
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import tensorflow as tf
import json
import time

tf.config.threading.set_intra_op_parallelism_threads(1)
tf.config.threading.set_inter_op_parallelism_threads(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOP_FLAG_FILE = os.path.join(BASE_DIR, "stop_flag.txt")

SAMPLE_RATE = 22050
DURATION = 3
N_MFCC = 13
MAX_TIMESTEPS = 130
INPUT_FEATURES = 39
THRESHOLD = 0.95
RECORDINGS_DIR = os.path.join(os.getcwd(), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

try:
    if os.path.exists("brainrot_lstm_model.h5"):
        model = load_model("brainrot_lstm_model.h5")
    elif os.path.exists("best_model.h5"):
        model = load_model("best_model.h5")
    else:
        model = load_model("brainrot_detector_advanced.h5")
    print("TensorFlow model loaded successfully.")
except Exception as e:
    print(f"Error loading TensorFlow model: {e}")
    model = None 

try:
    scaler_mean = np.load("scaler_mean.npy")
    scaler_scale = np.load("scaler_scale.npy")
    print("Scaler parameters loaded successfully.")
except Exception as e:
    print(f"Error loading scaler parameters: {e}")
    scaler_mean = None
    scaler_scale = None

devices = sd.query_devices()
input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
if not input_devices:
    print("No audio input devices found. Please check your microphone setup.")
    sd.default.device = None
else:
    print("Available input devices:")
    for i in input_devices:
        print(f"{i}: {devices[i]['name']}")

    if len(input_devices) > 1:
        sd.default.device = (input_devices[1], None)
    elif len(input_devices) == 1:
        sd.default.device = (input_devices[0], None)
    else:
        sd.default.device = None

    if sd.default.device and sd.default.device[0] is not None:
        print(f"Using input device: {sd.default.device[0]} – {devices[sd.default.device[0]]['name']}")
    else:
        print("Could not select a default input device. Please specify manually if needed.")

def scale_features(features):
    if scaler_mean is None or scaler_scale is None:
        print("Scaler not loaded. Cannot scale features.")
        return features 
    flat = features.reshape(-1, INPUT_FEATURES)
    scaled = (flat - scaler_mean) / (scaler_scale + 1e-10) 
    return scaled.reshape(1, MAX_TIMESTEPS, INPUT_FEATURES).astype(np.float32)

def extract_features(audio):
    if not np.all(np.isfinite(audio)) or np.max(np.abs(audio)) < 0.001: 
        return None

    try:
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        mfcc = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
        delta = librosa.feature.delta(mfcc)
        delta2 = librosa.feature.delta(mfcc, order=2)
        full = np.vstack([mfcc, delta, delta2]).T

        if np.isnan(full).any() or np.isinf(full).any():
            print("MFCC contains NaN or Inf values after extraction.")
            return None

        if full.shape[0] > MAX_TIMESTEPS:
            full = full[:MAX_TIMESTEPS, :]
        padded = pad_sequences([full], maxlen=MAX_TIMESTEPS, dtype='float32', padding='post')[0]
        padded = padded.reshape(1, MAX_TIMESTEPS, INPUT_FEATURES)

        if padded.shape[1] != MAX_TIMESTEPS or padded.shape[2] != INPUT_FEATURES:
            print(f"Padded features have incorrect shape: {padded.shape}")
            return None

        return scale_features(padded)

    except Exception as e:
        print(f"Feature extraction error: {e}")
        return None

def predict_brainrot(features):
    if features is None or model is None:
        return 0.0
    try:
        prediction = model.predict(features, verbose=0)
        return float(prediction[0][0])
    except Exception as e:
        print(f"Prediction error: {e}")
        return 0.0

def record_audio_chunk():
    if sd.default.device is None or sd.default.device[0] is None:
        print("No input device selected for recording. Skipping chunk.")
        return np.array([])
    try:
        audio = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
        sd.wait()
        return audio.flatten()
    except Exception as e:
        print(f"Error during audio recording: {e}")
        return np.array([])

def save_audio(audio, path):
    if audio.size == 0:
        print(f"No audio to save to {path}")
        return
    int_audio = (audio * 32767).astype(np.int16)
    try:
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(int_audio.tobytes())
    except Exception as e:
        print(f"Error saving audio to {path}: {e}")

def check_stop_flag():
    try:
        if not os.path.exists(STOP_FLAG_FILE):
            return False
        with open(STOP_FLAG_FILE, "r") as f:
            content = f.read().strip()
        return content.lower() == "stop"
    except Exception as e:
        print(f"Error checking stop flag: {e}")
        return False

def main_loop_process(prediction_queue, should_run_event):
    print("Voice detection process started for real-time analysis.")
    current_merged_file_path = os.path.join(RECORDINGS_DIR, f"live_recording_{uuid.uuid4().hex}.wav")

    if os.path.exists(STOP_FLAG_FILE):
        os.remove(STOP_FLAG_FILE)

    try:
        with wave.open(current_merged_file_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)

            while should_run_event.is_set() and not check_stop_flag():
                audio = record_audio_chunk()
                if audio.size > 0:
                    wf.writeframes((audio * 32767).astype(np.int16).tobytes())
                    features = extract_features(audio)
                    score = predict_brainrot(features)
                    label = "brainrot" if score > THRESHOLD else "normal"

                    result = {"score": round(score, 3), "label": label}
                    prediction_queue.put(json.dumps(result))
                time.sleep(0.1)

    except Exception as e:
        print(f"Error in main_loop_process: {e}")
    finally:
        print("Real-time detection process stopped.")

        if os.path.exists(current_merged_file_path) and os.path.getsize(current_merged_file_path) > 44:
            try:
                audio_segment = AudioSegment.from_wav(current_merged_file_path)
                mp3_path = current_merged_file_path.replace(".wav", ".mp3")
                audio_segment.export(mp3_path, format="mp3")
                print(f"Saved live recording as: {mp3_path}")

                latest_audio_path = os.path.join(RECORDINGS_DIR, "latest_realtime_audio.txt")
                with open(latest_audio_path, "w") as f:
                    f.write(os.path.basename(mp3_path))
            except Exception as e:
                print(f"Error converting or saving live recording: {e}")
            finally:
                if os.path.exists(current_merged_file_path):
                    os.remove(current_merged_file_path)
        else:
            print(f"No valid audio recorded to save from {current_merged_file_path}")

        if os.path.exists(STOP_FLAG_FILE):
            os.remove(STOP_FLAG_FILE)

def predict_from_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: Audio file not found at {filepath}")
        return 0.0

    try:
        audio_segment = AudioSegment.from_file(filepath)
        audio_segment = audio_segment.set_frame_rate(SAMPLE_RATE).set_channels(1)
        audio_np = np.array(audio_segment.get_array_of_samples()).astype(np.float32) / 32768.0

        features = extract_features(audio_np)
        return predict_brainrot(features)
    except Exception as e:
        print(f"Error processing uploaded file {filepath}: {e}")
        return 0.0

def main_loop():
    print("main_loop is now primarily used internally or as a placeholder. For real-time analysis, use the WebSocket endpoint.")
    pass