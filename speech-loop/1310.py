from __future__ import division

import re
import sys
import six
import fire
import openai
import random
import socket
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

from stt_loop import processMicrophoneStream

# SPEECH_LANG = "cs-CZ" # a BCP-47 language tag
# SPEECH_LANG = "zh-CN"
SPEECH_LANG = "cs-CZ"
TEXT_TARGET_LANG = "en"
ALTERNATIVE_SPEECH_LANG_CODES = ["en-US", "fr-FR", "ru-RU"]
OUTPUT_SPEECH_LANG = "cs-CZ"
OUTPUT_LANG = "cs"

# TRANSCRIPTION_HOST = "localhost"
TRANSCRIPTION_HOST = "192.168.220.207"
TRANSCRIPTION_PORT = 5000

ENGINE = "davinci"
MAX_TOKENS = 150
TEMPERATURE = 0.9

client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

def normalize_text(text):
    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")
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
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code=OUTPUT_SPEECH_LANG, ssml_gender=pick_voice_randomly()
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=0, # 20 for dying patient voice
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    fname = "output.mp3"
    # The response's audio_content is binary.
    with open(fname, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')
    return fname

def send_text(text, translation):
    sock = socket.socket()
    sock.connect((TRANSCRIPTION_HOST, TRANSCRIPTION_PORT))
    # sock.send(text.encode())
    # sock.send(("\n").encode())
    sock.send(translation.encode())
    sock.close()

def do_with_hypothesis(hypothesis):
    print(hypothesis)

    # Translate hypothesis
    normalized_transcript = normalize_text(hypothesis)

    translation = translate_client.translate(normalized_transcript, target_language=TEXT_TARGET_LANG)
    translation = translation["translatedText"]    
    print(translation)

    # Generate continuation
    gpt3_resp = openai.Completion.create(
        engine=ENGINE, prompt=translation, max_tokens=MAX_TOKENS, temperature=TEMPERATURE
    )
    continuation = gpt3_resp["choices"][0]["text"]
    continuation = normalize_text(continuation)
    continuation = cut_to_sentence_end(continuation)
    # Translate generated text back to the language of speech
    out_text = translate_client.translate(continuation, target_language=OUTPUT_LANG)
    out_text = out_text["translatedText"]

    # Send hypothesis and translation over network
    # send_text(hypothesis, translation)

    # Convert continuation to speech
    fname = text_to_speech(out_text)

    # Play utterance
    playsound(fname)


def do_with_top_hypothesis(hypothesis):
    do_with_hypothesis(hypothesis)

def do_with_sentence(sentence):
    do_with_hypothesis(sentence)

def listen_print_loop(responses):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0
    for response in responses:

        if not response.results:
            continue

        for i, res in enumerate(response.results):
            for j, alt in enumerate(res.alternatives):
                pass
                # do_with_hypothesis(alt.transcript)
                # print(*sentence_buffer, alt.transcript)

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)

            # do_with_top_hypothesis(transcript + overwrite_chars + "\r")
            ##########################

        else:
            overlayed_transcript = transcript + overwrite_chars
            
            do_with_sentence(transcript + overwrite_chars)
            break
            ####################

            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                # sock.close()
                break

            num_chars_printed = 0


def main(speech_lang=SPEECH_LANG):
    while True:
        processMicrophoneStream(speech_lang, listen_print_loop)


if __name__ == "__main__":
    main()
