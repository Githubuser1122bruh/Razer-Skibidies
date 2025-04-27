from gtts import gTTS
from pydub import AudioSegment
import os

language = 'en'

output_folder = "brainrot_audio"
os.makedirs(output_folder, exist_ok=True)

brainrot = ["af", "alpha", "altered my brain chemistry", "and I oop", "anti-tourism", "ate", "aura", "axel in harlem",
    "baby gronk", "babygirl", "bae", "based", "beige flag", "beta", "bet", "big yikes", "blud", "boomer", "brat", "brainrot", "bussin",
    "camp", "cap", "caught in 4K", "cheugy", "clap back", "cozzie livs", "cringe", "copium", "coffee badging", "coded",
    "dab", "deadass", "delulu", "demure", "dank", "drag", "drip", "drippy", "dusted", "doomscrolling",
    "e-boy", "e-girl", "enshittification", "era", "extra",
    "fam", "fanum tax", "fire", "fit check", "flex", "for the plot", "fr", "frfr", "finsta",
    "gas up", "gassed up", "ghost", "girl dinner", "girl math", "glow up", "goated", "goated with the sauce", "goblin mode", "goofy ahh", "grip reaper", "grindset", "gyatt",
    "hawk tuah", "heat", "highkey", "hits different", "hot girl summer", "hot take", "holding space",
    "IDK", "IMO", "IRL", "it's giving", "it's the _ for me", "ice cream so good",
    "janky", "jelly", "JOMO",
    "Karen", "keysmash", "kiki",
    "left no crumbs", "let him cook", "let them cook", "LFG", "lit", "lowkey", "low taper fade", "L",
    "main character energy", "mewing", "mid", "menty b", "millennial pause", "mood", "mother", "mukbang",
    "no cap", "NPC", "NSFW", "neon",
    "Ohio", "only in Ohio", "OP", "OTP", "on god",
    "parasocial", "periodt", "pookie", "POV", "preen", "pressed",
    "QOTD",
    "ratio", "rent-free", "rizz", "ROFL", "rawdogging", "romantasy",
    "sassy", "savage", "sheesh", "sigma", "simp", "skibidi", "slaps", "slay", "smh", "snatched", "spiraling", "stan", "sus", "sussy", "side quest", "stenographer", "supermajority",
    "tea", "thirst trap", "TIL", "TL;DR", "TMI", "toxic", "touch grass", "thirst", "throw shade", "tush push",
    "uwu",
    "vibe check", "vine boom", "vibing",
    "W", "woke", "WFH", "wildin'",
    "XOXO",
    "yapping", "yeet", "yass", "YOLO",
    "zaddy", "zesty", "zillennial"]

for i in range(len(brainrot)):
    mp3_path = os.path.join(output_folder, f"brainrot{i}.mp3")
    myobj = gTTS(text=brainrot[i], lang=language, slow=True)
    myobj.save(mp3_path)

    wav_path = os.path.join(output_folder, f"brainrot{i}.wav")
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")

    os.remove(mp3_path)


    #PLEASE DONT RUN THIS AGAIN, THIS WAS TO MAKE THE DATASET USING TEXT TO SPEECH AND RUNNING IT AGAIN
    #MAY CAUSE ISSUES WITH FILE PATHS OF THE DATASET