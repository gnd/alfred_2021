import os
import re
import six
import sys
import fire
import time
import openai
import socket
import random
import subprocess
from google.cloud import translate_v2 as translate

from collections import namedtuple
Seed = namedtuple("Seed", "title prompts")

from utils import pblue, pred, pgreen, pcyan, pmagenta, pyellow, prainbow, cmagenta, ccyan, cyellow, cred
from display_sender import DisplaySender

# SEEDS_DIR = "seeds"
SEEDS_DIR = "PRIKAZY"

TEXT_TARGET_LANG = "en"
OUTPUT_LANG = "cs"

ENGINE = "davinci-instruct-beta"
MAX_TOKENS = 150
TEMPERATURE = 1

translate_client = translate.Client()

def get_question_mark_idx(text):
    #return text.find("?")
    return text.find("!")

def normalize_text(text):
    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    text = re.sub("\?", "", text)

    text = re.sub(r"[0-9]+\.", "", text)
    text = re.sub(r"_+", "", text)
    text = re.sub("&quot;", "", text)
    text = re.sub(r"[“”\"‘’]", "", text)
    text = re.sub(r"[\n ]+", " ", text)
    text = text.strip()

    return text

def cut_to_sentence_end(text):
    """Cuts off unfinished sentence."""

    endIdx = max(text.rfind("."), text.rfind("?"), text.rfind("!"))
    endIdx = endIdx if endIdx > -1 else 0
    
    return text[0: endIdx + 1]

def generate_question(prompt):
    q = ""
    while len(q) < 1:
        gpt3_resp = openai.Completion.create(
            engine=ENGINE,
            prompt=prompt,
            temperature=TEMPERATURE,
            max_tokens=64,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )

        q = gpt3_resp["choices"][0]["text"]
        #pyellow(q)
        q = normalize_text(q)
        q = cut_to_sentence_end(q)
        q = q[0:get_question_mark_idx(q) + 1]

    return q

def translate_question(q):
    # Translate generated text back to the language of speech
    out = translate_client.translate(q, target_language=OUTPUT_LANG)
    out = out["translatedText"]
    out = re.sub(r"[0-9]+\. ", "", out)
    return out

def question_me(prompt):
    q_en = normalize_text(generate_question(prompt))
    q_cs = translate_question(q_en)

    print(q_en)
    pcyan(q_cs)
    print()

def load_seeds():
    seed_files = os.listdir(SEEDS_DIR)

    seed_titles = [f.replace(".txt", "").upper() for f in seed_files] # e.g. ["EGO", "CULTURE", "HUMAN", ...]
    
    seeds = []
    for idx, fname in enumerate(seed_files):
        # Split to prompts
        prompts = []
        for raw_prompt in open(SEEDS_DIR + "/" + fname, "r").read().split("\n\n"):
            lines = raw_prompt.split("\n")
            prompt = ""
            jdx = 0
            if lines[0][0] == "[":
                prompt = "Write a list of questions about " + lines[0][1:-1] + ":\n\n"
                jdx = 1
            elif lines[0][0] == "(":
                prompt = "Write a list of questions " + lines[0][1:-1] + ":\n\n"
                jdx = 1
            else:
                #prompt = "Write a list of questions in a similar theme:\n\n"
                prompt = "Write a list of varied physical assignments for a person:\n\n"
            
            q_num = 1
            for kdx in range(jdx, len(lines)):
                prompt = prompt + str(q_num) + ". " + lines[kdx] + "\n\n"
                q_num = q_num + 1
            prompt = prompt + str(q_num) + ". "
            prompts.append(prompt)
        seeds.append(Seed(title=seed_titles[idx],prompts=prompts))

    log_seeds(seeds)

    return seeds
        
def log_seeds(seeds):
    with open("./seeds-log.txt", "w") as outf:
        for s in seeds:
            for p in s.prompts:
                outf.writelines(p)
                outf.write("\n")
                outf.write("\n")
            outf.write("\n")


def main(part=1):
    SEEDS = load_seeds()

    for seed in SEEDS:
        pred("seed: " + seed.title)
        print()
        for prompt in seed.prompts:
            print("prompt: ", prompt)
            print()

            print("questions: ")
            for _ in range(10):
                question_me(prompt)
    


if __name__ == "__main__":
    fire.Fire(main)
