import random

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
    
    
sentence = 'Colorless green ideas sleep furiously'
sentence_versions = shuffle_sentence(sentence.split())
for version in sentence_versions:
    print(version)
