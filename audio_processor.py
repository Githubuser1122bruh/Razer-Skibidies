import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import subprocess

import sounddevice as sd

from glob import glob

import librosa
import librosa.display
import IPython.display as ipd

from itertools import cycle

sns.set_theme(style="white", palette=None)
color_pal = plt.rcParams["axes.prop_cycle"].by_key()["color"]
color_cycle = cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])

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
        return None  # Return None if the headset is not found
    
    sd.default.device = headset_device

    try:
        print("Currently listening...")
        audio_data = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=1)
        sd.wait()

        max_amplitude = np.max(np.abs(audio_data))

        if max_amplitude > threshold:
            print("Sound detected!")
            return audio_data  # Return the recorded audio data
        else:
            print("No sound detected.")
            return None  # Return None if no sound is detected
    except Exception as e:
        print("There was an error: " + str(e))
        return None

if __name__ == "__main__":
    import numpy as np

    headset_name = "External Microphone"
    threshold = 0.02
    sample_rate = 22050
    duration = 0.5

    print("Starting voice detection..., press ctrl+c to end the loop")
    try:
        while True:
            audio_data = detect_voice(threshold=threshold, sample_rate=sample_rate, duration=duration, headset_name=headset_name)
            if audio_data is not None:
                # Save the audio data to a NumPy file
                np.save("recorded_audio.npy", audio_data)
                print("Audio data saved to 'recorded_audio.npy'")
            else:
                print("No audio data to save.")
    except KeyboardInterrupt:
        print("Voice detection ended by user.")
        subprocess.run(["/usr/bin/python3", "/Users/samhithpola/Documents/GitHub/Razer-Skibidies#/process_audio.py"])