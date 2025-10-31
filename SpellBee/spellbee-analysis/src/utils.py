def load_wordlist(file_path):
    """Load words from a given file and return a set of words."""
    with open(file_path, 'r') as file:
        words = {line.strip().upper() for line in file if line.strip()}
    return words

def filter_wordlist(wordlist, min_length=3):
    """Filter the wordlist to include only words of a minimum length."""
    return {word for word in wordlist if len(word) >= min_length}

def is_valid_word(word, valid_words):
    """Check if a word is in the set of valid words."""
    return word in valid_words

def format_wordlist(wordlist):
    """Format the wordlist for display or output."""
    return sorted(wordlist)

def save_filtered_wordlist(filtered_words, output_path):
    """Save the filtered wordlist to a specified output file."""
    with open(output_path, 'w') as file:
        for word in filtered_words:
            file.write(f"{word}\n")