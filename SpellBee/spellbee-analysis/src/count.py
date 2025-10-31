from math import comb

def load_wordlist(file_path):
    with open(file_path, 'r') as file:
        return set(word.strip().upper() for word in file.readlines())

def count_valid_puzzles_with_words(puzzle_size=7, min_vowels=1, wordlist_path='data/wordlists/wordlist.txt'):
    VOWELS = set('AEIOU')
    CONSONANTS = set('BCDFGHJKLMNPQRSTVWXYZ')
    wordlist = load_wordlist(wordlist_path)
    
    total = 0
    # Count combinations with at least 'min_vowels' vowels
    for vowel_count in range(min_vowels, min(puzzle_size, len(VOWELS)) + 1):
        consonant_count = puzzle_size - vowel_count
        if consonant_count <= len(CONSONANTS):
            # Calculate valid combinations
            vowel_combos = comb(len(VOWELS), vowel_count)
            consonant_combos = comb(len(CONSONANTS), consonant_count)
            total_combinations = vowel_combos * consonant_combos * puzzle_size  # center letter choices
            
            # Validate combinations against the word list
            for word in wordlist:
                if len(word) == puzzle_size and has_valid_letters(word, vowel_count, consonant_count):
                    total += total_combinations

    return total

def has_valid_letters(word, vowel_count, consonant_count):
    vowels_in_word = sum(1 for letter in word if letter in 'AEIOU')
    consonants_in_word = len(word) - vowels_in_word
    return vowels_in_word >= vowel_count and consonants_in_word >= consonant_count

# Calculate and display result
result = count_valid_puzzles_with_words()
print(f"Total possible Spell Bee puzzles with valid words: {result:,}")