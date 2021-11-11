#!/usr/bin/env python

# Note: Run as `python3 seven-eleven.py 2>/dev/null` to redirect stderr
#       to hide pyaudio warnings from the MicrophoneStream.

from __future__ import division

import re
import os
import sys
import fire
import time
import openai
import random
import socket
import threading
import subprocess
from termcolor import colored
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

import utils
from stt_loop import processMicrophoneStream
from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow, prainbow, beep

from display_sender import DisplaySender
from display_manager import DisplayManager

from tongue_twister import TongueTwister

SPEECH_LANG = "cs-CZ"
OUTPUT_SPEECH_LANG = "cs-CZ"

ENGINE = "davinci-instruct-beta"
MAX_TOKENS = 200
TEMPERATURE = 0.9

MAX_SUCC_BLANKS = 3

GPT3_RESP = ""

TRANSCRIPTION_HOST = "127.0.0.1"
TRANSCRIPTION_PORT = 5000

DEBUG_HOST = "127.0.0.1"
DEBUG_PORT = 5432

FONT_FILE = "./fonts/Roboto-MediumItalic.ttf"

SPEECH_CODE_TO_LANG_CODE = {
    "cs-CZ": "cs",
    "en-US": "en",
    "fr-FR": "fr",
    "de-DE": "de",
    "ru-RU": "ru",
    "cmn-CN": "zh-CN"
}

class SpeechCode:
    def __init__(self):
        self.CZECH = "cs-CZ"
        self.ENGLISH = "en-US"
        self.FRENCH = "fr-FR"
        self.GERMAN = "de-DE"
        self.RUSSIAN = "ru-RU"
        self.CHINESE = "cmn-CN"

class LangCode:
    def __init__(self):
        self.CZECH = "cs"
        self.ENGLISH = "en"
        self.FRENCH = "fr"
        self.GERMAN = "de"
        self.RUSSIAN = "ru"
        self.CHINESE = "zh-CN"

def getLangCode(speech_code):
    return SPEECH_CODE_TO_LANG_CODE.get(speech_code)

client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

def chop_endword(text):
    kw_end = ["I'm out", "peace out"] if SPEECH_LANG != "cs-CZ" else ["díky", "jedeš"]
    
    if re.search(rf"\b(.*)(({kw_end[0]})|({kw_end[1]}))\b", text, re.I):
        text = re.sub(rf"\b(({kw_end[0]})|({kw_end[1]}))\b", "", text)
        text = text.strip()
        return text

    return text

def recognize_speech_end(text):
    kw_end = ["I'm out", "peace out"] if SPEECH_LANG != "cs-CZ" else ["díky", "jedeš"]
    
    if re.search(rf"\b(.*)(({kw_end[0]})|({kw_end[1]}))\b", text, re.I):
        pyellow("> speech end")
        return True
    return False

def pick_voice_randomly():
    """Randomly choose between the male and female voice, if available."""
    return random.choice([texttospeech.SsmlVoiceGender.MALE, texttospeech.SsmlVoiceGender.FEMALE])

def _text_to_speech(text):
    """
    Synthesizes `text` into audio.
    
    The audio file is stored on disk as "output.mp3".
    """
    global OUTPUT_SPEECH_LANG
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=OUTPUT_SPEECH_LANG, ssml_gender=pick_voice_randomly()
    )
    audio_config = texttospeech.AudioConfig(
        speaking_rate=0.75, # 0.5 - 4.0
        effects_profile_id=['medium-bluetooth-speaker-class-device'],
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=0, # 20 for dying patient voice
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    fname = "output.mp3"
    with open(fname, "wb") as out:
        out.write(response.audio_content)
    return fname

def text_to_speech(text):
    print("Converting text to speech...")
    send_simple_msg("Converting text to speech...")
    # Convert continuation to speech
    start = time.time()
    _text_to_speech(text)
    end = time.time()
    print("(text to speech)   ", colored(utils.elapsed_time(start, end), "magenta"))
    send_simple_msg(f"(text to speech)    {utils.elapsed_time(start, end)}")

def play_audio():
    print("Playing audio...")
    subprocess.run(
        ["mplayer", "output.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def translate_response(response):
    print("Translating response...")
    send_simple_msg("Translating GPT-3 response...")
    start = time.time()
    res = translate_client.translate(response, target_language=getLangCode(OUTPUT_SPEECH_LANG))
    res = res["translatedText"]
    end = time.time()
    print("(translation)   ", colored(utils.elapsed_time(start, end), "magenta"))
    send_simple_msg(f"(translation)    {utils.elapsed_time(start, end)}")
    return res

def log_gpt3_response(msg):
    """ `nc -lkv 5432` to listen. """

    send_simple_msg(msg)

    s = socket.socket()
    try:
        s.connect((DEBUG_HOST, DEBUG_PORT))
        s.send((msg + "\n\n" + resp + "\n\n").encode())
    except:
        pass
    finally:
        s.close()

def do_with_hypothesis(hypothesis):
    pred(">>>>>>>>> DO WITH HYPOTHESIS")
    global GPT3_RESP

    if len(hypothesis) == 0:
        send_simple_msg("Hypothesis empty")
        pred("\nHypothesis empty\n")
        return

    os.system('play -nq -t alsa synth {} sine {}'.format(0.3, 440)) # Beep sound to signal end of recording

    # Translate hypothesis from Czech to English.
    if SPEECH_LANG != "en-US":
        start = time.time()
        send_simple_msg("Translating hypothesis...")
        print("Translating hypothesis...")
        hypothesis = translate_client.translate(hypothesis, target_language="en")
        hypothesis = hypothesis["translatedText"] 
        end = time.time()
        print("(translation)   ", colored(utils.elapsed_time(start, end), "magenta"))
        send_simple_msg(f"(translation)    {utils.elapsed_time(start, end)}")

    hypothesis = hypothesis.capitalize()
    pyellow(hypothesis + "\n")
    print("Sending text to GPT-3...")
    send_simple_msg(f"set_gpt: {hypothesis}")

    # Generate continuation

    # hypothesis = hypothesis + ":\n\n"
    
    response = ""
    num_blanks = 0
    max_blanks = 3
    while len(response.strip()) < 1 and num_blanks < MAX_SUCC_BLANKS:
        start = time.time()
        gpt3_resp = openai.Completion.create(
            engine=ENGINE,
            prompt=hypothesis,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            # stop=["\n\n"] 
        )
        end = time.time()
        
        out_text = gpt3_resp["choices"][0]["text"]
        out_text = utils.normalize_text(out_text)
    
        # Postprocess translated text
        out_text = out_text.lstrip(". ")               # remove leftover dots and spaces from the beggining
        response = out_text.replace("&quot;","")       # remove "&quot;"
        response = response.strip()

        # Print response stats
        prainbow(
            ["(GPT-3 response)", "w"],
            ["   " + utils.elapsed_time(start, end), "m"],
            [f'   {len(gpt3_resp["choices"][0]["text"])} chars', "c"],
            ["   {:.3f} tokens".format(len(gpt3_resp["choices"][0]["text"]) / 4), "y"],
            [f'   {len(response)} chars clean', "g"],
            ["   {:.3f} tokens clean".format(len(response) / 4), "r"],
            ["   {:.3f} tokens total".format((len(response) + len(hypothesis)) / 4), "b"]
        )

        if len(response) < 1:
            print("Received blank response :(")
            num_blanks = num_blanks + 1

    if num_blanks == MAX_SUCC_BLANKS:
        response = random.choice([
            "Try again.",
            "Sorry, can you please try again.",
            "I don't understand. Please try again.",
            "Sorry, what?"
        ])
    else:
        pblue(response)

    if OUTPUT_SPEECH_LANG != "en-US":
        response = translate_response(response)

    GPT3_RESP = response

    text_to_speech(response)

    log_gpt3_response("".join([
            f"(GPT-3 response)",
            "   " + utils.elapsed_time(start, end),
            f'   {len(gpt3_resp["choices"][0]["text"])} chars',
            "   {:.3f} tokens".format(len(gpt3_resp["choices"][0]["text"]) / 4),
            f'   {len(response)} chars clean',
            "   {:.3f} tokens clean".format(len(response) / 4),
            "   {:.3f} tokens total".format((len(response) + len(hypothesis)) / 4),
            f"   {len(response.split())} words"
        ]))

    play_audio()

    os.system('play -nq -t alsa synth {} sine {}'.format(0.3, 440)) # Beep sound to signal end of response
    print()

class App:
    def __init__(self, speech_lang=SPEECH_LANG):
        self.text_buffer = ""
        self.prev_text_buffer = ""
        self.trans_buffer = ""

        self.speech_lang = speech_lang

        self.display = DisplaySender(
            TRANSCRIPTION_HOST,
            TRANSCRIPTION_PORT,
            FONT_FILE
        )
        self.dm = DisplayManager(self, self.display, padding=(150, 200), max_words=24)
        
    def run(self):
        while True:
            if self.text_buffer == "":
                pcyan("Listening :)\n")

            # Blocks to process audio from the mic. This function continues
            # once the end of the utterance has been recognized.        
            text = processMicrophoneStream(
                self.speech_lang,
                self.handle_stt_response
            )
        
            # Print "complete utterance" as recognized by the STT service.
            pgreen(text)

            # Stop word clears the text
            if utils.recognize_stop_word(text):
                self.dm.clear()
                self.reset_buffer()
                self.reset_trans_buffer()
                continue

            # Once speech end is recognized, text is sent to GPT-3
            if recognize_speech_end(text):
                text = chop_endword(text)
                
                self.push_to_buffer(text)
                self.dm.display()
                
                do_with_hypothesis(self.text_buffer)
                
                self.dm.clear()
                self.reset_buffer()
                self.reset_trans_buffer()
            else:
                self.push_to_buffer(text)
                self.dm.display()
                # translate new text and display buffered translation
                self.display_translation_async(text)

    def handle_stt_response(self, responses):
        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue
            transcript = result.alternatives[0].transcript
            overwrite_chars = " " * (num_chars_printed - len(transcript))
            if not result.is_final:
                sys.stdout.write(transcript + overwrite_chars + "\r")    
                self.dm.display_intermediate(transcript)

                sys.stdout.flush()
                num_chars_printed = len(transcript)
            else:
                self.dm.display_intermediate(transcript)

                return (transcript + overwrite_chars + "\n")

    def push_to_buffer(self, text):
        self.text_buffer = (self.text_buffer + " " + text).strip()

    def reset_buffer(self):
        self.prev_text_buffer = self.text_buffer
        self.text_buffer = ""

    def push_to_trans_buffer(self, text):
        self.trans_buffer = (self.trans_buffer + " " + text).strip()

    def reset_trans_buffer(self):
        self.trans_buffer = ""

    def translate_cs(self, text):
        # t = translate_client.translate(
        #     text,
        #     target_language="cs"
        # )["translatedText"]
        # self.push_to_trans_buffer(t)

        # Translates entire buffer each time.
        self.trans_buffer = translate_client.translate(
            self.text_buffer,
            target_language="en"
        )["translatedText"]
        self.trans_buffer = utils.sanitize_translation(self.trans_buffer)
        
        self.dm.display_translation()

    def display_translation_async(self, text):
        t = threading.Thread(target=self.translate_cs, args=(text,))
        t.start()

if __name__ == "__main__":
    # Hra s vyslovnostou / Prepis
    TongueTwister().run()
    app = App(speech_lang=SPEECH_LANG)
    app.run()
