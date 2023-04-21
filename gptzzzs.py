import os
import urllib.request
import json
import random
import re

file_name = "synonyms"
zaibacu_url = "https://raw.githubusercontent.com/zaibacu/thesaurus/master/en_thesaurus.jsonl"
finnlp_url = "https://raw.githubusercontent.com/FinNLP/synonyms/master/src.json"
adjective_url = "https://raw.githubusercontent.com/rgbkrk/adjectives/master/index.js"
common_words_url = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/20k.txt"

def get_zaibacu_synonyms():
    response = urllib.request.urlopen(zaibacu_url)
    data = response.read()
    text = data.decode('utf-8')

    lines = text.split("\n")
    word_synonyms = [json.loads(line) for line in lines if line]
    print("Loaded file from remote URL")

    # Create word-synonyms dictionary

    return {entry['word']: entry['synonyms'] for entry in word_synonyms}

def get_finnlp_synonyms():
    response = urllib.request.urlopen(finnlp_url)
    data = response.read()
    text = data.decode('utf-8')

    synonyms = json.loads(text)
    print("Loaded synonym file from remote URL")

    # Create word-synonyms dictionary

    for key, value in synonyms.items():
        synonyms[key] = []
        for k, v in value.items():
            synonyms[key] += [word for word in v[1:]]
        if ("v" in synonyms[key]):
            synonyms[key].remove("v")
        if ("s" in synonyms[key]):
            synonyms[key].remove("s")
        if ("r" in synonyms[key]):
            synonyms[key].remove("r")
        if ("a" in synonyms[key]):
            synonyms[key].remove("a")
        if ("n" in synonyms[key]):
            synonyms[key].remove("n")

    return synonyms

def load_synonyms(collection):
    if os.path.exists("{}_synonyms.json".format(collection)):
        with open("{}_synonyms.json".format(collection), "r") as f:
            return json.load(f)

    if collection == 'zaibacu':
        synonyms = get_zaibacu_synonyms()
    elif collection == 'finnlp':
        synonyms = get_finnlp_synonyms()
    else:
        raise ValueError('Invalid collection')
    
    with open("{}_synonyms.json".format(collection), "w") as f:
        f.write(json.dumps(synonyms))
    
    return synonyms

# TODO: Save them

def get_common_words():
    response = urllib.request.urlopen(common_words_url)
    data = response.read()
    text = data.decode('utf-8')

    return text.split("\n")

def get_adjectives():
    if os.path.exists("adjectives.json"):
        with open("adjectives.json", "r") as f:
            text = f
            adjectives = json.load(text)
    else:
        response = urllib.request.urlopen(adjective_url)
        data = response.read()
        text = data.decode('utf-8')

        lines = text.split("\n")
        adjectives = []

        for i in range(1, len(lines) - 2):
            adjective = re.search('\'(.*)\',', lines[i]).group(1)
            adjectives.append(adjective)
        print("Loaded adjective file from remote URL")

        dict_file_name = "adjectives.json"
        with open(dict_file_name, "w") as f:
            f.write(json.dumps(adjectives))
            print("Saved adjective dictionary to local folder")
    
    return adjectives


class GPTZZZ:
    def __init__(self, ignore_quotes=False, use_common_words=True):
        self.ignore_quotes = ignore_quotes

        zaibacu = load_synonyms('zaibacu')
        finnlp = load_synonyms('finnlp')

        if use_common_words:
            self.common_words = get_common_words()
            zaibacu = self.filter_common_words(zaibacu)
            finnlp = self.filter_common_words(finnlp)
        else:
            self.common_words = None
        
        self.zaibacu = zaibacu
        self.finnlp = finnlp

        self.adjectives = get_adjectives()
    
    def filter_common_words(self, synonyms):
        new_synonyms = {}
        for key, value in synonyms.items():
            updated_value = []
            for synonym in value:
                if synonym in self.common_words:
                    updated_value.append(synonym)
            if updated_value:
                new_synonyms[key] = updated_value
        
        return new_synonyms

    def replace_synonyms(self, text, synonyms, synonym_probability):
        words = text.split(" ")

        new_words = ""

        num_words = int(len(words) * synonym_probability)
        chosen_indices = random.sample(range(len(words)), num_words)

        quotation_count = 0
        for i in range(len(words)):
            if "\"" in words[i]:
                quotation_count += words[i].count("\"")

            if i in chosen_indices and (quotation_count % 2 == 0 or not self.ignore_quotes):
                word = words[i]
                endswith = ""
                if word.endswith((".", ",", "!", "'", "?", ":", ";")):
                    endswith = word[len(word) - 1]
                    word = word[:-1]

                if len(word) > 3 and word in synonyms.keys() and len(synonyms[word]) != 0 and random.random():
                    word = random.choice(synonyms[word])

                new_words = "{}{}{}".format(new_words, word, endswith)
                if i != len(words) - 1:
                    new_words = "{}{}".format(new_words, " ")
            else:
                new_words = "{}{}".format(new_words, words[i])
                if i != len(words) - 1:
                    new_words = "{} ".format(new_words)
        
        return new_words

    def replace_adjectives(self, text, adjective_probability):
        words = text.split(" ")

        new_words = ""

        quotation_count = 0
        emphasis_words = ["very", "very", "very", "really", "really", "really", "extremely", "quite", "so", "too", "very", "really"]
        dont_change = False
        for i in range(len(words)):
            if "\"" in words[i]:
                quotation_count += words[i].count("\"")

            if words[i] in emphasis_words and words[i+1] and words[i+1] in self.adjectives and (quotation_count % 2 == 0 or not self.ignore_quotes):
                if random.random() < adjective_probability:
                    dont_change = True
                    continue

            if words[i] in self.adjectives and not dont_change and (quotation_count % 2 == 0 or not self.ignore_quotes):
                if random.random() < adjective_probability:
                    emp_word = random.choice(emphasis_words)
                    new_words = "{}{} {}".format(new_words, emp_word, words[i])
                    if i != len(words) - 1:
                        new_words = "{} ".format(new_words)
                    continue

            dont_change = False
            new_words = "{}{}".format(new_words, words[i])
            if i != len(words) - 1:
                new_words = "{} ".format(new_words)

        return new_words

    def apply(self, text, collection='both', synonym_probability=0.5, adjective_probability=0.5):
        if collection == 'zaibacu':
            synonyms = self.zaibacu
        elif collection == 'finnlp':
            synonyms = self.finnlp
        elif collection == 'both':
            synonyms = self.zaibacu
            
            for key, value in self.finnlp.items():
                if key in synonyms:
                    if value not in synonyms[key]:
                        synonyms[key].append(value)
                else:
                    synonyms[key] = [value]
        else:
            raise ValueError('Invalid collection')

        text = self.replace_synonyms(text, synonyms, synonym_probability=synonym_probability)
        text = self.replace_adjectives(text, adjective_probability=adjective_probability)

        return text
