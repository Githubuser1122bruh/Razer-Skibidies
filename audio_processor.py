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
tf.config.threading.set_intra_op_parallelism_threads(1)
tf.config.threading.set_inter_op_parallelism_threads(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOP_FLAG_FILE = os.path.join(BASE_DIR, "stop_flag.txt")

# Constants
SAMPLE_RATE = 22050
DURATION = 3  # seconds
N_MFCC = 13
MAX_TIMESTEPS = 130
INPUT_FEATURES = 39
THRESHOLD = 0.95  # Lowered threshold as requested
RECORDINGS_DIR = os.path.join(os.getcwd(), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# Prepare file path for merged audio (wav + mp3)
MERGED_FILE = os.path.join(RECORDINGS_DIR, f"merged_audio_{uuid.uuid4().hex}.wav")

# Load model and scaler
if os.path.exists("brainrot_lstm_model.h5"):
    model = load_model("brainrot_lstm_model.h5")
elif os.path.exists("best_model.h5"):
    model = load_model("best_model.h5")
else:
    model = load_model("brainrot_detector_advanced.h5")

scaler_mean = np.load("scaler_mean.npy")
scaler_scale = np.load("scaler_scale.npy")

# Select audio input device automatically if not set
devices = sd.query_devices()
input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
print("Available input devices:")
for i in input_devices:
    print(f"{i}: {devices[i]['name']}")

if not isinstance(sd.default.device, (list, tuple)) or sd.default.device[0] is None:
    sd.default.device = (input_devices[0], None)
print(f"Using input device: {sd.default.device[0]} – {devices[sd.default.device[0]]['name']}")

def scale_features(features):
    flat = features.reshape(-1, INPUT_FEATURES)
    scaled = (flat - scaler_mean) / scaler_scale
    return scaled.reshape(1, MAX_TIMESTEPS, INPUT_FEATURES).astype(np.float32)

def extract_features(audio):
    if not np.all(np.isfinite(audio)) or np.max(np.abs(audio)) < 0.01:
        print(f"Audio is silent or corrupted. Max amplitude: {np.max(np.abs(audio))}")
        return None

    try:
        mfcc = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
        delta = librosa.feature.delta(mfcc)
        delta2 = librosa.feature.delta(mfcc, order=2)
        full = np.vstack([mfcc, delta, delta2]).T  # (time_steps, 39)

        if np.isnan(full).any():
            print("MFCC contains NaN values.")
            return None

        padded = pad_sequences([full], maxlen=MAX_TIMESTEPS, dtype='float32', padding='post')
        return scale_features(padded)

    except Exception as e:
        print(f"Feature extraction error: {e}")
        return None

def predict_brainrot(features):
    if features is None:
        return 0.0
    prediction = model.predict(features, verbose=0)
    return float(prediction[0][0])

def record_audio_chunk():
    print("Recording...")
    audio = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten()

def detect_brainrot():
    """Record a 3-second chunk and predict brainrot score."""
    audio = record_audio_chunk()
    features = extract_features(audio)
    if features is None:
        return -1  # Signal that input was invalid/silent
    return predict_brainrot(features)

def save_audio(audio, path):
    int_audio = (audio * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int_audio.tobytes())

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

def main_loop():
    print("Voice detection started. Ctrl+C or create stop_flag.txt to stop.")
    try:
        with wave.open(MERGED_FILE, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)

            while True:
                if check_stop_flag():
                    print("Stop flag detected. Exiting main loop...")
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

            # Write latest audio filename for frontend download
            latest_audio_path = os.path.join(RECORDINGS_DIR, "latest_audio.txt")
            with open(latest_audio_path, "w") as f:
                f.write(os.path.basename(mp3_path))