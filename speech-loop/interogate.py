import six
import fire
import time
import openai
import random
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

SPEECH_LANG = "cs-CZ"
TEXT_TARGET_LANG = "en"
OUTPUT_SPEECH_LANG = "cs-CZ"
OUTPUT_LANG = "cs"

ENGINE = "davinci"
MAX_TOKENS = 150
TEMPERATURE = 0.9

PROMPTS = [
    "Create a random question that asks about a really specific and absurd detail of my personal life",
    "Create a question about your own hygiene that is slightly uncomfortable.",
    # "Create a question that asks about my horse's dental hygiene",
    # "Create a question that asks about the secret life of house animals",
    "Imagine you are a police officer interogating a suspect. Ask a question about the suspects intimate life."
]

QUESTIONS_PER_PROMPTS = [
    1, 1, 1
]

SECONDS_TO_ANSWER = [
    2, 1.5, 0.75
]

SPEECH_RATE = [
    1.1, 1.277, 1.5
]

SPEECH_PITCH = [
    -10, -13, -17
]

SPEECH_VOLUME = [
    0, 8, 16
]

SECONDS_AFTER_ROUND = 1

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

def text_to_speech(text, speech_rate, speech_pitch, speech_volume):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=OUTPUT_SPEECH_LANG, ssml_gender=pick_voice_randomly()
    )

    audio_config = texttospeech.AudioConfig(
        speaking_rate=speech_rate, # 0.5 - 4.0
        effects_profile_id=['medium-bluetooth-speaker-class-device'],
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=speech_pitch, # 20 for dying patient voice
        volume_gain_db=speech_volume,
    )

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

def generate_question(prompt):
    prompt = prompt + ":\n\n1."
    question = ""
    while len(question) < 1:
        gpt3_resp = openai.Completion.create(
            engine="davinci-instruct-beta",
            prompt=prompt,
            temperature=0.9,
            max_tokens=64,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=["\n\n"]
        )
    
        print(gpt3_resp)
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

def question_me(prompt, seconds, speech_rate, speech_pitch, speech_volume):
    question_text = generate_question(prompt)

    # translate question to CS
    question_text_cs = translate_question(question_text)

    # Print translated text for debugging
    print(question_text)
    print(question_text_cs)

    text_to_speech(question_text_cs, speech_rate, speech_pitch, speech_volume)
    
    time.sleep(seconds)
    # for x in range(seconds):
    #     print(x)
    #     time.sleep(1)
    
def main():
    while True:
        print("Next round starts in...")
        for x in range(SECONDS_AFTER_ROUND):
            print(x)
            time.sleep(1)

        for i, prompt in enumerate(PROMPTS):
            seconds_to_answer = SECONDS_TO_ANSWER[i]
            num_questions = QUESTIONS_PER_PROMPTS[i]
            speech_rate = SPEECH_RATE[i]
            speech_pitch = SPEECH_PITCH[i]
            speech_volume = SPEECH_VOLUME[i]

            for j in range(num_questions):
                question_me(prompt, seconds_to_answer, speech_rate, speech_pitch, speech_volume)

if __name__ == "__main__":
    fire.Fire(main)