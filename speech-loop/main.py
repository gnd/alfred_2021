###############################################
# WARNING: THIS CODE LEAVES MUCH TO BE DESIRED 
###############################################

from __future__ import division

import re
import sys

import six
import fire
import socket
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

from stt_loop import processMicrophoneStream

SPEECH_LANG = "cs-CZ" # a BCP-47 language tag
ALTERNATIVE_SPEECH_LANG_CODES = ["en-US", "fr-FR", "ru-RU"]

TRANSCRIPTION_HOST = "localhost"
TRANSCRIPTION_PORT = 5000

client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

sentence_buffer = []
# sock = socket.socket()
# sock.connect((TRANSCRIPTION_HOST, TRANSCRIPTION_PORT))

def textToSpeech(text):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
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
    sock.send(text.encode())
    sock.send(("\n").encode())
    sock.send(translation.encode())
    # sock.send(" ".join([*sentence_buffer, alt]).encode())
    sock.close()

def do_with_hypothesis(hypothesis):
    print(hypothesis)

    # Translate hypothesis
    normalized_transcript = hypothesis            
    if isinstance(hypothesis, six.binary_type):
        normalized_transcript = hypothesis.decode("utf-8")
                
    translation = translate_client.translate(normalized_transcript, target_language="en")
    translation = translation["translatedText"]
    
    print(translation)

    # Try send hypothesis and translation over network
    try:
        send_text(hypothesis, translation)
    except:
        print("Can't send text to {}".format(TRANSCRIPTION_HOST))
    
    # Convert translated hypothesis to speech
    fname = textToSpeech(translation)

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
                do_with_hypothesis(alt.transcript)
                # print(*sentence_buffer, alt.transcript)

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)

            # do_with_top_hypothesis()
            ##########################

        else:
            overlayed_transcript = transcript + overwrite_chars
            
            # do_with_sentence()
            ####################

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                # sock.close()
                break

            num_chars_printed = 0


def main(speech_lang=SPEECH_LANG):
    print(speech_lang) # a BCP-47 language tag
    processMicrophoneStream(speech_lang, listen_print_loop)


if __name__ == "__main__":
    main()