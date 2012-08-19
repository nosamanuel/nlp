import nltk.data

segmenter = nltk.data.load('tokenizers/punkt/spanish.pickle')


def segment(text):
    return segmenter.tokenize(text)
