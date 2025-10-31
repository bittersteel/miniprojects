def load_wordlist(file_path):
    with open(file_path, 'r') as file:
        words = {line.strip().upper() for line in file if line.strip()}
    return words

def filter_wordlist(wordlist, min_length=3):
    return {word for word in wordlist if len(word) >= min_length}

def is_valid_word(word, wordlist):
    return word in wordlist

def get_filtered_wordlist(file_path, min_length=3):
    wordlist = load_wordlist(file_path)
    return filter_wordlist(wordlist, min_length)