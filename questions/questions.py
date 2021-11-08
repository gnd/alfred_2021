import os
import re
import six
import sys
import fire
import time
import openai
import random
import subprocess
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

from collections import namedtuple
Seed = namedtuple("Seed", "title prompts")

from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow, prainbow, cmagenta, ccyan, cyellow, cred

IN_FILE_NAMES = "names.txt"
SEEDS_DIR = "seeds"

SPEECH_LANG = "cs-CZ"
TEXT_TARGET_LANG = "en"
OUTPUT_SPEECH_LANG = "cs-CZ"
OUTPUT_LANG = "cs"

ENGINE = "davinci-instruct-beta"
MAX_TOKENS = 150
TEMPERATURE = 0.9

SECONDS_FOR_ENTRANCE = 7

STOCK_RESPONSES = [
    "Zajímavé.", 
    "Ahá", 
    "Jasně.", 
    "Ani nepokračuj.", 
    "Velice zajímavé.", 
    "Mm, to jsem nečekela.", 
    "To jsem nečekela.",
    "Á, to zní moc hezky.",
    "To jsem ráda.",
    "To mi stačí. Děkuji.",
]

STOCK_RESP_PROB = 30

client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

def get_question_mark_idx(text):
    return text.find("?")

def normalize_text(text):
    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")
    
    text = re.sub(r"[0-9]+\. ", "", text)
    text = re.sub(r"_+", "", text)
    text = re.sub("&quot;", "", text)
    return text

def cut_to_sentence_end(text):
    """Cuts off unfinished sentence."""

    endIdx = max(text.rfind("."), text.rfind("?"), text.rfind("!"))
    endIdx = endIdx if endIdx > -1 else 0
    
    return text[0: endIdx + 1]

def pick_voice_randomly():
    return random.choice([texttospeech.SsmlVoiceGender.MALE, texttospeech.SsmlVoiceGender.FEMALE])

def text_to_speech(text):
    # Set the text input to be synthesized

    # Add emphasis randomly
    emph = random.choice(["strong", "none", "reduced", "moderate"])
    text = f"<emphasis level={emph}>" + text + "</emphasis>"

    text = "<speak>" + text + "</speak>"

    synthesis_input = texttospeech.SynthesisInput(ssml=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=OUTPUT_SPEECH_LANG, ssml_gender=pick_voice_randomly()
    )

    audio_config = texttospeech.AudioConfig(
        effects_profile_id=['medium-bluetooth-speaker-class-device'],
        audio_encoding=texttospeech.AudioEncoding.MP3,
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    fname = "output.mp3"
    # The response's audio_content is binary.
    with open(fname, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)

    subprocess.run(
        ["mplayer", "output.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return

def generate_question(prompt):
    q = ""
    while len(q) < 1:
        gpt3_resp = openai.Completion.create(
            engine=ENGINE,
            prompt=prompt,
            temperature=0.9,
            max_tokens=64,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        q = gpt3_resp["choices"][0]["text"]
        q = normalize_text(q)
        q = cut_to_sentence_end(q)
        q = q[0:get_question_mark_idx(q) + 1]
        q = q

    return q

def translate_question(q):
    # Translate generated text back to the language of speech
    out = translate_client.translate(q, target_language=OUTPUT_LANG)
    out = out["translatedText"]
    return out

def question_me(prompt):
    q = generate_question(prompt)
    q = translate_question(q)
    pcyan(q)
    text_to_speech(q)
    
def question_person(name, prompt):
    q = generate_question(prompt)
    q = translate_question(q)
    pcyan(name + ", " + q)
    q = name + ", <break time=\"500ms\"/>" + q
    text_to_speech(q)

def question_specific_person(name, seed):
    text_to_speech(random.choice(["Hey, <break time=\"500ms\"/>"]) + " " + name + ".")

    for x in range(SECONDS_FOR_ENTRANCE):
        sys.stdout.write(cyellow(f"Asking question in {SECONDS_FOR_ENTRANCE - x}\r"))
        sys.stdout.flush()
        time.sleep(1)

    # 1. question
    prompt = get_prompt(seed)
    pmagenta("Generating question...")
    question_me(prompt)
    cmd = input("> ")
    
    # next questions
    while cmd != "n" and cmd != "q":
        if random.randint(0, 100) < STOCK_RESP_PROB:
            text_to_speech(random.choice(STOCK_RESPONSES))
        
        prompt = get_prompt(seed)
        pmagenta("Generating question...")
        question_me(prompt)
        cmd = input("> ")

    text_to_speech("<emphasis level=\"moderate\">Ok carbon.</emphasis>")
    return cmd

def get_prompt(seed):
    idx = random.randint(0, len(seed) - 1)
    return seed[idx]

def print_people(people, current_idx):
    start = people[:current_idx]
    end = people[current_idx+1:]
    line = ccyan("[")
    for x in range(len(people)):
        if x == current_idx:
            line = line + cmagenta(people[x])
        else:
            line = line + ccyan(people[x])
        if x < (len(people) - 1):
            line = line + ccyan(", ")
    line = line + ccyan("]")
    print(line)

def load_seeds():
    seed_files = os.listdir("seeds")

    seed_titles = [f.replace(".txt", "").upper() for f in seed_files] # e.g. ["EGO", "CULTURE", "HUMAN", ...]
    
    seeds = []
    for idx, fname in enumerate(seed_files):
        # Split to prompts
        prompts = []
        for raw_prompt in open("seeds/" + fname, "r").read().split("\n\n"):
            lines = raw_prompt.split("\n")
            prompt = ""
            jdx = 0
            if lines[0][0] == "[":
                prompt = "Write a list of questions about " + lines[0][1:-1] + ":\n\n"
                jdx = 1
            elif lines[0][0] == "(":
                prompt = "Write a list of questions " + lines[0][1:-1] + ":\n\n"
                jdx = 1
            else:
                prompt = "Write a list of questions in a similar theme:\n\n"
            
            q_num = 1
            for kdx in range(jdx, len(lines)):
                prompt = prompt + str(q_num) + ". " + lines[kdx] + "\n\n"
                q_num = q_num + 1
            prompt = prompt + str(q_num) + ". "
            prompts.append(prompt)
        seeds.append(Seed(title=seed_titles[idx],prompts=prompts))

    log_seeds(seeds)

    return seeds
        
def log_seeds(seeds):
    with open("seeds-log.txt", "w") as outf:
        for s in seeds:
            for p in s.prompts:
                outf.writelines(p)
                outf.write("\n")
                outf.write("\n")
            outf.write("\n")

def main():
    # Load names
    NAMES = [l.strip() for l in open(IN_FILE_NAMES, "r").readlines()]

    SEEDS = load_seeds()
    
    # First part - series of questions for specific people
    cmd = ""
    idx = 0
    while cmd != "q":
        if idx % len(NAMES) == 0:
            idx = 0
            random.shuffle(NAMES) # Shuffle names randomly
        
        name = NAMES[idx]
        
        print_people(NAMES, idx) # Prints order and currently questioned person.
        
        idx = idx + 1
        
        seed = random.choice(SEEDS)
        print("Seed " + cred(seed.title))
        
        cmd = question_specific_person(name, seed.prompts)

    pred("\n┏(-_-)┛┗(-_-﻿ )┓ OK CARBON ┗(-_-)┛┏(-_-)┓\n")
    os.system('play -nq -t alsa synth {} sine {}'.format(1, 440))

    # Second part - question at random for different people
    cmd = ""
    while cmd != "q":
        seed = random.choice(SEEDS)
        print("Seed " + cred(seed.title))
        prompt = get_prompt(seed.prompts) # Random seed, random prompt
        name = random.choice(NAMES)
        pyellow(f"Generating question for {name}.")
        question_person(name, prompt)
        cmd = input(">") # Don't ask another question until requested


if __name__ == "__main__":
    fire.Fire(main)