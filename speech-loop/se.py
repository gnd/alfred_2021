#!/usr/bin/env python

from __future__ import division

import re
import os
import sys
import fire
import time
import socket
import threading
import subprocess
from playsound import playsound
from google.cloud import speech
from google.cloud import translate_v2 as translate

from stt_loop import processMicrophoneStream
from utils import pblue, pred, pgreen, pcyan, pyellow, prainbow, beep, concat, sanitize_translation, elapsed_time, normalize_text, recognize_stop_word
from utils import delete_word

from display_sender import DisplaySender
from display_manager import DisplayManager

from tongue_twister import TongueTwister

from kw_parser import replace_punct, recognize_kws, INSTRUCT_RE, NORMAL_RE

from gpt3 import GPT3Client

DAVINCI = "davinci"
DAVINCI_BETA_INSTRUCT = "davinci-instruct-beta"

SPEECH_EN = "en-US"
SPEECH_CS = "cs-CZ"
TEXT_EN = "en"
TEXT_CS = "cs"

# TRANSCRIPTION_HOST = "127.0.0.1"
TRANSCRIPTION_HOST = "192.168.217.207"
# GND HOME
TRANSCRIPTION_HOST = "192.168.217.207"
TRANSCRIPTION_PORT = 5000

DEFAULT_PADDING_TOP = 40
DEFAULT_PADDING_LEFT = 40

# FONT_FILE = "./fonts/Roboto-MediumItalic.ttf"
FONT_FILE = "./fonts/Newsreader_36pt-Medium.ttf"
MAX_WORDS = 24

PAUSE_LENGTH = 10 # If there is no mic input in `PAUSE_LENGTH` seconds, the display will be reset on subsequent input.

class App:
    def __init__(self, speech_lang=SPEECH_EN, reset_pause=PAUSE_LENGTH):
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
        self.dm = DisplayManager(self, self.display, padding=(DEFAULT_PADDING_TOP, DEFAULT_PADDING_LEFT))

        self.last_sent_time = 0
        self.reset_pause = reset_pause
        
        self.input_lang = "en"
        self.output_lang = "en"
        self.model = "normal"

        # Translation client
        self.translate_client = translate.Client()

        # GPT3 client
        self.gpt3 = GPT3Client(self, self.translate_client, engine=DAVINCI)
        self.gpt3_resp = ""
        
    def run(self):
        while True:
            if self.text_buffer == "":
                pcyan("Listening :)\n")
                
            # Always show state
            self.dm.display_state(self.input_lang, self.output_lang, self.model)

            # Blocks to process audio from the mic. This function continues
            # once the end of the utterance has been recognized.        
            (text, kw_dict) = processMicrophoneStream(
                self.speech_lang,
                self.handle_stt_response
            )
        
            # Print "complete utterance" as recognized by the STT service.
            pgreen(text)

            # Set Instruct
            if kw_dict.get("instruct"):
                self.model = "instruct"
                self.gpt3.set_engine(DAVINCI_BETA_INSTRUCT)
                pred("Setting instruct")
                self.dm.display_action("engine: Instruct")
                time.sleep(1)
                text = re.sub(INSTRUCT_RE, "", text).strip()

            # Set Normal
            if kw_dict.get("normal"):
                self.model = "normal"
                self.gpt3.set_engine(DAVINCI)
                pred("Setting normal")
                self.dm.display_action("engine: Normal")
                time.sleep(1)
                text = re.sub(NORMAL_RE, "", text).strip()

            if kw_dict.get("in_english"):
                self.input_lang = "en"
                self.speech_lang = SPEECH_EN
                pred("Setting input English")
                self.dm.display_action("input: English")
                time.sleep(1)
                self.dm.clear()
                # Always show state
                self.dm.display_state(self.input_lang, self.output_lang, self.model)
                self.reset_buffer()
                self.reset_trans_buffer()
                continue

            if kw_dict.get("in_czech"):
                self.input_lang = "cs"
                self.speech_lang = SPEECH_CS
                pred("Setting input Czech")
                self.dm.display_action("input: Czech")
                time.sleep(1)
                self.dm.clear()
                # Always show state
                self.dm.display_state(self.input_lang, self.output_lang, self.model)
                self.reset_buffer()
                self.reset_trans_buffer()
                continue

            if kw_dict.get("out_english"):
                self.output_lang = "en"
                self.gpt3.output_speech_lang = SPEECH_EN
                pred("Setting output English")
                self.dm.display_action("output: English")
                time.sleep(1)
                continue

            if kw_dict.get("out_czech"):
                self.output_lang = "cs"
                self.gpt3.output_speech_lang = SPEECH_CS
                pred("Setting output Czech")
                self.dm.display_action("output: Czech")
                time.sleep(1)
                continue

            if kw_dict.get("show"):
                self.dm.display_action(self.text_buffer)
                time.sleep(3)
                self.dm.clear()
                continue
            
            # Stop word clears the text
            if kw_dict.get("clear"):
                self.dm.clear()
                # Always show state
                self.dm.display_state(self.input_lang, self.output_lang, self.model)
                self.reset_buffer()
                self.reset_trans_buffer()
                continue
            if kw_dict.get("delete"):
                self.push_to_buffer(text)

                kw_del = ["delete", "Delete"] if self.speech_lang == "en-US" else ["smazat", "Smazat"]

                # Delete in `text_buffer`
                num_dels = self.text_buffer.count(kw_del[0]) + self.text_buffer.count(kw_del[1])
                # Delete `num_dels` words and additionally all "delete"s.
                for x in range(num_dels * 2):
                    self.text_buffer = delete_word(self.text_buffer)

                # Delete in `text_buffer_window`
                num_dels = self.text_buffer_window.count(kw_del[0]) + self.text_buffer_window.count(kw_del[1])
                # Delete `num_dels` words and additionally all "delete"s.
                for x in range(num_dels * 2):
                    self.text_buffer_window = delete_word(self.text_buffer_window)

                self.dm.display()
                self.display_translation_async()
                continue
            if kw_dict.get("repeat"):
                self.text_buffer = self.prev_text_buffer
                self.dm.clear()
                self.gpt3.feed(self.text_buffer)
                self.dm.clear()
                self.reset_buffer()
                self.reset_trans_buffer()
                continue
            if kw_dict.get("continue"):
                self.text_buffer = concat(self.prev_text_buffer, self.gpt3_resp)
                self.dm.clear()
                self.gpt3.feed(self.text_buffer)
                self.dm.clear()
                self.reset_buffer()
                self.reset_trans_buffer()
                continue
            if kw_dict.get("submit"):
                text = self.chop_endword(text)

                self.push_to_buffer(text)
                self.dm.display()
                self.dm.clear()
                # Always show state
                self.dm.display_state(self.input_lang, self.output_lang, self.model)

                # Generate GPT-3 response.
                self.gpt3.feed(self.text_buffer)
                
                self.dm.clear()
                self.reset_buffer()
                self.reset_trans_buffer()
            else:
                self.push_to_buffer(text)
                self.dm.display()
                # translate new text and display buffered translation
                self.display_translation_async()
            

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
            kw_dict = recognize_kws(transcript)
            print(kw_dict)
            
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
                # Always show state
                self.dm.display_state(self.input_lang, self.output_lang, self.model)

                sys.stdout.flush()
                num_chars_printed = len(transcript)
                
                for v in kw_dict.values():
                    if v:
                        return ((transcript + overwrite_chars + "\n"), kw_dict)
            else:
                self.dm.display_intermediate(transcript)
                # Always show state
                self.dm.display_state(self.input_lang, self.output_lang, self.model)
                return ((transcript + overwrite_chars + "\n"), kw_dict)
                

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

    def translate(self):
        pyellow(f"Translating text: {self.text_buffer_window}")
        translation = self.translate_client.translate(
            self.text_buffer_window,
            target_language=TEXT_EN if self.speech_lang == SPEECH_CS else TEXT_CS
        )["translatedText"]
        pyellow(f"Received: {translation}")
        translation = sanitize_translation(translation)
        pyellow(f"After sanitization: {translation}")

        self.trans_buffer_window = translation

        self.trans_buffer = translation
        self.dm.display_translation()
        # Always show state
        self.dm.display_state(self.input_lang, self.output_lang, self.model)

    def display_translation_async(self):
        t = threading.Thread(target=self.translate)
        t.start()

    def chop_endword(self, text):
        print("Chop endword text:", text)
        kw_end = ["I'm out", "peace out"] if self.speech_lang != "cs-CZ" else ["díky", "jedeš"]
    
        if re.search(rf"\b(.*)(({kw_end[0]})|({kw_end[1]}))\b", text, re.I):
            text = re.sub(rf"\b(díky|Díky|jedeš|Jedeš|I'm out|peace out|Peace out)\b", "", text)
            text = text.strip()
            print("Matched, returning:", text)
            return text

        print("Didn't match, returning:", text)
        return text


# Stavba / Generovanie / Karaoke
if __name__ == "__main__":
    App(speech_lang=SPEECH_EN).run()
