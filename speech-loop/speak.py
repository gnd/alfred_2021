from __future__ import division

import re
import sys
import six
import fire
import openai
import random
import socket
import subprocess
import ConfigParser

from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

from stt_loop import processMicrophoneStream

# Load variables from config
settings = os.path.join(sys.path[0], '../settings.ini')
config = ConfigParser.ConfigParser()
config.read(settings)

OUTPUT_SPEECH_LANG = "en-GB"
TRANSCRIPTION_HOST = config.get('display', 'DISPLAY_HOST')
TRANSCRIPTION_PORT = config.get('display', 'DISPLAY_PORT')


client = texttospeech.TextToSpeechClient()
translate_client = translate.Client()

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
    # Plz note we are asking for speaking rate every time
    config.read(settings)
    SPEAKING_RATE = config.get('text-to-speech', 'SPEAKING_RATE')

    audio_config = texttospeech.AudioConfig(
        speaking_rate=SPEAKING_RATE, # 0.5 - 4.0
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
    sock.send(translation.encode())
    sock.close()

def processKeyboardInput():
    instructions = input("Awaiting instructions:")

    # Convert instructions to speech
    fname = text_to_speech(instructions)

    # Play the audio
    subprocess.run(
        ["mplayer", fname],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    print()


def main():
    while True:
        processKeyboardInput()

if __name__ == "__main__":
    main()
