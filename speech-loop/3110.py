from __future__ import division

import sys
import fire
import openai
import random
import socket
import subprocess
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

import utils
from stt_loop import processMicrophoneStream

SPEECH_LANG = "en-US"
OUTPUT_SPEECH_LANG = "en-US"

ENGINE = "davinci-instruct-beta"
MAX_TOKENS = 200
TEMPERATURE = 0.9

client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

def pick_voice_randomly():
    return random.choice([texttospeech.SsmlVoiceGender.MALE, texttospeech.SsmlVoiceGender.FEMALE])

def text_to_speech(text):
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
        print('Audio content written to file "output.mp3"')
    return fname

def do_with_hypothesis(hypothesis):
    if utils.recognize_stop_word(hypothesis):
        return

    print("Final hypothesis is:")
    print(hypothesis)

    print("Sending text to GPT-3...")
    # Generate continuation
    response = ""
    while len(response) < 1:
        gpt3_resp = openai.Completion.create(
            engine=ENGINE,
            prompt=hypothesis,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            stop=["\n\n"]
        )
        out_text = gpt3_resp["choices"][0]["text"]
        out_text = utils.normalize_text(out_text)
        out_text = utils.cut_to_sentence_end(out_text)  
    
        # Postprocess translated text
        out_text = out_text.lstrip(". ")               # remove leftover dots and spaces from the beggining
        response = out_text.replace("&quot;","")       # remove "&quot;"

    print(response)
    print("Converting text to speech...")
    # Convert continuation to speech
    fname = text_to_speech(response)

    print("Playing audio...")
    subprocess.run(["mplayer", "output.mp3"])

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
            sys.stdout.flush()
            num_chars_printed = len(transcript)
        else:
            do_with_hypothesis(transcript + overwrite_chars)
            break

def main(speech_lang=SPEECH_LANG):
    while True:
        processMicrophoneStream(speech_lang, listen_print_loop)


if __name__ == "__main__":
    main()
