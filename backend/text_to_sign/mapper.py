import os
from utils.helpers import clean_text

# Project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Absolute path to signs folder
SIGNS_FOLDER = os.path.join(BASE_DIR, "signs")

UNKNOWN_GIF = "unknown.gif"


def text_to_sign_mapper(text):
    """
    Convert text into a list of sign GIF filenames.
    Priority:
    1) Full word GIF
    2) Letter-by-letter GIFs
    3) unknown.gif fallback
    """

    text = clean_text(text)
    result = []

    if not text:
        return [UNKNOWN_GIF]

    for word in text.split():
        word_gif = f"{word}.gif"
        word_path = os.path.join(SIGNS_FOLDER, word_gif)

        # Full word GIF exists
        if os.path.exists(word_path):
            result.append(word_gif)
            continue

        # Spell letter-by-letter
        letters_added = False
        for ch in word:
            if ch.isalpha():
                letter_gif = f"{ch}.gif"
                letter_path = os.path.join(SIGNS_FOLDER, letter_gif)

                if os.path.exists(letter_path):
                    result.append(letter_gif)
                    letters_added = True

        # Nothing matched → unknown.gif
        if not letters_added:
            result.append(UNKNOWN_GIF)

    return result