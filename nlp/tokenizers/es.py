#-*- coding: utf-8 -*
import re
import os

from nlp import punctuation
from nlp.encoding import decode
from nlp.statistics.tokens import Token, EMPTY_TOKEN, TokenClassifier

ROOT = os.path.dirname(__file__)
CLASS_FILE = os.path.join(ROOT, 'pickle', 'spanish.pickle')

CLASSIFIER = None
"""
try:
    CLASSIFIER = TokenClassifier(CLASS_FILE)
except IOError:
    from corpus.db import Text
    text = '\n'.join([t.text for t in Text.objects.all() if not t.is_empty])
    tokens = tokenize(text)

    CLASSIFIER = TokenClassifier()
    CLASSIFIER.train(tokens, verbose=True)
    CLASSIFIER.save(CLASS_FILE)
"""

URL_PATTERN = r"""
([a-z]{2,4}\:\/\/)?                      # Protocol
([a-z][a-z0-9_\-]*\.)+                   # Domains
[a-z]{2,4}                               # TLD
(\/[a-z0-9_\-]+)*                        # Path
(\/|\.[a-z]{2,5})?                       # Extension
(\?[a-z0-9\_\-]+\=[a-z0-9\_\-\\\%]+)?    # Parameters
(?:\&[a-z0-9\_\-]+\=[a-z0-9_\-\\\%]+)*   # Parameters
"""

TAG_PATTERN = r"\<\/?[a-z]+\>"
TAG_RE = re.compile(TAG_PATTERN)

ABBREVIATIONS = map(decode, [
    'EE.UU.',
    'Ud.', 'Uds.',
    'Sr.', 'Sra.', 'Srta.',
    'Dr.', 'Dra.', 'Prof.'
    'vs.', 'etc.',
])
ABBREVIATION_PATTERN = r'(%s|([BCDFGKLMNPQRSTVXZ]{1,2}\.)+)' % u'|'.join(
    [re.escape(a) for a in ABBREVIATIONS])
ABBREVIATION_RE = re.compile(ABBREVIATION_PATTERN)

SENTENCE_OPENERS_PATTERN = r'[%s]' % re.escape('¡¿')
SENTENCE_OPENERS_RE = re.compile(SENTENCE_OPENERS_PATTERN)

TOKEN_RE = re.compile(r"""
%s|%s|%s|                                # Abbreviations, URLs, and tags
((US)?\$|\#)?\d+([\.\,\-]\d+)?(%%|\b)|   # Numerals, money and percentages
\w+(-\w+)*(\'s|\xb4s)?|                  # Words (possibly hyphenated)
\n|\r\n|%s                               # Newlines and punctuation
""" % (
    ABBREVIATION_PATTERN,
    URL_PATTERN,
    TAG_PATTERN,
    punctuation.PUNCTUATION_PATTERN
), re.U | re.X | re.I)

TOKEN_RE_NO_ABBR = re.compile(r"""
%s|%s|                                   # Abbreviations, URLs, and tags
((US)?\$|\#)?\d+([\.\,\-]\d+)?(%%|\b)|   # Numerals, money and percentages
\w+(-\w+)*(\'s|\xb4s)?|                  # Words (possibly hyphenated)
\n|\r\n|%s                               # Newlines and punctuation
""" % (
    URL_PATTERN,
    TAG_PATTERN,
    punctuation.PUNCTUATION_PATTERN
), re.U | re.X | re.I)

STACK_PUNCTUATION = punctuation.STACK_PUNCTUATION + (
    (decode('¿'), u'?'),
    (decode('¡'), u'!'),
)


class SpanishPunctuationStack(punctuation.PunctuationStack):
    def __init__(self, punctuation=STACK_PUNCTUATION):
        super(SpanishPunctuationStack, self).__init__(
            punctuation=STACK_PUNCTUATION)


def tokenize(text, ignore_abbreviations=False, as_unicode=False):
    regex = TOKEN_RE_NO_ABBR if ignore_abbreviations else TOKEN_RE
    tokens, last = [], EMPTY_TOKEN
    for m in regex.finditer(text):
        t = Token(m.group(0), m.start(0), m.end(0))
        if t.match(punctuation.NEWLINE_RE):
            t = Token(punctuation.BR)
        if t:
            last = t
            tokens.append(t)

    if as_unicode:
        return [t.type for t in tokens]
    else:
        return tokens


def segment(text_or_tokens, raw=False, classifier=CLASSIFIER):
    tokens = tokenize(text_or_tokens) if raw else text_or_tokens
    n_tokens = len(tokens)

    # Classify tokens for abbreviation and proper noun detection
    if not classifier:
        classifier = TokenClassifier()
        classifier.train(tokens)

    sentences, cache = [], []
    closing = False
    stack = SpanishPunctuationStack()

    for i, t in enumerate(tokens):
        # Always segment on a newline
        if t.match(punctuation.NEWLINE_RE):  # Newline
            if cache:
                if raw:
                    start, end = cache[0].start, cache[-1].end
                    sentences.append(text_or_tokens[start:end])
                else:
                    sentences.append(cache)
                cache = []
                stack = SpanishPunctuationStack()
                closing = False
            continue

        stack.feed(t.type)
        cache.append(t)

        # Classify local context
        current_class = classifier.classify(t)
        next_token = tokens[i + 1] if i < n_tokens - 1 else EMPTY_TOKEN
        next_class = classifier.classify(next_token)

        # Look for the next sentence segment marker
        # The candidates are abbreviations and literal markers
        if not closing:
            if t.type.endswith(u'.') or current_class.is_abbreviation:
                # Segment on this abbreviation
                # if the the next token is capitalized and not a proper noun
                if punctuation.is_capitalized(next_token.type) \
                   and not next_class.is_proper_noun:
                    closing = True
            elif t.match(punctuation.SEGMENT_RE):
                # Segment at this literal segment marker
                # if punctuation.is_capitalized(next_token):
                closing = True

        # If we have found the sentence segment marker or reached the end,
        # check for any remaining tokens then end the sentence
        if closing or not next_token:
            if not stack.pending() or not next_token:
                if raw:
                    start, end = cache[0].start, cache[-1].end
                    sentences.append(text_or_tokens[start:end])
                else:
                    sentences.append(cache)
                cache = []
                stack = SpanishPunctuationStack()
                closing = False

    return sentences

if __name__ == '__main__':
    import corpus.text
    import corpus.db

    text = corpus.text.articles(limit=None)
    #sentences = segment(text, raw=True, classifier=None)
    #text = corpus.text.books()

    import nltk.data
    segmenter = nltk.data.load('tokenizers/punkt/spanish.pickle')
    sentences = segmenter.tokenize(text, realign_boundaries=True)
    sentences = list(set(s for s in sentences if len(s) <= 100 and '\n' not in s))
    sentences.sort(key=lambda s: len(s))

    for s in sentences:
        print s

    # db = corpus.db.connect()
    #     if 'sentences' in db.collection_names():
    #         db.drop_collection('sentences')


    # db.sentences.ensure_index('tokens')
