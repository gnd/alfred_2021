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
from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow, prainbow, beep

SPEECH_LANG = "en-US"
OUTPUT_SPEECH_LANG = "en-US"

ENGINE = "davinci-instruct-beta"
MAX_TOKENS = 200
TEMPERATURE = 0.9

MAX_SUCC_BLANKS = 3

TEXT_BUFFER = ""
PREV_BUFFER = ""

GPT3_RESP = ""

TRANSCRIPTION_HOST = "127.0.0.1"
TRANSCRIPTION_PORT = 5000

DEBUG_HOST = "127.0.0.1"
DEBUG_PORT = 5432

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

class State:
    def __init__(
        self,
        speech_lang=SPEECH_LANG,
        output_speech_lang=OUTPUT_SPEECH_LANG,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        engine=ENGINE,
    ):
        self.speech_lang = speech_lang
        self.output_speech_lang = output_speech_lang
        
        self.buffer = ""
        self.prev_buffer = ""
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.engine = engine

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

    kw_instruct = "engine instruct" if SPEECH_LANG != "cs-CZ" else "motor instrukce"
    kw_normal = "engine normal" if SPEECH_LANG != "cs-CZ" else "motor normální"

    m = re.search(rf"\b({kw_normal}|{kw_instruct})\b", text, re.I)
    if m:
        engine = m.group(1)
        if engine == kw_normal:
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting engine - Davinci )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_engine normal")
            ENGINE = "davinci"
            beep(0.3)
            return True
        if engine == kw_instruct:
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting engine - Instruct )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_engine instruct")
            ENGINE = "davinci-instruct-beta"
            beep(0.3)
            return True
    return False

def recognize_language_switch(text):
    global SPEECH_LANG

    if SPEECH_LANG == "cs-CZ":
        kw_in = "vstup anglicky"
        if re.search(rf"\b({kw_in})\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - English )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang english")
            SPEECH_LANG = "en-US"
            beep(0.3)
            return True
        if re.search(rf"\b(vstup francouzsky)\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - French )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang french")
            SPEECH_LANG = "fr-FR"
            beep(0.3)
            return True
        if re.search(rf"\b(vstup rusky)\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - Russian )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang russian")
            SPEECH_LANG = "ru-RU"
            beep(0.3)
            return True
        if re.search(rf"\b(vstup čínsky)\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - Chinese )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang chinese")
            SPEECH_LANG = "cmn-CN"
            beep(0.3)
            return True
        else:
            return False
    elif SPEECH_LANG == "en-US": # This is more tricky
        if re.search(rf"\b(input (Czech|check|chess|chair))\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - Czech )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang czech")
            SPEECH_LANG = "cs-CZ"
            beep(0.3)
            return True
        if re.search(rf"\b(input (french|French))\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - French )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang french")
            SPEECH_LANG = "fr-FR"
            beep(0.3)
            return True
        if re.search(rf"\b(input (russian|Russian))\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - Russian )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang russian")
            SPEECH_LANG = "ru-RU"
            beep(0.3)
            return True
        if re.search(rf"\b(input (chinese|Chinese))\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - Chinese )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang chinese")
            SPEECH_LANG = "cmn-Cn"
            beep(0.3)
            return True
        else:
            return False
    elif SPEECH_LANG == "fr-FR":
        if re.search(rf"\b(saisir (anglais|Anglais))\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - English )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang english")
            SPEECH_LANG = "en-US"
            beep(0.3)
            return True
        if re.search(rf"\b(saisir (tchèque|Tchèque))\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - Czech )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang cs-CZ")
            SPEECH_LANG = "cs-CZ"
            beep(0.3)
            return True
        if re.search(rf"\b(saisir (russe|Russe))\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - Russian )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang ru-RU")
            SPEECH_LANG = "ru-RU"
            beep(0.3)
            return True
        if re.search(rf"\b(saisir (chinoise|Chinoise))\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - Chinese )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_lang cmn-CN")
            SPEECH_LANG = "cmn-CN"
            beep(0.3)
            return True
        if re.search(rf"\b(Michael Jackson)\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - English )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("recognized Michael Jackson")
            send_simple_msg("set_lang english")
            SPEECH_LANG = "en-US"
            beep(0.3)
            return True
        return False    
    elif SPEECH_LANG == "ru-RU":
        if re.search(rf"\b(Michael Jackson)\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - English )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("recognized Michael Jackson")
            send_simple_msg("set_lang english")
            SPEECH_LANG = "en-US"
            beep(0.3)
            return True
    elif SPEECH_LANG == "cmn-CN":
        if re.search(rf"\b(Michael Jackson)\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting language - English )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("recognized Michael Jackson")
            send_simple_msg("set_lang english")
            SPEECH_LANG = "en-US"
            beep(0.3)
            return True
    return False

def recognize_output_switch(text):
    global OUTPUT_SPEECH_LANG

    if SPEECH_LANG == "cs-CZ":
        kw_cs = "výstup česky"
        kw_en = "výstup anglicky"
        m = re.search(rf"\b({kw_cs}|{kw_en})\b", text, re.I)
        if m:
            lang = m.group(1)
            if lang[:-4] == kw_cs[:-4]:
                pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting output language - Czech )-,.-~*´¨¯¨`*·~-.¸")
                send_simple_msg("set_out_lang czech")
                OUTPUT_SPEECH_LANG = "cs-CZ"
                beep(0.3)
                return True
            if lang[:-4] == kw_en[:-4]:
                pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting output language - English )-,.-~*´¨¯¨`*·~-.¸")
                send_simple_msg("set_out_lang english")
                OUTPUT_SPEECH_LANG = "en-US"
                beep(0.3)
                return True
        return False
    elif SPEECH_LANG == "en-US": 
        if re.search(rf"\b(output English)\b", text, re.I):
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting output language - English )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_out_lang english")
            OUTPUT_SPEECH_LANG = "en-US"
            beep(0.3)
            return True
        m = re.search(rf"\b(output (Czech|check|chess|chair))\b", text, re.I)
        if m:
            pmagenta(",.-~*´¨¯¨`*·~-.¸-( Setting output language - Czech )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg("set_out_lang czech")
            OUTPUT_SPEECH_LANG = "cs-CZ"
            beep(0.3)
            return True
    return False

def recognize_temperature(text):
    global TEMPERATURE

    kw_temp = "temperature" if SPEECH_LANG != "cs-CZ" else "teplota"

    m = re.search(rf"\b({kw_temp} ([0-9]+))\b", text, re.I)
    if m:
        temperature = int(m.group(2))
        if temperature >= 0 and temperature <= 100:
            temperature = temperature / 100
            pmagenta(f",.-~*´¨¯¨`*·~-.¸-( Setting temperature to {temperature} )-,.-~*´¨¯¨`*·~-.¸")
            send_simple_msg(f"set_temp {temperature}")
            TEMPERATURE = temperature
            beep(0.3)
            return True
    return False

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

def recognize_repeat(text):
    kw_repeat = "repeat" if SPEECH_LANG != "cs-CZ" else "znovu"
    
    if re.search(rf"\b(.*)({kw_repeat})\b", text, re.I):
        pyellow("> repeat")
        return True
    return False

def recognize_delete(text):
    kw_del = "delete" if SPEECH_LANG != "cs-CZ" else "smazat"
    
    if re.search(rf"\b({kw_del})\b", text, re.I):
        pyellow("> delete")
        return True
    return False

def recognize_backspace(text):
    if re.search(r"\b(backspace)\b", text, re.I):
        pyellow("> backspace")
        return True
    return False

def recognize_continue(text):
    kw_cont = "continue" if SPEECH_LANG != "cs-CZ" else "pokračuj"

    if re.search(rf"\b({kw_cont})\b", text, re.I):
        pyellow("> cont")
        return True
    return False

def recognize_info(text):
    kw_info = "info"
    if re.search(rf"\b({kw_info})\b", text, re.I):
        pyellow("> info")
        return True
    return False

def recognize_help(text):
    kw_help = "help" if SPEECH_LANG != "cs-CZ" else "pomoc|nápověda"
    if re.search(rf"\b({kw_help})\b", text, re.I):
        pyellow("> help")
        return True
    return False

def recognize_word(word, text):
    if re.search(rf"\b({word})\b", text, re.I):
        return True
    return False

def recognize_words(words, text):
    ws = "|".join(words)
    if re.search(rf"\b({ws})\b", text, re.I):
        return True
    return False

def send_info():
    info = f"Engine: {ENGINE}\nTemperature: {TEMPERATURE}\nInput lang: {SPEECH_LANG}\nOutput lang: {OUTPUT_SPEECH_LANG}"
    send_simple_msg(info)

def send_help():
    help_msg = [
        "     ,.-~*´¨¯¨`*·~-.¸-_   repeat carbon   _-,.-~*´¨¯¨`*·~-.¸",
        "",
        "Anglicky                           Cesky",
        "",
        "engine normal/instruct   motor normální/instrukce",
        "temperature 0-100           teplota 0-100",
        "input Czech                      vstup anglicky",
        "output Czech/English     výstup česky/anglicky",
        "I'm out/peace out              díky/jedeš",
        "exit/quit/sorry                   exit/quit/sorry",
        "repeat                                 znovu",
        "delete                                 smazat",
        "backspace                          backspace",
        "continue                             pokračuj",
        "info                                      info/nápověda"
    ]
    help_msg = "\n".join(help_msg)
    send_simple_msg(help_msg)

def convert_cs_period(text):
    if SPEECH_LANG != "cs-CZ":
        return False
    
    return re.sub(rf"\b(tečka)\b", ".", text)

def convert_cs_question_mark(text):
    if SPEECH_LANG != "cs-CZ":
        return text
    
    return re.sub(rf"\b(otazník)\b", "?", text)

def convert_cs_exclamation_mark(text):
    if SPEECH_LANG != "cs-CZ":
        return text

    return re.sub(rf"\b(vykřičník)\b", "!", text)

def delete_word(text):
    """Deletes the last word from `text`."""
    text = text.split()
    if len(text) > 0:
        return " ".join(text[:-1])
    else:
        return text

def handle_deletes():
    """
    Deletes last words from the text buffer.
    
    Deletes one word from the end for each "delete" occurence
    in the buffer.

    "delete"/"Delete" in English.
    "smazat"/"Smazat" in Czech.
    """
    global TEXT_BUFFER
    
    kw_del = ["delete", "Delete"] if SPEECH_LANG == "en-US" else ["smazat", "Smazat"]
    
    num_dels = TEXT_BUFFER.count(kw_del[0]) + TEXT_BUFFER.count(kw_del[1])
    # Delete `num_dels` words and additionally all "delete"s.
    for x in range(num_dels * 2):
        TEXT_BUFFER = delete_word(TEXT_BUFFER)

def handle_backspaces():
    """
    Deletes the last characted of the text buffer for each
    occurrence of "backspace" or "Backspace".
    """
    global TEXT_BUFFER
    num_bckspcs = TEXT_BUFFER.count("backspace") + TEXT_BUFFER.count("Backspace")
    TEXT_BUFFER = TEXT_BUFFER.replace("backspace", "").replace("Backspace", "").strip()
    TEXT_BUFFER = TEXT_BUFFER[:-num_bckspcs]

def stopword_cleanup():
    """Clears the remote screen."""
    send_simple_msg("set_exit")
    time.sleep(0.5)
    send_simple_msg("")

def push_to_buffer(text):
    """Adds `text` to the nasty global buffer."""
    global TEXT_BUFFER
    TEXT_BUFFER = (TEXT_BUFFER + " " + text).strip()

def reset_buffer():
    """
    Resets the global text buffer.
    
    Also stores the text buffer for potential later reuse through "repeat".
    Used after the end-word has been detected and the text has been processed
    by GPT-3.
    """
    global TEXT_BUFFER
    global PREV_BUFFER
    PREV_BUFFER = TEXT_BUFFER
    TEXT_BUFFER = ""

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
    text_to_speech(response)
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

def listen_print_loop(responses):
    """
    Sends intermediate transcriptions to remote display.

    This function is executed for each intermediate response
    from the Google Clout speech-to-text API.
    """
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
    global GPT3_RESP

    while True:
        if TEXT_BUFFER == "":
            pcyan("Listening :)\n")

        # Blocks to process audio from the mic. This function continues
        # once the end of the utterance has been recognized.        
        text = processMicrophoneStream(SPEECH_LANG, listen_print_loop)
        
        # Print "complete utterance" as recognized by the STT service.
        pgreen(text)

        if SPEECH_LANG == "cs-CZ":
            text = convert_cs_period(text)
            text = convert_cs_question_mark(text)
            text = convert_cs_exclamation_mark(text)

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
            send_simple_msg("gpt-3 end")
            time.sleep(0.5)
            send_simple_msg("")
            reset_buffer()
            continue

        if recognize_continue(text):
            TEXT_BUFFER = PREV_BUFFER + " " + GPT3_RESP
            do_with_hypothesis(TEXT_BUFFER)
            reset_buffer()
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

        if recognize_info(text):
            send_info()
            continue

        if recognize_help(text):
            send_help()
            continue

        # Once speech end is recognized, text is sent to GPT-3
        if recognize_speech_end(text):
            text = chop_endword(text)
            push_to_buffer(text)
            send_simple_msg(TEXT_BUFFER)
            do_with_hypothesis(TEXT_BUFFER)
            send_simple_msg("gpt-3 end")
            time.sleep(0.5)
            send_simple_msg("")
            reset_buffer()
        else:
            push_to_buffer(text)
            send_simple_msg(TEXT_BUFFER)

if __name__ == "__main__":
    main()
