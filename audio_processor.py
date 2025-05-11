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
from sklearn.preprocessing import StandardScaler

# Load model and scaler
if os.path.exists("brainrot_lstm_model.h5"):
    model = load_model("brainrot_lstm_model.h5")
elif os.path.exists("best_model.h5"):
    model = load_model("best_model.h5")
else:
    model = load_model("brainrot_detector_advanced.h5")

scaler_mean = np.load("scaler_mean.npy")
scaler_scale = np.load("scaler_scale.npy")

# Audio parameters
SAMPLE_RATE = 22050
DURATION = 3  # seconds
N_MFCC = 13
THRESHOLD = 0.9
MAX_TIMESTEPS = 130  # must match training shape
INPUT_FEATURES = 39  # 13 MFCC + delta + delta2

STOP_FLAG_FILE = "stop_flag.txt"
RECORDINGS_DIR = os.path.join(os.getcwd(), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)
MERGED_FILE = os.path.join(RECORDINGS_DIR, f"merged_audio_{uuid.uuid4().hex}.wav")

def scale_features(features):
    flat = features.reshape(-1, INPUT_FEATURES)
    scaled = (flat - scaler_mean) / scaler_scale
    return scaled.reshape(1, MAX_TIMESTEPS, INPUT_FEATURES)

def check_stop_flag():
    return os.path.exists(STOP_FLAG_FILE)

def record_audio_chunk(duration=DURATION, sample_rate=SAMPLE_RATE):
    print("Recording...")
    audio = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten()

def extract_features(audio, sample_rate=SAMPLE_RATE):
    if np.max(np.abs(audio)) < 1e-4:
        print("Audio is silent.")
        return None

    mfcc = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=N_MFCC)
    delta = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2)
    full = np.vstack([mfcc, delta, delta2])  # (39, T)
    full = full.T  # (T, 39)
    padded = pad_sequences([full], maxlen=MAX_TIMESTEPS, dtype='float32', padding='post')
    return scale_features(padded[0])

def detect_brainrot():
    audio = record_audio_chunk()
    features = extract_features(audio)
    if features is None:
        return 0.0
    padded = tf.keras.preprocessing.sequence.pad_sequences([features], maxlen=130, padding='post', dtype='float32')
    scaled = (padded[0] - scaler_mean) / scaler_scale
    prediction = model.predict(scaled)
    return prediction[0][0]


def save_audio(audio, file_path, sample_rate=SAMPLE_RATE):
    int_audio = (audio * 32767).astype(np.int16)
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_audio.tobytes())

def main_loop():
    print("Starting voice detection. Press Ctrl+C to stop.")
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
                if features is not None:
                    if detect_brainrot(features):
                        print("Live Analysis: You have brainrot.")
                    else:
                        print("Live Analysis: No brainrot detected.")
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        # Convert merged WAV to MP3
        if os.path.exists(MERGED_FILE):
            audio = AudioSegment.from_wav(MERGED_FILE)
            mp3_path = MERGED_FILE.replace(".wav", ".mp3")
            audio.export(mp3_path, format="mp3")
            print(f"Audio saved as: {mp3_path}")

if __name__ == "__main__":
    main_loop()
