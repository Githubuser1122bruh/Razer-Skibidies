from gtts import gTTS
from pydub import AudioSegment
import os

language = 'en'

output_folder = "no_brainrot"
os.makedirs(output_folder, exist_ok=True)

brainrot_words = ["How are you today?", "What did you have for breakfast?", "Can you help me with this?", "I’ll call you later.",
    "That sounds like a great idea.", "Have you seen the latest movie?", "Let’s grab a coffee sometime.",
    "What time does the meeting start?", "I’m so tired today.", "I’m looking forward to the weekend.",
    "Are you free tomorrow?", "Do you want to go for a walk?", "I need to finish my homework.", "Let’s go out for lunch.",
    "Do you want to watch a movie?", "It’s so nice to meet you.", "How’s your day going?", "What’s the plan for today?",
    "I can’t wait for the holidays.", "I need a nap.", "What are you doing this weekend?", "I just finished reading that book.",
    "Let’s hang out sometime soon.", "I can’t find my keys.", "Are you going to the gym today?", "I’ve been feeling a little down lately.",
    "I’ve been really busy with work.", "Let’s go to the park.", "How’s your family doing?", "What’s the weather like today?",
    "Do you need help with anything?", "Let me know if you want to chat.", "I’m not sure what to eat for dinner.",
    "I hope you’re having a good day.", "Do you want to go to the mall?", "I’ve been working on a new project.",
    "What’s your favorite TV show?", "I’m meeting some friends later.", "Let’s plan something fun for the weekend.",
    "I’ve been feeling a little stressed out.", "What did you do over the weekend?", "I’m really tired, but I have work to do.",
    "I hope you’re doing well.", "Let’s catch up soon.", "I’m going to the grocery store later.", "Do you want to go out for dinner?",
    "How’s everything at work?", "What are you up to today?", "Let’s do something fun this weekend.", "Have you been to the new café in town?",
    "I’ve been thinking about traveling soon.", "I’m trying to stay active.", "I love reading in my spare time.",
    "I’ve been learning something new lately.", "I’m working on some personal goals.", "How was your day at work?",
    "I need a little break.", "Let’s go for a hike sometime.", "I’m going to relax today.", "What’s your favorite restaurant around here?",
    "I’ve been really into cooking lately.", "Let me know if you need anything.", "I’m planning a trip next month.",
    "Can you give me some advice?", "I’ve been saving up for something special.", "I can’t wait to see you again.",
    "How’s your day been so far?", "I’ve been really busy with school.", "It’s been a long week.", "What’s your favorite type of music?",
    "I need to clean my room today.", "What did you have for dinner last night?", "I’m feeling a bit under the weather today.",
    "I’ve been trying to eat healthier.", "Let’s take a walk around the block.", "How are things going with you?",
    "I need to catch up on my sleep.", "Do you want to go to a concert?", "I’m really excited for the weekend.",
    "I’ve been getting into photography lately.", "I’m planning on going to the beach.", "Let’s grab dinner sometime this week.",
    "I’m going to a wedding next weekend.", "How’s your week going?", "I’ve been trying to be more organized.", "What’s up?", "How’s it going?", "I’m tired.", "Just chilling.", "I’m good, thanks.", "Sounds good.", 
    "That’s cool.", "I’ll be there soon.", "How about you?", "Let’s go!", "That works for me.", "I’m down.",
    "I’ll think about it.", "That’s awesome!", "Can’t wait!", "I’m excited.", "I’m so busy.", "I’ll call you later.",
    "Got it.", "Let’s talk soon.", "How’s your day?", "I’m on my way.", "See you soon.", "Take care.",
    "I’ll catch you later.", "I’m heading out.", "Let’s meet up.", "I need a break.", "How’s everything?", 
    "I’m all set.", "I’ll let you know.", "I’m doing alright.", "Same here.", "I’m feeling good today.", 
    "Let me check.", "I’m not sure.", "Let’s do it.", "I’m thinking about it.", "It’s fine.", "I’m all in.",
    "That’s funny!", "That’s hilarious!", "It’s not a big deal.", "I’ll be right back.", "What’s your plan?",
    "I can’t decide.", "I’m with you on that.", "I’m so hungry.", "I’m just relaxing.", "Let’s go grab something to eat.",
    "I’m ready.", "I need to focus.", "I’ll take care of it.", "I’ve got this.", "Can you help me?", "What’s new?",
    "That sounds nice.", "Let’s keep in touch.", "I’m in.", "Sounds great.", "I’m good for now.", "Take it easy.",
    "Just woke up.", "Not much, you?", "I’ll be fine.", "Not yet.", "I’m good now.", "I’m not feeling it.",
    "Sure, why not?", "It’s up to you.", "Can’t complain.", "I’m here.", "What do you think?", "That’s amazing!",
    "I don’t know yet.", "I’ll figure it out.", "I’ve been busy.", "I’ll check it out.", "Can we do it later?",
    "I need to rest.", "Let’s catch up soon.", "I’m not sure what to do.", "I’m in the mood to relax.", "I’m trying to stay positive.", "I’m just thinking.", "I’ll get back to you on that.", "It’s been a long day.", "I’m so tired of this.",
    "I need some coffee.", "I’ll be back in a minute.", "I’m not in the mood.", "Can we talk later?", 
    "It’s been a rough week.", "I’ll try my best.", "Not today.", "Can you believe that?", "I’m just chilling at home.",
    "I’m running late.", "I’m so over this.", "I can’t wait to see it.", "I need to grab something.", "Let’s get this over with.",
    "I’ll be home soon.", "I’m not feeling great.", "I’m working on it.", "It’s been a while.", "I didn’t expect that.",
    "It’s been a crazy day.", "Let’s hang out soon.", "Let’s grab lunch.", "I’m waiting for something.", "I’m not up for it.",
    "That’s so interesting.", "I’ll think about it later.", "It’s all good.", "What’s the plan?", "I’ll let you know soon.",
    "That sounds perfect.", "I have a lot going on.", "I’ve been thinking about it.", "I’ll send you the details.",
    "I need to talk to someone.", "I’ll make time for it.", "We’ll figure it out.", "I’m planning to relax today.",
    "I’m super busy right now.", "What are you up to?", "That was unexpected.", "I’m not ready for this.", "It’s time to go.",
    "I need a few minutes.", "I’ll call you back.", "I’m feeling better now.", "I’ll see you in a bit.", "That’s really kind of you.",
    "I can’t believe it.", "I’ll just go with the flow.", "I need to check my schedule.", "I’ll try again later.",
    "It’s not as bad as it seems.", "Let’s talk about it tomorrow.", "I’m really excited for this.", "I’m so ready for this.",
    "I can’t stop laughing.", "I’m in the middle of something.", "I’ll be right there.", "Let’s meet up soon.",
    "It’s all happening so fast.", "I’m just taking it easy today.", "I need some space.", "I’ll catch you up later.",
    "I’m having a great time.", "I’ll figure it out soon.", "It’s all coming together.", "Let’s stay in touch.",
    "I’ll give you a call later.", "I’m taking a break.", "That’s so nice of you.", "I’m really proud of you.",
    "I’ll take a look at it.", "I don’t have time right now.", "That’s a good idea.", "Let’s meet this weekend.",
    "I’m feeling pretty good.", "What’s going on with you?", "I’m just enjoying the moment.", "I can’t wait to start.",
    "I’ll need some help with this.", "I don’t think I can make it.", "It’s been a peaceful day.", "Let’s keep it simple.",
    "I’m in no rush.", "I’m starting to get the hang of it.", "I need to focus on something.", "I’m really glad you’re here.",
    "I’m just taking it one step at a time.", "I’ve got a lot of things to do.", "I’ll try to get it done soon.",
    "I’ll let you know when I’m free.", "I’m just relaxing for now.", "Let’s do this another time.", "I’m glad we talked.",
    "I’m just looking for a place to relax.", "I’ll need a little more time.", "I’m so grateful for this opportunity.",
    "I can’t stop thinking about it.", "I’m just going with the flow.", "Yeah", "Hello", "Hi", "Salutations", "Why", "Who", "When", "Where", "What"]
    


for i in range(len(brainrot_words)):
    mp3_path = os.path.join(output_folder, f"normal{i}.mp3")
    myobj = gTTS(text=brainrot_words[i], lang=language, slow=False)
    myobj.save(mp3_path)

    wav_path = os.path.join(output_folder, f"normal{i}.wav")
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")

    os.remove(mp3_path)


    #PLEASE DONT RUN THIS AGAIN, THIS WAS TO MAKE THE DATASET USING TEXT TO SPEECH AND RUNNING IT AGAIN
    #MAY CAUSE ISSUES WITH FILE PATHS OF THE DATASET