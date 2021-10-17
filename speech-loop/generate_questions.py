import six
import time
import openai
import random
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

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

def get_question_mark_idx(text):
    return text.find("?")

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
    # See: https://googleapis.dev/java/google-cloud-texttospeech/latest/com/google/cloud/texttospeech/v1/AudioConfig.html
    # For audio profiles see: https://cloud.google.com/text-to-speech/docs/audio-profiles#tts-audio-profile-python
    audio_config = texttospeech.AudioConfig(
        speaking_rate=0.9, # 0.5 - 4.0
        effects_profile_id=['medium-bluetooth-speaker-class-device'],
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

    playsound(fname)
    return

def generate_question():
    question = ""
    while len(question) < 1:
        gpt3_resp = openai.Completion.create(
            engine="davinci-instruct-beta",
            # prompt="Create a list of questions for my interview with a science fiction author:\n\n1.",
            # prompt="Create a question for my interview with a science fiction author:\n\n1.",
            # prompt="Create a random question for my interview with a retired punk motocyclist that contains at least 9 words:\n\n1.",
            prompt="Create a random question that asks about a really specific and absurd detail of my personal life:\n\n1.",
            temperature=0.9,
            max_tokens=64,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=["\n\n"]
        )
    
        q = gpt3_resp["choices"][0]["text"]
        q = normalize_text(q)
        q = cut_to_sentence_end(q)
        q = q[0:get_question_mark_idx(q) + 1]
        print(q)
        question = q

    return question

def translate_question(question):
    # Translate generated text back to the language of speech
    out_text = translate_client.translate(question, target_language=OUTPUT_LANG)
    out_text = out_text["translatedText"]
    return out_text

def question_me():
    question_text = generate_question()

    # translate question to CS
    question_text_cs = translate_question(question_text)

    # Print translated text for debugging
    print(question_text)
    print(question_text_cs)

    text_to_speech(question_text_cs)
    
    # Pause for `PAUSE_SECONDS` seconds
    PAUSE_SECONDS = 3 
    for x in range(PAUSE_SECONDS):
        print(x)
        time.sleep(1)
    

if __name__ == "__main__":
    while True:
        question_me()
