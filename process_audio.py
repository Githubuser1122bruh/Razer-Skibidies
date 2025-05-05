import numpy as np
import librosa
import librosa.display
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from pydub import AudioSegment
import os
import uuid
import time

try:
    base_dir = os.path.expanduser("~")
    recordings_dir = os.path.join(base_dir, "Razer-Skibidies", "recordings")
    os.makedirs(recordings_dir, exist_ok=True) 
    # Load the recorded audio
    audio_data = np.load("recorded_audio.npy")
    print("Loaded audio data:", audio_data)

    # Convert the NumPy array to a format compatible with pydub
    audio_data = (audio_data * 32767).astype(np.int16)  # Scale to 16-bit PCM format
    sample_rate = 44100


    audio_data = np.load("recorded_audio.npy")
    print("Loaded audio data:", audio_data)
    print("Shape of data:", audio_data.shape)

    audio_data = audio_data.flatten()
    print("flattened data", audio_data)

    sample_rate = 44100

    plt.figure(figsize=(10,4))
    librosa.display.waveshow(audio_data, sr=sample_rate)
    plt.title("waveform of recorded audio")
    plt.xlabel("time in seconds")
    plt.ylabel("amplitude")
    plt.show()

    mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
    print("extracted mfccs shape:", mfccs.shape)

    scaler = StandardScaler()
    mfccs_normalized = scaler.fit_transform(mfccs.T)
    print("normalized mfccs shape", mfccs_normalized.shape)

    plt.figure(figsize=(10,4))
    librosa.display.specshow(mfccs, sr=sample_rate, x_axis="time", cmap="viridis")
    plt.colorbar(format="%+2.0f dB")
    plt.title("Waveform of audio recorded")
    plt.xlabel("Time (s)")
    plt.ylabel("MFCC Coefficients")
    plt.show()

    mfccs_normalized = np.expand_dims(mfccs_normalized, axis=0)
    print("prepared data shape:", mfccs_normalized.shape)

except FileNotFoundError:
    print("no file found, please run the script again ")
except Exception as e:
    print("an error occured" + str(e))
