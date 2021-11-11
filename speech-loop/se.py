#!/usr/bin/env python

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

from stt_loop import processMicrophoneStream
from utils import pblue, pred, pgreen, pcyan, pyellow, prainbow, beep, concat, sanitize_translation, elapsed_time, normalize_text, recognize_stop_word

from display_sender import DisplaySender
from display_manager import DisplayManager

from tongue_twister import TongueTwister

from kw_parser import replace_punct

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

# FONT_FILE = "./fonts/Roboto-MediumItalic.ttf"
FONT_FILE = "./fonts/Newsreader_36pt-Medium.ttf"
MAX_WORDS = 24

PAUSE_LENGTH = 2 # If there is no mic input in `PAUSE_LENGTH` seconds, the display will be reset on subsequent input.

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
    print("CHop endword text:", text)
    kw_end = ["I'm out", "peace out"] if SPEECH_LANG != "cs-CZ" else ["díky", "jedeš"]
    
    if re.search(rf"\b(.*)(({kw_end[0]})|({kw_end[1]}))\b", text, re.I):
        text = re.sub(rf"\b(({kw_end[0]})|({kw_end[1]}))\b", "", text)
        text = text.strip()
        print("Matched, returning:", text)
        return text

    print("Didn't match, returning:", text)
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
        speaking_rate=0.9, # 0.75, # 0.5 - 4.0
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
    # send_simple_msg("Converting text to speech...")
    # Convert continuation to speech
    start = time.time()
    _text_to_speech(text)
    end = time.time()
    print("(text to speech)   ", colored(elapsed_time(start, end), "magenta"))
    # send_simple_msg(f"(text to speech)    {elapsed_time(start, end)}")

def play_audio():
    print("Playing audio...")
    subprocess.run(
        ["mplayer", "output.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def translate_response(response):
    print("Translating response...")
    # send_simple_msg("Translating GPT-3 response...")
    start = time.time()
    res = translate_client.translate(response, target_language=getLangCode(OUTPUT_SPEECH_LANG))
    res = res["translatedText"]
    end = time.time()
    print("(translation)   ", colored(elapsed_time(start, end), "magenta"))
    # send_simple_msg(f"(translation)    {elapsed_time(start, end)}")
    return res

def log_gpt3_response(msg):
    """ `nc -lkv 5432` to listen. """

    # send_simple_msg(msg)

    s = socket.socket()
    try:
        s.connect((DEBUG_HOST, DEBUG_PORT))
        s.send((msg + "\n\n" + resp + "\n\n").encode())
    except:
        pass
    finally:
        s.close()

class App:
    def __init__(self, speech_lang=SPEECH_LANG, reset_pause=PAUSE_LENGTH):
        self.text_buffer = ""
        self.prev_text_buffer = ""
        self.text_buffer_window = ""

        self.max_words = 24
        self.window_wiped_flag = False

        self.trans_buffer = ""
        self.trans_buffer_window = ""

        self.speech_lang = speech_lang

        self.display = DisplaySender(
            TRANSCRIPTION_HOST,
            TRANSCRIPTION_PORT,
            FONT_FILE
        )
        self.dm = DisplayManager(self, self.display, padding=(150, 200))

        self.last_sent_time = 0
        self.reset_pause = reset_pause

        self.gpt3_resp = ""
        
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
            if recognize_stop_word(text):
                self.dm.clear()
                self.reset_buffer()
                self.reset_trans_buffer()
                continue

            # Once speech end is recognized, text is sent to GPT-3
            if recognize_speech_end(text):
                text = chop_endword(text)

                self.push_to_buffer(text)
                self.dm.display()

                self.feed_gpt3(self.text_buffer)
                
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

            transcript = replace_punct(transcript)
            
            # This part clears the display and starts writing from the top
            # if there was a longer pause.
            t = time.time()
            if t - self.last_sent_time > self.reset_pause:
                self.text_buffer_window = ""
                self.trans_buffer_window = ""
            self.last_sent_time = t

            if not result.is_final:
                sys.stdout.write(transcript + overwrite_chars + "\r")    
                self.dm.display_intermediate(transcript)

                sys.stdout.flush()
                num_chars_printed = len(transcript)
            else:
                self.dm.display_intermediate(transcript)

                return (transcript + overwrite_chars + "\n")

    def push_to_buffer(self, text):
        self.text_buffer = (concat(self.text_buffer, text)).strip()
        if len(self.text_buffer_window.split(" ")) > self.max_words:
            self.text_buffer_window = text.strip()
            self.window_wiped_flag = True
        else:
            self.text_buffer_window = (concat(self.text_buffer_window, text)).strip()

    def reset_buffer(self):
        self.prev_text_buffer = self.text_buffer
        self.text_buffer = ""
        self.text_buffer_window = ""

    def push_to_trans_buffer(self, text):
        self.trans_buffer = (concat(self.trans_buffer, text)).strip()

    def reset_trans_buffer(self):
        self.trans_buffer = ""
        self.trans_buffer_window = ""

    def translate_cs(self, text):
        pyellow(f"Translating text: {text}")
        translation = translate_client.translate(
            self.text_buffer_window,
            target_language="en"
        )["translatedText"]
        pyellow(f"Received: {translation}")
        translation = sanitize_translation(translation)
        pyellow(f"After sanitization: {translation}")

        self.trans_buffer_window = translation

        self.trans_buffer = translation
        self.dm.display_translation()

    def display_translation_async(self, text):
        t = threading.Thread(target=self.translate_cs, args=(text,))
        t.start()

    def feed_gpt3(self, x):
        if len(x) == 0:
            # self.dm.display("Hypothesis empty")
            pred("\nHypothesis empty\n")
            return

        os.system('play -nq -t alsa synth {} sine {}'.format(0.3, 440)) # Beep sound to signal end of recording

        pred(f"GPT-3 input: {x}")

        # Translate hypothesis from Czech to English.
        if self.speech_lang != "en-US":
            start = time.time()
            # self.dm.display("Translating hypothesis...")
            print("Translating hypothesis...")
            x = translate_client.translate(x, target_language="en")
            x = x["translatedText"] 
            end = time.time()
            print("(translation)   ", colored(elapsed_time(start, end), "magenta"))

        x = x.capitalize()
        pyellow(x + "\n")
        print("Sending text to GPT-3...")
        # self.dm.display(f"set_gpt: {x}")

        # Generate continuation
        y = ""
        num_blanks = 0
        max_blanks = 3
        while len(y.strip()) < 1 and num_blanks < MAX_SUCC_BLANKS:
            start = time.time()
            resp = openai.Completion.create(
                engine=ENGINE,
                prompt=x,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )
            end = time.time()
        
            y = resp["choices"][0]["text"]
            y = normalize_text(y)
    
            # Postprocess translated text
            y = y.lstrip(". ")               # remove leftover dots and spaces from the beggining
            y = y.replace("&quot;","")       # remove "&quot;"
            y = y.strip()

            # Print response stats
            prainbow(
                ["(GPT-3 response)", "w"],
                ["   " + elapsed_time(start, end), "m"],
                [f'   {len(resp["choices"][0]["text"])} chars', "c"],
                ["   {:.3f} tokens".format(len(resp["choices"][0]["text"]) / 4), "y"],
                [f'   {len(y)} chars clean', "g"],
                ["   {:.3f} tokens clean".format(len(y) / 4), "r"],
                ["   {:.3f} tokens total".format((len(y) + len(x)) / 4), "b"]
            )

            if len(y) < 1:
                print("Received blank response :(")
                num_blanks = num_blanks + 1

        if num_blanks == MAX_SUCC_BLANKS:
            y = random.choice([
                "Try again.",
                "Sorry, can you please try again.",
                "I don't understand. Please try again.",
                "Sorry, what?"
            ])
        else:
            pblue(y)

        if OUTPUT_SPEECH_LANG != "en-US":
            y = translate_response(y)

        self.gpt3_resp = y

        text_to_speech(y)

        # log_gpt3_response("".join([
        #         f"(GPT-3 response)",
        #         "   " + elapsed_time(start, end),
        #         f'   {len(gpt3_resp["choices"][0]["text"])} chars',
        #         "   {:.3f} tokens".format(len(gpt3_resp["choices"][0]["text"]) / 4),
        #         f'   {len(response)} chars clean',
        #         "   {:.3f} tokens clean".format(len(response) / 4),
        #         "   {:.3f} tokens total".format((len(response) + len(hypothesis)) / 4),
        #         f"   {len(response.split())} words"
        #     ]))

        play_audio()

        os.system('play -nq -t alsa synth {} sine {}'.format(0.3, 440)) # Beep sound to signal end of response
        print()

if __name__ == "__main__":
    # Hra s vyslovnostou / Prepis
    TongueTwister().run()

    app = App(speech_lang=SPEECH_LANG)
    app.run()
