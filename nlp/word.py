import re

from nlp.punctuation import PUNCTUATION_RE

WORD_RE = re.compile(r'\w+(\-\w+)?', re.U)  # Sorry, "Yahoo!"
NUMBER_RE = re.compile(r'\d*\.?\d+\.?\d*')


def is_es_word(token):
    if not WORD_RE.match(token):
        return False
    if len(token) == 1 and token not in ('a', 'e', 'o', 'u', 'y'):
        return False
    else:
        return True


LANGUAGE_WORD_LIB = {
    'ES': is_es_word,
}


def is_word(token, language=None, exclude_numbers=True):
    # Match numbers
    if NUMBER_RE.match(token):
        return False if exclude_numbers else True

    # This could be wrong; maybe some punctuation is worth glossing?
    if PUNCTUATION_RE.match(token):
        return False

    # Match words by language
    if language:
        test_word = LANGUAGE_WORD_LIB[language.upper()]
        return test_word(token)
    else:
        return True if WORD_RE.match(token) else False
