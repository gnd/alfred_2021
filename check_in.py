"""Generates a check-in contribution."""

import openai
from playsound import playsound
from google.cloud import speech
from google.cloud import texttospeech
from google.cloud import translate_v2

PROMPTS = [
    "I woke up pretty late today. I had two eggs for breakfast then I brushed my teeth and rode a bike to come here.",
    "So I woke up at eleven, because it's the weekend, right? I did a lot of stuff today, but basically I didn't do anything. So that's the truth, haha.",
    "I woke up, then I rode my bike to the National Theatre for this rehearsal. The guy, Honza, put on the smart glove and did \"Rrrraaaa\". Then I went home and played with some synthesizers. Then I came here.",
    "I woke up pretty late, just in time for this corporate thing called \"stand-up\" which we have to do every day at 10:30. It's a meeting where everybody has to say what they've been working on. It's a complete waste of time. I spent the whole day working basically.",
    "Hi guys, so, I had a pretty basic day. I had a lecture in the morning then I went to work. At lunch I read this book that Peter recommended as, which we weren't supposed to read yet. I really liked it.",
    "Hey everybody, yeah, thanks for the recommendation. I've found this song today, called \"Smrt Letny\", have you heard it? It's really nuts, I think it fits nicely into the theme of the performance. Can I have the ashtray?",
    "Damn, it's freezing here. Anyway, I had a really nice day, I finally tried out the historical tram ride across Prague that I've dreamt about for so long. I'm really excited about today's rehearsal.",
    "Hey guys, sorry, I'm a little bit tired today, thanks for the pizza, Peter. So, I was walking my dog when I saw this squirell and it looked at me and it looked right into my eyes. Can you believe that? And it also had a nut in its mouth. I've never seen that, have you?"
]

def text_to_speech(text, speech_language="cs-CZ"):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=speech_language, ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    audio_config = texttospeech.AudioConfig(
        speaking_rate=0.9,
        effects_profile_id=['medium-bluetooth-speaker-class-device'],
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=0,
    )
    client = texttospeech.TextToSpeechClient()
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    print("Writing audio file...")
    with open("checkin.mp3", "wb") as out:
        out.write(response.audio_content)

    print("Playing audio...")
    playsound("checkin.mp3")

def translate(text, target_language="CS"):
    translate_client = translate_v2.Client()
    translation = translate_client.translate(text, target_language=target_language)
    return translation["translatedText"]

def generate_check_in_text():
    prompt = "\nHow are you?\n".join(PROMPTS)
    prompt = "How are you?\n" + prompt + "\nHow are you?\n"
    out = ""
    while len(out) < 1:
        resp = openai.Completion.create(
            engine="davinci",
            prompt=prompt,
            temperature=0.9,
            max_tokens=300,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=["\n"]
        )    
        out = resp["choices"][0]["text"]

    return out

def check_in():
    print("Generating check-in confession...")
    check_in_text = generate_check_in_text()

    print("Translating to Czech...")
    check_in_text_cs = translate(check_in_text, "CS")

    print("Converting to audio...")
    text_to_speech(check_in_text_cs)

if __name__ == "__main__":
    check_in()