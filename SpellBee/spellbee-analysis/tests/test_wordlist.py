from src.wordlist import load_wordlist, filter_wordlist

def test_load_wordlist():
    # Test loading the full wordlist
    words = load_wordlist('data/wordlists/wordlist.txt')
    assert isinstance(words, list), "Loaded wordlist should be a list"
    assert len(words) > 0, "Wordlist should not be empty"

def test_filter_wordlist():
    # Test filtering the wordlist
    words = load_wordlist('data/wordlists/wordlist.txt')
    filtered_words = filter_wordlist(words, min_length=3)
    assert all(len(word) >= 3 for word in filtered_words), "All filtered words should have at least 3 characters"
    assert len(filtered_words) <= len(words), "Filtered wordlist should not exceed original wordlist size"