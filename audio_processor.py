import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

import sounddevice as sd

from glob import glob

import librosa
import librosa.display
import IPython.display as ipd

from itertools import cycle

sns.set_theme(style="white", palette=None)
color_pal = plt.rcParams["axes.prop_cycle"].by_key()["color"]
color_cycle = cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])

def detect_voice(threshold=0.02, sample_rate = 22050, duration=0.5):
    """
    this is my very shitty attempt to detect voice in a sound file by using an audio threshold
    is actually quite simple in theory which is why i dont think it will work, its just using a boolean that 
    activates if the noise is louder than a certain amount of decibels, so ig if someone just whispers
    then they can bypass it so this is just temporary.
    """
