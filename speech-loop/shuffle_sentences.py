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
TRANSCRIPTION_HOST = "127.0.0.1"
TRANSCRIPTION_PORT = 5000

client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

def normalize_text(text):
    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")
    return text
    
#
# takes a an array of words of the input sentence
#
def shuffle_sentence(words):
    # return an array of all shuffles of a sentence
    sentence_versions = []
    
    # walk over the sentence and shuffle from word[i] to end
    for i in range(len(words)):
        shuffled = words[i:]
        random.shuffle(shuffled)
        new_sentence = " ".join(words[:i]) + " " + " ".join(shuffled)
        sentence_versions.append(new_sentence.strip().lower().capitalize())
    return sentence_versions

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
    # See: https://googleapis.dev/java/google-cloud-texttospeech/latest/com/google/cloud/texttospeech/v1/AudioConfig.html
    # For audio profiles see: https://cloud.google.com/text-to-speech/docs/audio-profiles#tts-audio-profile-python
    audio_config = texttospeech.AudioConfig(
        speaking_rate=1.4, # 0.5 - 4.0
        effects_profile_id=['medium-bluetooth-speaker-class-device'],
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=3, # 20 for dying patient voice
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
    transcript = normalize_text(hypothesis)
    transcript_shuffled = shuffle_sentence(transcript.split())
    versions = ". ".join(transcript_shuffled)
    
    # Print translated text for debugging
    print(versions)
    
    # Convert continuation to speech
    fname = text_to_speech(versions)

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
