from src.count import count_valid_puzzles
from src.wordlist import load_wordlist

def test_count_valid_puzzles():
    # Load the word list for validation
    wordlist = load_wordlist('data/wordlists/wordlist.txt')
    
    # Test cases for counting valid puzzles
    assert count_valid_puzzles(puzzle_size=7, min_vowels=1) > 0, "Should return a positive count for valid puzzles"
    assert count_valid_puzzles(puzzle_size=7, min_vowels=2) > 0, "Should return a positive count for valid puzzles with at least 2 vowels"
    assert count_valid_puzzles(puzzle_size=7, min_vowels=3) > 0, "Should return a positive count for valid puzzles with at least 3 vowels"
    
    # Additional tests can be added based on specific criteria or expected outcomes
    # Example: Check if the count is less than the theoretical maximum
    theoretical_max = 4604600  # From the first approach
    assert count_valid_puzzles(puzzle_size=7, min_vowels=1) < theoretical_max, "Count should be less than the theoretical maximum"