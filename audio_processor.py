import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import subprocess
import os
import sounddevice as sd
import wave
from glob import glob
import tensorflow as tf
import uuid
from pydub import AudioSegment
import librosa
import librosa.display
import IPython.display as ipd

from itertools import cycle
from tensorflow.keras.models import load_model

recordings_dir = os.path.join(os.getcwd(), "recordings")
os.makedirs(recordings_dir, exist_ok=True)
STOP_FLAG_FILE = "stop_flag.txt"

merged_file = os.path.join(recordings_dir, f"merged_audio_{uuid.uuid4().hex}.wav")
merged_mp3_file = os.path.join(recordings_dir, f"merged_audio_{uuid.uuid4().hex}.mp3")

latest_audio_file = os.path.join(recordings_dir, "latest_audio.txt")
with open(latest_audio_file, "w") as f:
    f.write(os.path.basename(merged_mp3_file))

model = load_model("brainrot_detector.h5")
scaler_mean = np.load("scaler_mean.npy")
scaler_scale = np.load("scaler_scale.npy")

X_test = np.load("X_test.npy")
y_test = np.load("y_test.npy")

sns.set_theme(style="white", palette=None)
color_pal = plt.rcParams["axes.prop_cycle"].by_key()["color"]
color_cycle = cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])

def scale_features(features):
    return (features - scaler_mean) / scaler_scale

def check_stop_flag():
    """checks for stop file"""
    return os.path.exists(STOP_FLAG_FILE)

def record_audio_chunk(sample_rate=44100, duration=3):
    """Records a 3-second audio chunk and normalizes it to float32."""
    print("Recording 3-second audio chunk...")
    audio_data = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()

    # Normalize audio data to float32 in the range [-1.0, 1.0]
    audio_data = audio_data.astype(np.float32) / 32768.0
    return audio_data

def detect_brainrot(audio_data, sample_rate=44100, threshold=0.5):
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / 32768.0
    mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
    mfccs_mean=np.mean(mfccs.T, axis=0)
    mfccs_mean = mfccs_mean.reshape(1,-1)

    prediction = model.predict(mfccs_mean)
    print(f"model prediction: {prediction}")
    return prediction[0][0] > threshold

def detect_voice(threshold=0.02, sample_rate=44100, duration=0.5, headset_name="External Microphone"):
    """
    Detects voice in a sound file by using an audio threshold.
    Returns the recorded audio data as a NumPy array if sound is detected.
    """
    devices = sd.query_devices()
    headset_device = None
    for i, device in enumerate(devices):
        if headset_name.lower() in device['name'].lower():
            headset_device = i
            break
    
    if headset_device is None:
        print("The skibidy razers are not connected currently, please connect them.")
        return None 
    
    sd.default.device = headset_device

    try:
        print("Currently listening...")
        audio_data = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=1)
        sd.wait()

        max_amplitude = np.max(np.abs(audio_data))

        if max_amplitude > threshold:
            print("Sound detected!")
            
            if detect_brainrot(audio_data.flatten(), sample_rate):
                print("you brainrot not skibidi alpha")
            else:
                print("no brainrot you are good")
            return audio_data
        else:
            print("No sound detected.")
            return None 
    except Exception as e:
        print("There was an error: " + str(e))
        return None


def detect_voice(threshold=0.02, sample_rate=44100, duration=0.5, headset_name="External Microphone"):
    """
    Detects voice in a sound file by using an audio threshold.
    Returns the recorded audio data as a NumPy array if sound is detected.
    """
    devices = sd.query_devices()
    headset_device = None
    for i, device in enumerate(devices):
        if headset_name.lower() in device['name'].lower():
            headset_device = i
            break
    
    if headset_device is None:
        print("The skibidy razers are not connected currently, please connect them.")
        return None 
    
    sd.default.device = headset_device

    try:
        print("Currently listening...")
        audio_data = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=1)
        sd.wait()

        max_amplitude = np.max(np.abs(audio_data))

        if max_amplitude > threshold:
            print("Sound detected!")
            
            if detect_brainrot(audio_data.flatten(), sample_rate):
                print("you brainrot not skibidi alpha")
            else:
                print("no brainrot you are good")
            return audio_data
        else:
            print("No sound detected.")
            return None 
    except Exception as e:
        print("There was an error: " + str(e))
        return None


if __name__ == "__main__":
    import numpy as np

    headset_name = "External Microphone"
    threshold = 0.02
    sample_rate = 22050
    duration = 3

    print("Starting voice detection..., press ctrl+c to end the loop")
    try:
        # Open a WAV file to store the merged audio
        with wave.open(merged_file, "wb") as wf:
            wf.setnchannels(1)  # Mono audio
            wf.setsampwidth(2)  # 16-bit PCM
            wf.setframerate(sample_rate)

            while True:
                if check_stop_flag():
                    print("Detection ended.")
                    os.remove(STOP_FLAG_FILE)
                    break

                # Record a 3-second audio chunk
                audio_data = record_audio_chunk(sample_rate, duration)
                wf.writeframes(audio_data.tobytes())

                # Perform live analysis on the recorded chunk
                if detect_brainrot(audio_data.flatten(), sample_rate):
                    print("Live Analysis: You have brainrot, not skibidi alpha.")
                else:
                    print("Live Analysis: No brainrot detected, you are good.")

    except KeyboardInterrupt:
        print("Voice detection interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Voice detection ended.")

        # Convert the merged WAV file to MP3
        if os.path.exists(merged_file):
            audio = AudioSegment.from_wav(merged_file)
            audio.export(merged_mp3_file, format="mp3")
            print(f"Merged audio saved as {merged_mp3_file}")

            # Run the process_audio.py script
            subprocess.run(["/usr/bin/python3", "process_audio.py"])
        else:
            print(f"Error: {merged_file} does not exist.")
            
        # Evaluate the model
        loss, accuracy = model.evaluate(X_test, y_test)
        print(f"Test Loss: {loss}")
        print(f"Test Accuracy: {accuracy}")

if os.path.exists(merged_file):
    with wave.open(merged_file, "rb") as wf:
        audio_data = wf.readframes(wf.getnframes())
        audio_data = np.frombuffer(audio_data, dtype=np.float32) * 32768.0
        audio_data = audio_data.astype(np.int16)

    audio = AudioSegment(
        audio_data.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    audio.export(merged_mp3_file, format="mp3")
    print(f"Merged audio saved as {merged_mp3_file}")
else:
    print(f"Error: {merged_file} does not exist.")