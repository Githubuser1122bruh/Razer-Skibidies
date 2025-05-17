import os
import uuid
import wave
import numpy as np
import sounddevice as sd
import tensorflow as tf
import librosa
from pydub import AudioSegment
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

# === Safe input device selection ===
devices = sd.query_devices()
input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]

print("Available input devices:")
for i in input_devices:
    print(f"{i}: {devices[i]['name']}")

# Automatically select a working input device if none specified
if not isinstance(sd.default.device, (list, tuple)) or sd.default.device[0] is None:
    sd.default.device = (input_devices[0], None)
    print(f"Default input device set to: {devices[input_devices[0]]['name']}")

# Debug print to verify device setup
print(f"Using input device: {sd.default.device[0]} – {devices[sd.default.device[0]]['name']}")

# Load model and scaler
if os.path.exists("brainrot_lstm_model.h5"):
    model = load_model("brainrot_lstm_model.h5")
elif os.path.exists("best_model.h5"):
    model = load_model("best_model.h5")
else:
    model = load_model("brainrot_detector_advanced.h5")

scaler_mean = np.load("scaler_mean.npy")
scaler_scale = np.load("scaler_scale.npy")

# Constants
SAMPLE_RATE = 22050
DURATION = 3  # seconds
N_MFCC = 13
MAX_TIMESTEPS = 130
INPUT_FEATURES = 39
STOP_FLAG_FILE = "stop_flag.txt"
THRESHOLD = 0.9

# Setup
RECORDINGS_DIR = os.path.join(os.getcwd(), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)
MERGED_FILE = os.path.join(RECORDINGS_DIR, f"merged_audio_{uuid.uuid4().hex}.wav")

# === Feature processing ===
def scale_features(features):
    flat = features.reshape(-1, INPUT_FEATURES)
    scaled = (flat - scaler_mean) / scaler_scale
    return scaled.reshape(1, MAX_TIMESTEPS, INPUT_FEATURES).astype(np.float32)

def extract_features(audio):
    if not np.all(np.isfinite(audio)) or np.max(np.abs(audio)) < 1e-4:
        print("Audio is silent or corrupted.")
        return None

    try:
        mfcc = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
        delta = librosa.feature.delta(mfcc)
        delta2 = librosa.feature.delta(mfcc, order=2)
        full = np.vstack([mfcc, delta, delta2])  # (39, T)
        full = full.T  # (T, 39)

        if np.isnan(full).any():
            print("MFCC contains NaN values.")
            return None

        padded = pad_sequences([full], maxlen=MAX_TIMESTEPS, dtype='float32', padding='post')
        return scale_features(padded)  # keep batch dim
    except Exception as e:
        print(f"Feature extraction error: {e}")
        return None

# === Prediction ===
def predict_brainrot(features):
    if features is None:
        return 0.0
    prediction = model.predict(features, verbose=0)
    return float(prediction[0][0])

def detect_brainrot():
    audio = record_audio_chunk()
    features = extract_features(audio)
    return predict_brainrot(features)

# === Audio recording ===
def record_audio_chunk():
    print("Recording...")
    audio = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten()

def save_audio(audio, path):
    int_audio = (audio * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int_audio.tobytes())

# === Stop control ===
def check_stop_flag():
    return os.path.exists(STOP_FLAG_FILE)

def main_loop():
    print("Voice detection started. Ctrl+C or create stop_flag.txt to stop.")
    try:
        with wave.open(MERGED_FILE, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)

            while True:
                if check_stop_flag():
                    print("Stop flag detected. Exiting...")
                    os.remove(STOP_FLAG_FILE)
                    break

                audio = record_audio_chunk()
                wf.writeframes((audio * 32767).astype(np.int16).tobytes())

                features = extract_features(audio)
                score = predict_brainrot(features)

                if score > THRESHOLD:
                    print(f"Live Analysis: You have brainrot (score: {score:.2f})")
                else:
                    print(f"Live Analysis: No brainrot detected (score: {score:.2f})")

    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        if os.path.exists(MERGED_FILE):
            audio = AudioSegment.from_wav(MERGED_FILE)
            mp3_path = MERGED_FILE.replace(".wav", ".mp3")
            audio.export(mp3_path, format="mp3")
            print(f"Saved audio as: {mp3_path}")
