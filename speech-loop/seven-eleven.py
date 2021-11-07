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
import subprocess
from termcolor import colored
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

import utils
from stt_loop import processMicrophoneStream
from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow, prainbow

SPEECH_LANG = "en-US"
OUTPUT_SPEECH_LANG = "en-US"

ENGINE = "davinci-instruct-beta"
MAX_TOKENS = 200
TEMPERATURE = 0.9

MAX_SUCC_BLANKS = 3

TEXT_BUFFER = ""
PREV_BUFFER = ""

TRANSCRIPTION_HOST = "127.0.0.1"
# TRANSCRIPTION_HOST = "192.168.70.133"
TRANSCRIPTION_PORT = 5000

INSTRUCT_NICK = "dog"
NORMAL_NICK = "fish"

client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

def translate(text, in_lang, out_lang):
    pass

def send_text(text):
    global TEXT_BUFFER
    sock = socket.socket()
    try:
        sock.connect((TRANSCRIPTION_HOST, TRANSCRIPTION_PORT))
        sock.send((TEXT_BUFFER + " " + text).encode())
    except:
        pred(f"Cannot connect to {TRANSCRIPTION_HOST}:{TRANSCRIPTION_PORT}")
    finally:
        sock.close()

def send_simple_msg(msg):
    sock = socket.socket()
    try:
        sock.connect((TRANSCRIPTION_HOST, TRANSCRIPTION_PORT))
        sock.send(msg.encode())
    except:
        pred(f"Cannot connect to {TRANSCRIPTION_HOST}:{TRANSCRIPTION_PORT}")
    finally:
        sock.close()

def recognize_engine_switch(text):
    global ENGINE
    m = re.search(rf"\b(engine ({NORMAL_NICK}|{INSTRUCT_NICK}))\b", text, re.I)
    if m:
        engine = m.group(2)
        if engine == NORMAL_NICK:
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting engine - Davinci )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_engine normal")
            ENGINE = "davinci"
            return True
        if engine == INSTRUCT_NICK:
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting engine - Instruct )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_engine instruct")
            ENGINE = "davinci-instruct-beta"
            return True
    return False

def recognize_language_switch(text):
    global SPEECH_LANG
    cz = "Czech"
    en = "English"
    m = re.search(rf"\b(({cz}|{en}) language)\b", text, re.I)
    if m:
        lang = m.group(2)
        if lang == cz:
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - Czech )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang czech")
            SPEECH_LANG = "cs-CZ"
            return True
        if lang == en:
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - English )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang english")
            SPEECH_LANG = "en-US"
            return True
    return False

def recognize_output_switch(text):
    global OUTPUT_SPEECH_LANG
    cz = "cappuccino"
    en = "zebra"
    m = re.search(rf"\b(({cz}|{en}))\b", text, re.I)
    if m:
        lang = m.group(2)
        if lang == cz:
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting output language - Czech )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_out_lang czech")
            OUTPUT_SPEECH_LANG = "cs-CZ"
            return True
        if lang == en:
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting output language - English )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_out_lang english")
            OUTPUT_SPEECH_LANG = "en-US"
            return True
    return False

def recognize_temperature(text):
    global TEMPERATURE
    m = re.search(r"\b(temperature ([0-9]+))\b", text, re.I)
    if m:
        temperature = int(m.group(2))
        if temperature >= 0 and temperature <= 100:
            temperature = temperature / 100
            pmagenta(f",.-~*´¨¯¨`*·~-.¸-( Setting temperature to {temperature} )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg(f"set_temp {temperature}")
            TEMPERATURE = temperature
            return True
    return False

def chop_endword(text):
    m = re.search(r"\b(.*)((I'm out)|(peace out))\b", text, re.I)
    if m:
        return m.group(1)
    return text

def recognize_speech_end(text):
    if re.search(r"\b(.*)((I'm out)|(peace out))\b", text, re.I):
        return True
    return False

def recognize_repeat(text):
    if re.search(r"\b(.*)(repeat)\b", text, re.I):
        return True
    return False

def recognize_delete(text):
    if re.search(r"\b(delete)\b", text, re.I):
        return True
    return False

def recognize_backspace(text):
    if re.search(r"\b(backspace)\b", text, re.I):
        return True
    return False

def delete_word(text):
    text = text.split()
    if len(text) > 0:
        return " ".join(text[:-1])
    else:
        return text

def handle_deletes():
    global TEXT_BUFFER
    num_dels = TEXT_BUFFER.count("delete") + TEXT_BUFFER.count("Delete")
    # Delete `num_dels` words and additionally all "delete"s.
    for x in range(num_dels * 2):
        TEXT_BUFFER = delete_word(TEXT_BUFFER)

def handle_backspaces():
    global TEXT_BUFFER
    num_bckspcs = TEXT_BUFFER.count("backspace") + TEXT_BUFFER.count("Backspace")
    TEXT_BUFFER = TEXT_BUFFER.replace("backspace", "").replace("Backspace", "").strip()
    TEXT_BUFFER = TEXT_BUFFER[:-num_bckspcs]

def stopword_cleanup():
    send_simple_msg("set_exit")
    time.sleep(1)
    send_simple_msg("")

def push_to_buffer(text):
    global TEXT_BUFFER
    TEXT_BUFFER = (TEXT_BUFFER + " " + text).strip()

def reset_buffer():
    global TEXT_BUFFER
    global PREV_BUFFER
    PREV_BUFFER = TEXT_BUFFER
    TEXT_BUFFER = ""

def pick_voice_randomly():
    return random.choice([texttospeech.SsmlVoiceGender.MALE, texttospeech.SsmlVoiceGender.FEMALE])

def text_to_speech(text):
    global OUTPUT_SPEECH_LANG
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=OUTPUT_SPEECH_LANG, ssml_gender=pick_voice_randomly()
    )
    audio_config = texttospeech.AudioConfig(
        speaking_rate=0.9, # 0.5 - 4.0
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

def do_with_hypothesis(hypothesis):
    if len(hypothesis) == 0:
        pred("\nHypothesis empty\n")
        return

    os.system('play -nq -t alsa synth {} sine {}'.format(0.3, 440)) # Beep sound to signal end of recording

    # Translate hypothesis from Czech to English.
    if SPEECH_LANG == "cs-CZ":
        start = time.time()
        print("Translating hypothesis...")
        hypothesis = translate_client.translate(hypothesis, target_language="en")
        hypothesis = hypothesis["translatedText"] 
        end = time.time()
        print("(translation)   ", colored(utils.elapsed_time(start, end), "magenta"))

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

    # Translate GPT-3 output from English to Czech.
    if OUTPUT_SPEECH_LANG == "cs-CZ":
        print("Translating response...")
        start = time.time()
        response = translate_client.translate(response, target_language="cs")
        response = response["translatedText"]
        end = time.time()
        print("(translation)   ", colored(utils.elapsed_time(start, end), "magenta"))

    print("Converting text to speech...")
    # Convert continuation to speech
    start = time.time()
    fname = text_to_speech(response)
    end = time.time()
    print("(text to speech)   ", colored(utils.elapsed_time(start, end), "magenta"))

    print("Playing audio...")
    subprocess.run(
        ["mplayer", "output.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print()

def listen_print_loop(responses):
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
            send_text(transcript)
            sys.stdout.flush()
            num_chars_printed = len(transcript)
        else:
            return (transcript + overwrite_chars + "\n")

def main(speech_lang=SPEECH_LANG):
    global TEXT_BUFFER
    global SPEECH_LANG

    while True:
        if TEXT_BUFFER == "":
            pcyan("Listening :)\n")

        # Blocks to process audio from the mic. This function continues
        # once the end of the utterance has been recognized.        
        text = processMicrophoneStream(SPEECH_LANG, listen_print_loop)
        
        # Print "complete utterance" as recognized by the STT service.
        pgreen(text)

        # Engine swithing        
        if recognize_engine_switch(text):
            continue

        # Temperature changing
        if recognize_temperature(text):
            continue

        if recognize_language_switch(text):
            TEXT_BUFFER = ""
            continue

        if recognize_output_switch(text):
            TEXT_BUFFER = ""
            continue

        # Stop word clears the text
        if utils.recognize_stop_word(text):
            stopword_cleanup()
            TEXT_BUFFER = ""
            continue

        # Generate another response for the previous seed
        if recognize_repeat(text):
            TEXT_BUFFER = PREV_BUFFER
            do_with_hypothesis(TEXT_BUFFER)
            continue
    
        if recognize_delete(text):
            push_to_buffer(text)
            handle_deletes()
            send_simple_msg(TEXT_BUFFER)
            continue

        if recognize_backspace(text):
            push_to_buffer(text)
            handle_backspaces()
            send_simple_msg(TEXT_BUFFER)
            continue

        # Once speech end is recognized, text is sent to GPT-3
        if recognize_speech_end(text):
            text = chop_endword(text)
            push_to_buffer(text)
            send_simple_msg(TEXT_BUFFER)
            do_with_hypothesis(TEXT_BUFFER)
            reset_buffer()
        else:
            push_to_buffer(text)
            send_simple_msg(TEXT_BUFFER)



if __name__ == "__main__":
    main()
