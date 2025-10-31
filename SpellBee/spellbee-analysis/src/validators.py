def load_wordlist(file_path):
    with open(file_path, 'r') as file:
        words = {line.strip().upper() for line in file if line.strip()}
    return words

def validate_puzzle(puzzle, wordlist):
    puzzle_set = set(puzzle)
    return any(word in wordlist for word in puzzle_set)

def filter_valid_words(puzzle, wordlist):
    valid_words = []
    for word in wordlist:
        if all(letter in puzzle for letter in word):
            valid_words.append(word)
    return valid_words