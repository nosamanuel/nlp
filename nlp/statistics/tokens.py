from __future__ import division
import re
import pickle

from nlp import punctuation
from nlp.encoding import encode

ALPHA_START_PATTERN = r'^\w(?<=[^\d\-])'
ALPHA_START_RE = re.compile(ALPHA_START_PATTERN, re.U)

ABBREVIATION_PATTERN = r'^[A-Z]\.|[BCDFGKLMNPQRSTVXZ]{1,2}\.$'
ABBREVIATION_RE = re.compile(ABBREVIATION_PATTERN)

ABBREVIATION_THRESHOLD = 0.788
PROPER_NOUN_THRESHOLD = 0.9


class Token(object):
    def __init__(self, type, start=None, end=None):
        self.type = type
        self.start = start
        self.end = end

    def __nonzero__(self):
        return True if self.type else False

    def __unicode__(self):
        return self.type

    def match(self, regex):
        return regex.match(self.type)

EMPTY_TOKEN = Token(u'')


class TokenClass(object):
    def __init__(self):
        self.count = 0
        self.upper_count = 0
        self.abbr_count = 0
        self.length = 0
        self.types = set()

    def record(self, token,
        left_context=EMPTY_TOKEN, right_context=EMPTY_TOKEN):
        self.types.add(token.type)

        self.count += 1
        if punctuation.is_capitalized(token.type):
            self.upper_count += 1
        if token.type.startswith(u'.') == False and \
           (right_context.type == u'.' or token.type.endswith(u'.')):
            self.abbr_count += 1

    @property
    def capitalized(self):
        """Returns the first capitalized type for this class if it exists"""
        for t in self.types:
            if punctuation.is_capitalized(t):
                return t

        return self.normalized

    @property
    def normalized(self):
        """Returns the lower-case normalized type for this class"""
        return self.normalize()

    def normalize(self):
        return list(self.types)[0].lower()

    @property
    def p_abbreviation(self):
        """Probability that this token class is an abbreviation"""
        return self.abbr_count / self.count * 2.0 / len(self.normalized)

    @property
    def p_proper_noun(self):
        """Probability that this token class is a proper noun"""
        return self.upper_count / self.count

    @property
    def is_abbreviation(self):
        if self.count > 1:
            return self.p_abbreviation > ABBREVIATION_THRESHOLD
        else:
            return 0

    @property
    def is_proper_noun(self):
        """Probability that this token class is a proper noun"""
        if self.count > 1:
            return self.p_proper_noun > PROPER_NOUN_THRESHOLD
        else:
            return False


class TokenClassifier(object):
    token_class = TokenClass

    def __init__(self, file_name=None):
        self.classes = {}
        self.count = None
        if file_name:
            with open(file_name) as f:
                self.classes = pickle.load(f)

    def train(self, tokens, verbose=False):
        self.count = None
        n_tokens = len(tokens)
        for i in range(n_tokens):
            t = tokens[i]
            left_context = tokens[i - 1] if i > 0 else EMPTY_TOKEN
            right_context = tokens[i + 1] if i < n_tokens - 1 else EMPTY_TOKEN

            key = self.normalize(t)
            self.classes.setdefault(key, TokenClass())
            self.classes[key].record(t, left_context, right_context)

        if verbose:
            print '-' * 80
            print 'Abbreviations'
            print '-' * 80
            for c in self.abbreviations:
                print encode(c.capitalized), c.p_abbreviation, c.count

            print '-' * 80
            print 'Proper nouns'
            print '-' * 80
            for c in self.proper_nouns:
                print encode(c.capitalized), c.p_proper_noun, c.count

            print '-' * 80

    def save(self, file_name):
        with open(file_name, 'w') as f:
            pickle.dump(self.classes, f)

    def __len__(self):
        if not self.count:
            self.count = sum(c.count for c in self.classes.values())
        return self.count

    def classify(self, token):
        key = self.normalize(token)
        try:
            return self.classes[key]
        except KeyError:
            self.classes[key] = TokenClass()
            self.classes[key].record(token)
            return self.classes[key]

    def normalize(self, token):
        return token.type.lower()

    @property
    def abbreviations(self):
        return [c for c in self.classes.values() if c.is_abbreviation]

    @property
    def proper_nouns(self):
        return [c for c in self.classes.values() if c.is_proper_noun]


if __name__ == '__main__':
    import corpus.text
    from corpus.tokenizers import es

    text = corpus.text.articles(limit=None)
    tokens = es.tokenize(text)
    c = TokenClassifier()
    c.train(tokens)
    for t in c.abbreviations:
        print t.capitalized
