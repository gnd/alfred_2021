import os
import re
import six
import sys
import fire
import time
import openai
import socket
import random
import subprocess
import configparser

from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

from collections import namedtuple
Seed = namedtuple("Seed", "title prompts")

from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow, prainbow, cmagenta, ccyan, cyellow, cred
from display_sender import DisplaySender

from voice_fx import *

# Load variables from config
settings = os.path.join(sys.path[0], '../settings.ini')
config = configparser.ConfigParser()
config.read(settings)

# Assign config variables - open ai
OPENAI_MODEL = config.get('openai', 'MODEL')
MAX_TOKENS_QUESTIONS = int(config.get('openai', 'MAX_TOKENS_QUESTIONS'))
TEMPERATURE_QUESTIONS = float(config.get('openai', 'TEMPERATURE_QUESTIONS'))
# display settings
TRANSCRIPTION_HOST = config.get('display', 'DISPLAY_HOST')
TRANSCRIPTION_PORT = int(config.get('display', 'DISPLAY_PORT'))
BIG_FONT_SIZE = int(config.get('display', 'BIG_FONT_SIZE'))
# question settings
NAMES_FILE = config.get('questions', 'NAMES_FILE')
SEEDS_DIR = config.get('questions', 'SEEDS_DIR')
SECONDS_FOR_ENTRANCE = int(config.get('questions', 'SECONDS_FOR_ENTRANCE'))
STOCK_RESP_PROB = float(config.get('questions', 'STOCK_RESP_PROB'))
EN_QUESTION_PROB = float(config.get('questions', 'EN_QUESTION_PROB'))
MIN_Q_PER_P = int(config.get('questions', 'MIN_Q_PER_P'))
MAX_Q_PER_P = int(config.get('questions', 'MAX_Q_PER_P'))
SPEECH_MU = int(config.get('questions', 'SPEECH_MU'))
SPEECH_SIGMA = int(config.get('questions', 'SPEECH_SIGMA'))
# voice effects
AUDIO_FNAME = config.get("voice-effects", "AUDIO_FNAME")
AUDIO_FX_FNAME = config.get("voice-effects", "AUDIO_FX_FNAME")
P1_DELAY_ON_NAME = config.get("voice-effects", "P1_DELAY_ON_NAME")
P2_GRADUAL_DECAY = config.get("voice-effects", "P2_GRADUAL_DECAY")

# Define some language codes
SPEECH_LANG = "cs-CZ"
TEXT_TARGET_LANG = "en"
OUTPUT_SPEECH_LANG = "cs-CZ"
OUTPUT_SPEECH_LANG = "en-GB"
OUTPUT_LANG_CZ = "cs"
OUTPUT_LANG_RU = 'ru'
OUTPUT_LANG_SK = 'sk'

STOCK_RESPONSES_CZ = [
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
    "Roztomilé.",
    "Roztomiloučké.",
    "Gratuluji.",
    "Díky.",
    "Gratulky.",
]

STOCK_RESPONSES_EN = [
    "Hmm",
    "I suppose so.",
    "Interesting.",
    "Alright.",
    "Please, don't go on.",
    "Very interesting.",
    "M, I didn't expect that.",
    "Lovely.",
    "O, that sounds lovely.",
    "I'm glad for you.",
    "Thank you. That's enough.",
]

display = DisplaySender(
    TRANSCRIPTION_HOST,
    TRANSCRIPTION_PORT
)

def send_to_display(msg):
    display.send(
        text=msg,
        fill=True,
        align="center",
        padding_left=40,
        padding_top=40,
    )

def send_to_display_rly_big(msg):
    display.send(
        text=msg,
        fill=True,
        align="center",
        padding_left=40,
        padding_top=40,
        font_size=BIG_FONT_SIZE,
    )

client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

def get_question_mark_idx(text):
    return text.find("?")

def normalize_text(text):
    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    text = re.sub(r"[0-9]+\.", "", text)
    text = re.sub(r"_+", "", text)
    text = re.sub("&quot;", "", text)
    text = re.sub(r"[“”\"‘’]", "", text)
    text = re.sub(r"[\n ]+", " ", text)
    text = text.strip()
    return text

def cut_to_sentence_end(text):
    """Cuts off unfinished sentence."""

    endIdx = max(text.rfind("."), text.rfind("?"), text.rfind("!"))
    endIdx = endIdx if endIdx > -1 else 0
    
    return text[0: endIdx + 1]

def pick_voice_randomly():
    return random.choice([texttospeech.SsmlVoiceGender.MALE, texttospeech.SsmlVoiceGender.FEMALE])

def text_to_speech(text, lang=OUTPUT_SPEECH_LANG, is_use_fx=False, fx_board=None):
    # Set the text input to be synthesized

    # Add emphasis randomly
    emph = random.choice(["strong", "none", "reduced", "moderate"])
    text = f"<emphasis level={emph}>" + text + "</emphasis>"

    text = "<speak>" + text + "</speak>"

    synthesis_input = texttospeech.SynthesisInput(ssml=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=lang, ssml_gender=pick_voice_randomly()
    )

    config.read(settings)
    SPEAKING_RATE = float(config.get('text-to-speech', 'SPEAKING_RATE'))

    audio_config = texttospeech.AudioConfig(
        speaking_rate=SPEAKING_RATE, # 0.75, # 0.5 - 4.0
        effects_profile_id=['medium-bluetooth-speaker-class-device'],
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    fname = AUDIO_FNAME
    # The response's audio_content is binary.
    with open(fname, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)

    if is_use_fx and fx_board is not None:
        apply_fx(fx_board, AUDIO_FNAME, AUDIO_FX_FNAME)

    fname = AUDIO_FX_FNAME if is_use_fx and fx_board is not None else AUDIO_FNAME
    subprocess.run(
        ["mplayer", fname],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return

def generate_question(prompt):
    print("Generating question...")
    q = ""
    while len(q) < 1:
        gpt3_resp = openai.Completion.create(
            engine=OPENAI_MODEL,
            prompt=prompt,
            temperature=0.9,
            max_tokens=64,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        q = gpt3_resp["choices"][0]["text"]
        pyellow(q)
        q = normalize_text(q)
        q = cut_to_sentence_end(q)
        q = q[0:get_question_mark_idx(q) + 1]
        if len(q) == 0:
            print("Empty question, regenerating...")

    print("Question generated...")
    return q

def translate_question(q, lang):
    print("Translating question...")
    # Translate generated text back to the language of speech
    if lang == 'cz':
        out = translate_client.translate(q, target_language=OUTPUT_LANG_CZ)
    if lang == 'ru':
        out = translate_client.translate(q, target_language=OUTPUT_LANG_RU)
    if lang == 'sk':
        out = translate_client.translate(q, target_language=OUTPUT_LANG_SK)
    out = out["translatedText"]
    out = re.sub(r"[0-9]+\. ", "", out)
    print("Translation done...")
    return out

def question_me(prompt, lang, fx_board=None):
    q_en = normalize_text(generate_question(prompt))
    # q_sk = translate_question(q_en, 'sk')
    q_cs = translate_question(q_en, 'cz')

    send_to_display(q_en.strip() + "\n\n" + q_cs.strip())
    pcyan(q_en)

    is_use_fx = True if fx_board is not None else False

    if lang == 'en':
        text_to_speech(q_en, "en-GB", is_use_fx, fx_board)
    if lang == 'cz':
        # q_cs = translate_question(q_en, 'cz')
        text_to_speech(q_cs, "cs-CZ", is_use_fx, fx_board)
    if lang == 'ru':
        q_ru = translate_question(q_en, 'ru')
        text_to_speech(q_ru, "ru-RU", is_use_fx, fx_board)
    if lang == 'sk':
        text_to_speech(q_sk, "sk-SK", is_use_fx, fx_board)

def question_person(name, prompt, lang, fx_board=None):
    q_en = normalize_text(generate_question(prompt))

    if len(q_en) > 0:
        q_en = q_en[0].lower() + q_en[1:]
    q_en =name + ", " + q_en

    # q_sk = translate_question(q_en, 'sk')
    q_cs = translate_question(q_en, 'cz')

    # send_to_display(q_en.strip() + "\n\n" + q_sk.strip())
    send_to_display(q_en.strip() + "\n\n" + q_cs.strip())
    pcyan(q_en)

    is_use_fx = True if fx_board is not None else False

    if lang == 'cz':
        # q_cs = translate_question(q_en, 'cz')
        text_to_speech(q_cs, 'cs-CZ', is_use_fx, fx_board)
    if lang == 'en':
        text_to_speech(q_en, 'en-GB', is_use_fx, fx_board)
    if lang == 'ru':
        q_ru = translate_question(q_en, 'ru')
        text_to_speech(q_ru, 'ru-RU', is_use_fx, fx_board)
    if lang == 'sk':
        text_to_speech(q_sk, 'sk-SK', is_use_fx, fx_board)

def gen_num_q():
    return random.randint(MIN_Q_PER_P, MAX_Q_PER_P)

def gen_q_pause():
    p = random.gauss(SPEECH_MU, SPEECH_SIGMA)
    while p <= 0:
        p = random.gauss(SPEECH_MU, SPEECH_SIGMA)
    pgreen(p)
    # return 0
    return p

def question_specific_person(name, seeds, lang, hell_voice=False):
    # This block of code formats and displays the name of the
    # questined person multiple times with a big font on the
    # screen.
    name_text = "\n".join([4*("".join([3*name.upper() + " "]))])
    send_to_display_rly_big(name_text)

    text_to_speech(
        text="Hey, " + name,
        lang="cs-CZ",
        is_use_fx=P1_DELAY_ON_NAME,
        fx_board=b_delay)

    for x in range(SECONDS_FOR_ENTRANCE):
        sys.stdout.write(cyellow(f"Asking question in {SECONDS_FOR_ENTRANCE - x}\r"))
        sys.stdout.flush()
        time.sleep(1)

    num_question = gen_num_q()
    print("Proceeding to ask ", num_question, "questions")

    # 1. question
    seed = random.choice(seeds)
    print("Seed " + cred(seed.title))
    prompt = get_prompt(seed)
    
    pmagenta("Generating question...")

    if hell_voice and num_question == 1:
        question_me(prompt, lang, fx_board=b_hell)
    else:
        question_me(prompt, lang)

    pmagenta("Giving time to answer...")
    time.sleep(gen_q_pause())
    
    # next questions
    for x in range(num_question - 1):
        if random.randint(0, 100) < STOCK_RESP_PROB:
            if lang == 'cz':
                text_to_speech(random.choice(STOCK_RESPONSES_CZ))
            if lang == 'en':
                text_to_speech(random.choice(STOCK_RESPONSES_EN))

        seed = random.choice(seeds)
        print("Seed " + cred(seed.title))
        
        prompt = get_prompt(seed)
        pmagenta("Generating question...")

        if hell_voice and x == num_question - 2:
            question_me(prompt, lang, fx_board=b_hell)
        else:
            question_me(prompt, lang)
        
        pmagenta("Giving time to answer...")
        time.sleep(gen_q_pause())

    text_to_speech("<emphasis level=\"moderate\">Ok carbon.</emphasis>", "cs-CZ")
    cmd = input("> ")
    return cmd

def get_prompt(seed):
    prompts = seed.prompts
    idx = random.randint(0, len(prompts) - 1)
    return prompts[idx]

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

def part_one(names, seeds):
    cmd = ""
    idx = 0

    # If enabled reads the question in a robotic voice from robot hell
    # used as a surprise
    hell_voice = False

    while cmd != "q":
        # Determine language first based on OUTPUT_SPEECH_LANG
        if OUTPUT_SPEECH_LANG == 'cs-CZ':
            lang = "cz"
        if OUTPUT_SPEECH_LANG == 'en-GB':
            lang = "en"
        # But language can be still overriden by a special command
        if cmd == "e":
            lang = "en"
        if cmd == "c":
            lang = "cz"
        if cmd == "r":
            lang = "ru"
        if cmd == "s":
            lang = "sk"
        if cmd == "h":
            hell_voice = True
        if idx % len(names) == 0:
            idx = 0
            random.shuffle(names) # Shuffle names randomly
        name = names[idx]
        print_people(names, idx) # Prints order and currently questioned person.
        idx = idx + 1
        cmd = question_specific_person(name, seeds, lang, hell_voice=hell_voice)
        
        # Disable hell voice after usage
        if hell_voice:
            hell_voice = False

def part_two(names, seeds):
    idx = 0
    distort_count = 0

    while True:
        if idx % len(names) == 0:
            idx = 0
            random.shuffle(names) # Shuffle names randomly
        
        name = names[idx]
        print_people(names, idx) # Prints order and currently questioned person.
        idx = idx + 1

        seed = random.choice(seeds)
        print("Seed " + cred(seed.title))
        prompt = get_prompt(seed) # Random seed, random prompt

        # Determine language first based on OUTPUT_SPEECH_LANG
        if OUTPUT_SPEECH_LANG == 'en-GB':
            lang = "en"
        if OUTPUT_SPEECH_LANG == 'cs-CZ':
            lang = "cz"
            # But language can be still overriden by a dice roll
            if random.randint(0, 100) < EN_QUESTION_PROB:
                lang = "en"

        # Also generate question in Czech for Anastazia, Eliska and Lenka
        if (name == 'Anastázia'):
            lang = 'cz'
        if (name == 'Eliška'):
            lang = 'cz'
        if (name == 'Eva'):
            lang = 'cz'
        # if (name == 'Lucia'):
        #     lang = 'sk'
        if (name == 'Lenka'):
            lang = 'cz'
        
        pyellow(f"Generating question for {name} in {lang}")

        # if P2_GRADUAL_DECAY:
        #     question_person(name, prompt, lang, make_b_decay(distort_count))
        #     distort_count = distort_count + 1
        # else:
        #     question_person(name, prompt, lang)
        question_person(name, prompt, lang)

        # wait
        sleep_time = random.randint(1, 15)
        # sleep_time = random.randint(0, 1)
        print("Waiting for", sleep_time)
        time.sleep(sleep_time)

def main(part=1):
    # Load names
    NAMES = [l.strip() for l in open(NAMES_FILE, "r").readlines()]
    # Load seeds
    SEEDS = load_seeds()
    
    if part == 1:
        # First part - series of questions for specific people
        part_one(NAMES, SEEDS)

        pred("\n┏(-_-)┛┗(-_-﻿ )┓ OK CARBON ┗(-_-)┛┏(-_-)┓\n")
        os.system('play -nq -t alsa synth {} sine {}'.format(1, 440))

    # Second part - questions at random for different people
    part_two(NAMES, SEEDS)


if __name__ == "__main__":
    fire.Fire(main)
