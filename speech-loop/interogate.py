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
    "Create a question that asks about my horse's dental hygiene",
    "Create a question that asks about the secret life of house animals",
]

QUESTIONS_PER_PROMPTS = [
    3, 3, 3
]

SECONDS_TO_ANSWER = [
    3, 2, 1
]

SECONDS_AFTER_ROUND = 5

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

def question_me(prompt, seconds):
    question_text = generate_question(prompt)

    # translate question to CS
    question_text_cs = translate_question(question_text)

    # Print translated text for debugging
    print(question_text)
    print(question_text_cs)

    text_to_speech(question_text_cs)
    
    for x in range(seconds):
        print(x)
        time.sleep(1)
    
def main():
    while True:
        print("Next round starts in...")
        for x in range(SECONDS_AFTER_ROUND):
            print(x)
            time.sleep(1)

        print()

        for i, prompt in enumerate(PROMPTS):
            print(prompt)
            print(i)
            seconds_to_answer = SECONDS_TO_ANSWER[i]
            num_questions = QUESTIONS_PER_PROMPTS[i]
            print(seconds_to_answer)
            print(num_questions)

            for j in range(num_questions):
                print("Question number ", j)
                print(prompt)
                print(seconds_to_answer)
                question_me(prompt, seconds_to_answer)

if __name__ == "__main__":
    fire.Fire(main)