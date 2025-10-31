# Spell Bee Puzzle Analysis

This project aims to analyze and count the number of possible NYT Spell Bee puzzles using various approaches, including theoretical combinations and validation against a comprehensive word list.

## Project Structure

```
spellbee-analysis
├── notebooks
│   └── count_SB.ipynb          # Jupyter notebook for counting Spell Bee puzzles
├── data
│   └── wordlists
│       ├── wordlist.txt        # Comprehensive list of words for validation
│       └── wordlist_filtered.txt # Filtered list of words based on specific criteria
├── src
│   ├── __init__.py             # Marks the directory as a Python package
│   ├── count.py                 # Functions related to counting valid puzzles
│   ├── wordlist.py              # Handles loading and processing word lists
│   ├── validators.py            # Functions to validate generated puzzles
│   └── utils.py                 # Utility functions for various tasks
├── tests
│   ├── test_count.py            # Unit tests for counting functions
│   └── test_wordlist.py         # Unit tests for word list processing
├── requirements.txt             # Project dependencies
├── pyproject.toml               # Project configuration
├── .gitignore                   # Files and directories to ignore by Git
└── README.md                    # Documentation for the project
```

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. **Counting Puzzles**: Open the Jupyter notebook `count_SB.ipynb` to explore different methods for counting Spell Bee puzzles.
2. **Word List Processing**: Use the `src/wordlist.py` module to load and filter words from the provided word lists.
3. **Validation**: Implement validation logic using the `src/validators.py` module to ensure generated puzzles contain valid words.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.