#-*- coding: utf-8 -*
from __future__ import division

import re
import unicodedata

from nlp.encoding import decode

BR = u'<br>'

ELLIPSES_PATTERN = r'\.\.+'
ELLIPSES_RE = re.compile(ELLIPSES_PATTERN)

NON_UNICODE_PUNCTUATION = [u'`', u'\xb4', u'\xa9', u'\xa3', u'$', u'=', u'+']
PUNCTUATION = [
    unicode(unichr(x)) for x in range(65536)
    if unicodedata.category(unichr(x)).startswith('P')
] + NON_UNICODE_PUNCTUATION
PUNCTUATION_PATTERN = r'%s|%s' % (
    ELLIPSES_PATTERN,
    u'|'.join([re.escape(p) for p in PUNCTUATION])
)
PUNCTUATION_RE = re.compile(PUNCTUATION_PATTERN, re.U)
PUNCTUATION_ES = decode("—»«¿¡•°^><|£~§„–™“”©■€®№±―…・¥♦，□►。·´▼▲")

NEWLINE_PATTERN = r'\r\n|\n|\<br\>'
NEWLINE_RE = re.compile(NEWLINE_PATTERN)

SEGMENT_PATTERN = r'%s|\.|\?|\!|%s' % (ELLIPSES_PATTERN, NEWLINE_PATTERN)
SEGMENT_RE = re.compile(SEGMENT_PATTERN)

ALPHA_START_PATTERN = r'^\w(?<=[^\d\-])'
ALPHA_START_RE = re.compile(ALPHA_START_PATTERN, re.U)

CONTINUATION_PATTERN = r'(?<!\.|\?|\!)\ ?\n'
CONTINUATION_RE = re.compile(CONTINUATION_PATTERN)

STACK_PUNCTUATION = (
    (u'(', u')'),
    (u'"', u'"'),
    (u'[', u']'),
)


class PunctuationStack(object):
    """
    >>> from corpus.punctuation import PunctuationStack
    >>> s = PunctuationStack()
    >>> s.feed(u'(')
    >>> s.pending()
    [u')']
    >>> s.feed(u'.')
    >>> s.feed(u'[')
    >>> s.pending()
    [u')', u']']
    >>> s.feed(u']')
    >>> s.feed(u')')
    >>> s.pending()
    []
    """
    def __init__(self, punctuation=STACK_PUNCTUATION):
        class CharStack(object):
            def __init__(self, start, end):
                self.start, self.end = start, end
                self.opened, self.closed = list(), list()
                if start == end:
                    self.pop = self.push

            def push(self):
                self.opened.append(self.start)

            def pop(self):
                self.closed.append(self.end)

            def pending(self):
                if self.start == self.end and len(self.opened) % 2 > 0:
                    return self.end
                elif len(self.opened) > len(self.closed):
                    return self.end

        self.operations = {}
        self.stacks = []

        for start, end in punctuation:
            self.stacks.append(CharStack(start, end))
            self.operations[start] = self.stacks[-1].push
            self.operations[end] = self.stacks[-1].pop

    def feed(self, token):
        _feed = self.operations.get(token)
        if callable(_feed):
            _feed()

    def pending(self):
        pending_punctuation = []
        for s in self.stacks:
            p = s.pending()
            if p:
                pending_punctuation.append(p)

        return pending_punctuation


def collapse(text):
    return CONTINUATION_RE.sub(' ', text)


def is_capitalized(t):
    """
    >>> from corpus.punctuation import is_capitalized
    >>> is_capitalized(u'Hello')
    True
    >>> is_capitalized(u'hello')
    False
    >>> is_capitalized(u'.')
    False
    >>> is_capitalized(u'')
    False
    """
    if ALPHA_START_RE.match(t):
        return t.startswith(t.upper()[0])
    else:
        return False


def find_abbreviations():
    import db
    from tokenizers import es
    from nltk import FreqDist

    corpus = db.connect()
    #text = '\n'.join([a['text'] for a in corpus.articles.find().limit(10)])
    text = '\n'.join([a['text'] for a in corpus.articles.find()])
    tokens = es.tokenize(text, ignore_abbreviations=True)

    fd = FreqDist()
    fd_abbr = FreqDist()
    fd_n_abbr = FreqDist()
    n_tokens = len(tokens)
    for i in range(n_tokens):
        fd.inc(tokens[i])
        if i < (n_tokens - 1) and tokens[i + 1] == u'.':
            fd_abbr.inc(tokens[i])
        else:
            fd_n_abbr.inc(tokens[i])

    adjusted = {}
    f_avg = len(fd.keys()) / fd.N()
    for t, n in fd_abbr.iteritems():
        f = fd.get(t, 0) / fd.N()
        deviation = 1 + (f - f_avg)
        adjusted[t] = n * deviation / fd_n_abbr.get(t, 1) / len(t)

    items = adjusted.items()
    items.sort(key=lambda i: i[1], reverse=True)
    for t, n in items[:100]:
        print u'%s. %f (%d, %d)' % (t, n, fd_abbr[t], fd_n_abbr.get(t, 0))
