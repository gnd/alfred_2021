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
from utils import get_env
from stt_loop import processMicrophoneStream
from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow, prainbow, beep

from display_sender import DisplaySender
from display_manager import DisplayManager

# GND HOME
# TRANSCRIPTION_HOST = "192.168.217.207"

TRANSCRIPTION_HOST = get_env("OKC_DISPLAY_HOST", "127.0.0.1")
TRANSCRIPTION_PORT = get_env("OKC_DISPLAY_PORT", 5000)
SPEECH_LANG = get_env("OKC_LANG_PREPIS", "en-US")
SCENE_END_WORD = get_env("OKC_SCENE_END_WORD_PREPIS", "Showtime")

class TongueTwister:
    def __init__(self, speech_lang="en-US", exit_word="Showtime"):
        self.text_buffer = ""
        self.prev_text_buffer = ""

        self.speech_lang = speech_lang

        self.display = DisplaySender(
            TRANSCRIPTION_HOST,
            TRANSCRIPTION_PORT
        )
        self.dm = DisplayManager(self, self.display, False, "left", (10, 10))

        self.exit_word = exit_word

        self.text_buffer_window = None
        
    def run(self):
        while self.text_buffer.find(self.exit_word) == -1:
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
                continue

            self.push_to_buffer(text)
            self.dm.display()
        
        # Will return once "Showtime" is detected in the transcription.
        self.dm.clear()
        return

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


if __name__ == "__main__":
    app = TongueTwister(speech_lang=SPEECH_LANG, exit_word=SCENE_END_WORD)
    app.run()
