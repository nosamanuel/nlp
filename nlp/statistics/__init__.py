from __future__ import division

import string

from nltk import FreqDist


def ngrams(tokens, n=1):
    """
    Generate the set of n adjacent tokens.
    """
    n_tokens = len(tokens)
    for first, t in enumerate(tokens):
        last = first + n
        if last <= n_tokens:
            yield tokens[first:last]


def bigrams(tokens):
    """
    Generate the set of 2 adjacent tokens.
    """
    return ngrams(tokens, n=2)


def trigrams(tokens):
    """
    Generate the set of 3 adjacent tokens.
    """
    return ngrams(tokens, n=3)


def collocations(tokens):
    """
    Return a list of bigrams that occur together above chance probability.
    """
    fd_unigrams = FreqDist()
    for u in tokens:
        fd_unigrams.inc(u.lower())

    fd_bigrams = FreqDist()
    for b in ngrams(tokens, n=2):
        fd_bigrams.inc(tuple(map(string.lower, b)))

    candidates = []
    for b, n in fd_bigrams.items():
        f_b = n / fd_unigrams[b[0]]
        f_w2 = fd_unigrams[b[1]] / fd_unigrams.N()
        if f_b > f_w2:  # also, log lambda > threshold?
            candidates.append((b, n))

    candidates.sort(key=lambda i: i[1], reverse=True)

    return candidates


if __name__ == '__main__':
    import corpus.db
    import corpus.tokenizers.es

    db = corpus.db.connect()
    text = u'\n'.join(a['text'] for a in db.articles.find())
    tokens = corpus.tokenizers.es.tokenize(text)
    collocations = collocations(tokens)

    for b, n in collocations[:100]:
        print b, n
