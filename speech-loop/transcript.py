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
import ConfigParser

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

# Load variables from config
settings = os.path.join(sys.path[0], '../settings.ini')
config = ConfigParser.ConfigParser()
config.read(settings)

# Assign config variables
TRANSCRIPTION_HOST = config.get('display', 'DISPLAY_HOST')
TRANSCRIPTION_PORT = config.get('display', 'DISPLAY_PORT')
DEBUG_HOST = config.get('display', 'DEBUG_HOST')
DEBUG_PORT = config.get('display', 'DEBUG_PORT')
DEFAULT_PADDING_TOP = config.get('display', 'DEFAULT_PADDING_TOP')
DEFAULT_PADDING_LEFT = config.get('display', 'DEFAULT_PADDING_LEFT')
FONT_FILE = config.get('display', 'FONT')
MAX_WORDS = config.get('display', 'MAX_WORDS')
PAUSE_LENGTH = config.get('display', 'PAUSE_LENGTH')

# Define some language codes
SPEECH_EN = "en-US"
SPEECH_CS = "cs-CZ"
SPEECH_sk = "sk-SK"
TEXT_EN = "en"
TEXT_CS = "cs"
TEXT_SK = "sk"


class App:
    def __init__(self, speech_lang=SPEECH_CS, reset_pause=PAUSE_LENGTH):
        self.text_buffer = ""
        self.prev_text_buffer = ""
        self.text_buffer_window = ""

        self.max_words = MAX_WORDS
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

        # Translation client
        self.translate_client = translate.Client()

        
    def run(self):
        while True:
            if self.text_buffer == "":
                pcyan("Listening :)\n")

            # Blocks to process audio from the mic. This function continues
            # once the end of the utterance has been recognized.        
            (text, kw_dict) = processMicrophoneStream(
                self.speech_lang,
                self.handle_stt_response
            )
        
            # Print "complete utterance" as recognized by the STT service.
            pgreen(text)

            if kw_dict.get("in_english"):
                self.speech_lang = SPEECH_EN
                pred("Setting input English")
                self.dm.display_action("input: English")
                time.sleep(1)
                self.dm.clear()
                self.reset_buffer()
                self.reset_trans_buffer()
                continue

            if kw_dict.get("in_czech"):
                self.speech_lang = SPEECH_CS
                pred("Setting input Czech")
                self.dm.display_action("input: Czech")
                time.sleep(1)
                self.dm.clear()
                self.reset_buffer()
                self.reset_trans_buffer()
                continue

            # Stop word clears the text
            if kw_dict.get("clear"):
                self.dm.clear()
                self.reset_buffer()
                self.reset_trans_buffer()
                continue
            
            if kw_dict.get("delete"):
                self.push_to_buffer(text)

                kw_del = ["delete", "Delete"] if self.speech_lang == "en-US" else ["smazat", "Smazat"]

                pblue(f"Buffer before replacement {self.text_buffer}")
                print()
                pblue(f"Window before replacement {self.text_buffer_window}")

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

                pblue(f"Buffer after replacement {self.text_buffer}")
                print()
                pblue(f"Window after replacement {self.text_buffer_window}")

                self.dm.display()
                self.display_translation_async()
                continue
            if kw_dict.get("submit"):
                self.push_to_buffer(text)
                self.dm.display()
                
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

                sys.stdout.flush()
                num_chars_printed = len(transcript)
                
                for v in kw_dict.values():
                    if v:
                        return ((transcript + overwrite_chars + "\n"), kw_dict)
            else:
                self.dm.display_intermediate(transcript)
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
        # TODO - switch to Slovak for Kiosk performance
        # TODO - set this also in the config file
        self.text_buffer_window,
        if (self.speech_lang == SPEECH_CS or self.speech_lang == SPEECH_SK): 
            target_language = TEXT_EN
        else:
            target_language = TEXT_CS
        translation = self.translate_client.translate(
            self.text_buffer_window,
            target_language
        )["translatedText"]
        pyellow(f"Received: {translation}")
        translation = sanitize_translation(translation)
        pyellow(f"After sanitization: {translation}")

        self.trans_buffer_window = translation

        self.trans_buffer = translation
        self.dm.display_translation()

    def display_translation_async(self):
        t = threading.Thread(target=self.translate)
        t.start()

    def chop_endword(self, text):
        print("Chop endword text:", text)
        kw_end = ["I'm out"] if self.speech_lang != "cs-CZ" else ["díky"]
    
        if re.search(rf"\b(.*)(({kw_end[0]})|({kw_end[1]}))\b", text, re.I):
            text = re.sub(rf"\b(díky|Díky|I'm out)\b", "", text)
            text = text.strip()
            print("Matched, returning:", text)
            return text

        print("Didn't match, returning:", text)
        return text


# Stavba / Generovanie / Karaoke
if __name__ == "__main__":
    App(speech_lang=SPEECH_CS).run()
