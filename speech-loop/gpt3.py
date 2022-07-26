import os
import time
import openai
import random
import subprocess
import ConfigParser

from termcolor import colored
from google.cloud import texttospeech

import utils
from utils import pblue, pred, pgreen, pcyan, pyellow, prainbow, beep, concat, sanitize_translation, elapsed_time, normalize_text, recognize_stop_word

# Load variables from config
settings = os.path.join(sys.path[0], '../settings.ini')
config = ConfigParser.ConfigParser()
config.read(settings)

# Assign config variables
OPENAI_MODEL = config.get('openai', 'MODEL')
MAX_TOKENS_STORIES = config.get('openai', 'MAX_TOKENS_STORIES')
TEMPERATURE_STORIES = config.get('openai', 'TEMPERATURE_STORIES')
MAX_SUCC_BLANKS = config.get('openai', 'MAX_SUCC_BLANKS')

class GPT3Client:
    def __init__(self, app, translate_client, engine=OPENAI_MODEL, input_lang="cs", output_speech_lang="cs-CZ"):
        self.app = app
        self.engine = engine
        self.input_lang = input_lang
        self.output_speech_lang = output_speech_lang
        self.translate_client = translate_client
        self.tts_client = texttospeech.TextToSpeechClient()

    def set_engine(self, engine):
        self.engine = engine

    def translate(self, x, target_lang):
        start = time.time()
        print("Translating hypothesis...")
        
        x = self.translate_client.translate(x, target_language=target_lang)
        x = x["translatedText"] 
        x = sanitize_translation(x)
        
        end = time.time()
        print("(translation)   ", colored(elapsed_time(start, end), "magenta"))

        return x

    def feed(self, x):
        if len(x) == 0:
            # self.dm.display("Hypothesis empty")
            pred("\nHypothesis empty\n")
            return

        # Signal GPT3 start-up
        os.system('play -nq -t alsa synth {} sine {}'.format(0.3, 440)) # Beep sound to signal end of recording
        pred(f"GPT-3 input: {x}")

        self.log(x)

        # Translate hypothesis from Czech to English.
        if self.input_lang != "en-US":
            x = self.translate(x, "en")

        pyellow(x + "\n")
        print("Sending text to GPT-3...")
        # self.dm.display(f"set_gpt: {x}")

        # Generate continuation
        y = ""
        num_blanks = 0
        max_blanks = 3
        while len(y.strip()) < 1 and num_blanks < MAX_SUCC_BLANKS:
            start = time.time()
            resp = openai.Completion.create(
                engine=self.engine,
                prompt=x,
                max_tokens=MAX_TOKENSS_STORIES,
                temperature=TEMPERATURE,
            )
            end = time.time()
        
            y = resp["choices"][0]["text"]
            y = normalize_text(y)
            y = sanitize_translation(y)

            # Print response stats
            prainbow(
                ["(GPT-3 response)", "w"],
                ["   " + elapsed_time(start, end), "m"],
                [f'   {len(resp["choices"][0]["text"])} chars', "c"],
                ["   {:.3f} tokens".format(len(resp["choices"][0]["text"]) / 4), "y"],
                [f'   {len(y)} chars clean', "g"],
                ["   {:.3f} tokens clean".format(len(y) / 4), "r"],
                ["   {:.3f} tokens total".format((len(y) + len(x)) / 4), "b"]
            )

            if len(y) < 1:
                print("Received blank response :(")
                num_blanks = num_blanks + 1

        if num_blanks == MAX_SUCC_BLANKS:
            y = random.choice([
                "Try again.",
                "Sorry, can you please try again.",
                "I don't understand. Please try again.",
                "Sorry, what?"
            ])
        else:
            pblue(y)

        if self.output_speech_lang != "en-US":
            y = self.translate_response(y)
            y = sanitize_translation(y)

        self.app.gpt3_resp = y

        self.text_to_speech(y)

        self.log("".join([
                f"(GPT-3 response)",
                "   " + elapsed_time(start, end),
                f'   {len(resp["choices"][0]["text"])} chars',
                "   {:.3f} tokens".format(len(resp["choices"][0]["text"]) / 4),
                f'   {len(y)} chars clean',
                "   {:.3f} tokens clean".format(len(y) / 4),
                "   {:.3f} tokens total".format((len(y) + len(x)) / 4),
                f"   {len(y.split())} words"
            ]))

        self.play_audio()

        os.system('play -nq -t alsa synth {} sine {}'.format(0.3, 440)) # Beep sound to signal end of response
        return y

    def _text_to_speech(self, text):
        """
        Synthesizes `text` into audio.
    
        The audio file is stored on disk as "output.mp3".
        """
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code=self.output_speech_lang)

        # Plz note we are asking for speaking rate every time
        config.read(settings)
        SPEAKING_RATE = config.get('text-to-speech', 'SPEAKING_RATE')
        audio_config = texttospeech.AudioConfig(
            speaking_rate=SPEAKING_RATE, # 0.75, # 0.5 - 4.0
            effects_profile_id=['medium-bluetooth-speaker-class-device'],
            audio_encoding=texttospeech.AudioEncoding.MP3,
            pitch=0, # 20 for dying patient voice
        )
        response = self.tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        fname = "output.mp3"
        with open(fname, "wb") as out:
            out.write(response.audio_content)
        return fname

    def text_to_speech(self, text):
        print("Converting text to speech...")
        # send_simple_msg("Converting text to speech...")
        # Convert continuation to speech
        start = time.time()
        self._text_to_speech(text)
        end = time.time()
        print("(text to speech)   ", colored(elapsed_time(start, end), "magenta"))
        # send_simple_msg(f"(text to speech)    {elapsed_time(start, end)}")

    def play_audio(self):
        print("Playing audio...")
        subprocess.run(
            ["mplayer", "output.mp3"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def translate_response(self, response):
        print("Translating response...")
        # send_simple_msg("Translating GPT-3 response...")
        start = time.time()
        res = self.translate_client.translate(response, target_language=utils.getLangCode(self.output_speech_lang))
        res = res["translatedText"]
        end = time.time()
        print("(translation)   ", colored(elapsed_time(start, end), "magenta"))
        # send_simple_msg(f"(translation)    {elapsed_time(start, end)}")
        return res

    def log(self, msg):
        self.app.dm.display_action(msg)

