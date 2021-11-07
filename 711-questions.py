import os
import six
import fire
import time
import openai
import random
import subprocess
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow, prainbow

SPEECH_LANG = "cs-CZ"
TEXT_TARGET_LANG = "en"
OUTPUT_SPEECH_LANG = "cs-CZ"
OUTPUT_LANG = "cs"

ENGINE = "davinci"
MAX_TOKENS = 150
TEMPERATURE = 0.9

# [Hobbies, Good attributes, Childhood trauma]
CORPORATE_PROMPTS = [
    "1. What do you like to spend time with, when you are not working?\n\n2.Where do you like to spend you savings?\n\n3. What's your favorite sports activity?\n\n4. Do you prefer active or passive relax?\n\n5. What movie would you watch during an ideal afternoon?\n\n6. ",
    "1. What are your positive attributes?\n\n2. What are you good in?\n\n3. What fulfills you with a sense of satisfaction?\n\n4. What activity makes your time pass the fastest?\n\n5. ",
    "1. Do you wake up in the night soaked in sweat?\n\n2. Do you suffer with sleep paralysis?\n\n3. Did someone hurt you when you were a child and you couldn't defend yourself?\n\n4. Do you have a recurrent dream, whose meaning you do not understand?\n\n5. "
]

# [Food, Physical pleasure, Images of pain]
PLEASURE_PROMPTS = [
    "1. What is your favorite fastfood?\n\n2. How do you prepare potatos?\n\n3. Pepper or salt?\n\n4. ",
    "1. What material can please you the most?\n\n2. What gives you goosebumps\n\n3. Where do you caress yourself?\n\n4. ",
    "1. What is worse, to burn or to drown?\n\n2. Have you ever seen kittens drowning in a bag?\n\n3. Can you imagine putting pins under somebody's fingernails?\n\n4. ",
]

# [Pop music, Fashion, Power]
EGO_PROMPT = [
    "1. Do you think it is right that Britney Spears is sui juris?\n\n2. Does Micheal Jackson's music deserve to be forsaken?\n\n3. Are you fond of Jennifer Lopez's butt?\n\n4. ",
    "1. What is your most beautiful piece of clothing?\n\n2. What was the most you spended on a piece of clothing?\n\n3. ",
    "1. Have you ever desired for the admiration of the people around you?\n\n2. Have you ever boasted with something that wasn't really your own credit?\n\n3. Does it please you to meet with people that are not as successful as you?\n\n4. What was the most you have given to charity?\n\n5. Does it please you when somebody who is more successful and smart than you, is less attractive than you?\n\n6. Do you have the number of likes visibility feature turned on on Instagram?\n\n7. ",
]

# [Poetry, Society, Eugenetics]
INTELLECT_PROMPT = [
    "1. Who are your favorite artists?\n\n\2. If you could live your life once again, what would be your job?\n\n3. Where does talent come from?\n\n4. ",
    "1. What job has the biggest spiritual contribution to society?\n\n2. ",
    "1. Two people are drowning, one of them is a genius and the other is a poet, you can save one of them, who would it be?\n\n2. There are two people drowning, one of them is a theatre director, the other is an ordinary person, you can save only one of them, who would it be?\n\n3. There are two people drowning, one of them is a genius and the other is a worker, you can save only one of them, who would it be?\n\n4. Imagine you traveled back in time to an austrian town, Braunau am Inn in 1891. Next to you is sleeping two year old boy. There is nobody other around and closeby is a furious river. What do you do?     The little boy is Adolf Hitler.\n\n5. "
]

THEATRE_PROMPT = [
    "1. Who is your favorite actor or actress and why?\n\n2. If you should make a theatre performance, what would it be about?\n\n3. Do you think it should be allowed to eat and drink in the theate?\n\n4. ",
    "1. If somebody filmed a movie about your life, what actor would play you?\n\n2. With what movie or book character do you personalize with?\n\n3. ",
    "1. Should the theatre be financed from taxes?\n\n2. Should the church be financed from taxes?\n\n3. ",
]

HUMAN_PROMPT = [
    "Ask questions as if you are leading a job interwiev.\n\n1. Can you speak about your personal strengths?\n\n2. Where do you see yourself in ten years?\n\n3. What positive changes can you birng to this company?\n\n4. ",
    "Ask questions about the necessity of human work.\n\n1. Why is work so central for human life?\n\n2. Why do humans build their identity around the work they do?\n\n3. Why do people work so much?\n\n4. Why do people have to work to have money?\n\n5. ",
    "Ask questions about how to be human.\n\n1. What do you feel when you feel pain?\n\n2. What do you feel when you are reading a poem about love?\n\n3. Why do humans have to die?\n\n4. ",
    "Ask questions about ethical dilemmas.\n\n1. Do animals have rights?\n\n2. Religion freedom or sexual freedom?\n\n3. ",
]

CULTURE_PROPMPT = [
    "Ask questions about culture.\n\n1. What's your favorite theatre genre?\n\n2. How many LP records do you have?\n\n3. Whats your favorite book older than 19. century?\n\n4. ",
    "Ask questions about love.\n\n1. What is your ideal partner type?\n\n2. How do you imagine your ideal date?\n\n3. Do you believe in eternal love?\n\n4. ",
    "Ask questions about perversions.\n\n1. Have you ever thought about eating human meat?\n\n2. Do you sometimes imagine how you torture your enemies?\n\n3. What punishment would you propose for an old man who raped an 8 year old girl?\n\n4. "
]

SEEDS = [
    CORPORATE_PROMPTS,
    PLEASURE_PROMPTS,
    EGO_PROMPT,
    INTELLECT_PROMPT,
    THEATRE_PROMPT,
]

QUESTIONS_PER_SEED = [
    5, 5, 5, 5, 5
]

SECONDS_TO_ANSWER = [
    5, 3, 1
]

SECONDS_FOR_ENTRANCE = 1

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
        effects_profile_id=['medium-bluetooth-speaker-class-device'],
        audio_encoding=texttospeech.AudioEncoding.MP3,
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

    subprocess.run(
        ["mplayer", "output.mp3"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return

def generate_question(prompt):
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

        q = gpt3_resp["choices"][0]["text"]
        q = normalize_text(q)
        q = cut_to_sentence_end(q)
        q = q[0:get_question_mark_idx(q) + 1]
        question = q

    return question

def translate_question(question):
    # Translate generated text back to the language of speech
    out_text = translate_client.translate(question, target_language=OUTPUT_LANG)
    out_text = out_text["translatedText"]
    return out_text

def question_me(prompt):
    question_text = generate_question(prompt)

    # translate question to CS
    question_text_cs = translate_question(question_text)

    text_to_speech(question_text_cs)
    
def question_person(name, prompt):
    question_text = generate_question(prompt)

    question_text = translate_question(question_text)

    question_text = name + ", " + question_text

    text_to_speech(question_text)

def question_single_person_loop(name, seed):
    text_to_speech(random.choice(["Hey,"]) + " " + name + ".")

    pgreen("Asking question in")
    for x in range(SECONDS_FOR_ENTRANCE):
        pgreen(SECONDS_FOR_ENTRANCE - x)
        time.sleep(1)

    input_cmd = ""
    while input_cmd != "X":
        if random.randint(0, 10) < 3:
            text_to_speech(random.choice(["Zajímavé.", "Ahá", "Jasně.", "Ani nepokračuj.", "Velice zajímavé.", "Mm, to jsem nečekela.", "To jsem nečekela."]))
        
        prompt = get_prompt(seed)
        # prompt = "Create a list of questions:\n" + prompt
        pmagenta("Generating question...")
        question_me(prompt)
        pcyan("Enter \"X\" to end cycle or press enter for another question.")
        input_cmd = input()

def question_single_person(name, prompt):
    question_person(name, prompt)

def get_prompt(SEED):
    idx = random.randint(0, len(SEED) - 1)
    return SEED[idx]

def main():
    NAMES = [
        "Jakub",
        "Karolína",
        "Eliška",
        "Alica",
        "Jolana",
        "Anna",
        "Lenka",
        "Anastázia",
        "Hana",
        "Hanka",
        "Lucia",
    ]
    NAMES_TEMP = [
        "Jakub",
        "Karolína",
        "Eliška",
        "Alica",
        "Jolana",
        "Anna",
        "Lenka",
        "Anastázia",
        "Hana",
        "Hanka",
        "Lucia",
    ]
    SEED = HUMAN_PROMPT

    input_cmd = ""
    while input_cmd != "Z":
        if len(NAMES_TEMP) == 0:
            pred("All people were asked, moving to second part...")
            break

        name = random.choice(NAMES_TEMP)
        NAMES_TEMP.remove(name)
        pmagenta(f"Proceeding to question {name}")
        question_single_person_loop(name, SEED)
        pyellow("Press \"Z\" to proceed to second part or Enter for another person...")
        input_cmd = input()
        

    pred("Second part")
    os.system('play -nq -t alsa synth {} sine {}'.format(1, 440))

    while True:
        prompt = get_prompt(SEED)
        name = random.choice(NAMES)
        pmagenta("Generating question for somebody at random.")
        question_single_person(name, prompt)
        pyellow("Press enter for another question...")
        input() # don't ask another question until requested


if __name__ == "__main__":
    fire.Fire(main)