import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import subprocess
import os
import sounddevice as sd

from glob import glob
import tensorflow as tf

import librosa
import librosa.display
import IPython.display as ipd

from itertools import cycle
from tensorflow.keras.models import load_model

STOP_FLAG_FILE = "stop_flag.txt"

def check_stop_flag():
    """checks for stop file"""
    return os.path.exists(STOP_FLAG_FILE)

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

def detect_brainrot(audio_data, sample_rate=22050, threshold=0.5):
    mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
    mfccs_mean=np.mean(mfccs.T, axis=0)

    mfccs_mean = mfccs_mean.reshape(1,-1)

    prediction = model.predict(mfccs_mean)
    print(f"model prediction: {prediction}")
    return prediction[0][0] > threshold

def detect_voice(threshold=0.02, sample_rate=22050, duration=0.5, headset_name="External Microphone"):
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
        while True:
            if check_stop_flag():
                print("detection ended")
                os.remove(STOP_FLAG_FILE)
                break

            audio_data = detect_voice(threshold=threshold, sample_rate=sample_rate, duration=duration, headset_name=headset_name)
            if audio_data is not None:
                np.save("recorded_audio.npy", audio_data)
                print("Audio data saved to 'recorded_audio.npy'")
            else:
                print("No audio data to save.")
    except Exception as e:
        print("an error occured" + e)
    finally:
        print("Voice detection ended by user.")
        subprocess.run(["/usr/bin/python3", "/Users/samhithpola/Documents/GitHub/Razer-Skibidies#/process_audio.py"])
        loss, accuracy = model.evaluate(X_test, y_test)
        print(f"Test Loss: {loss}")
        print(f"Test Accuracy: {accuracy}")