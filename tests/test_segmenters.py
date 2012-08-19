# -*- coding: utf-8 -*-
import unittest
import os

from nlp.tokenizers import es
from nlp.statistics.tokens import TokenClassifier
from nlp.encoding import decode

TEST_PATH = os.path.dirname(__file__)
CLASS_FILE = os.path.join(TEST_PATH, 'fixtures', 'spanish.pickle')

try:
    CLASSIFIER = TokenClassifier(CLASS_FILE)
    print 'Loaded %d classes...' % len(CLASSIFIER)
except IOError:
    from corpus.db import Text
    text = '\n'.join([t.text for t in Text.objects.all() if not t.is_empty])
    tokens = es.tokenize(text)

    CLASSIFIER = TokenClassifier()
    CLASSIFIER.train(tokens, verbose=True)
    CLASSIFIER.save(CLASS_FILE)


class TestSpanishSegmenter(unittest.TestCase):
    def test_simple(self):
        sentences = es.segment(decode("Aquí está mí primera frase. Aquí está la segunda.  Escribo frases muy sencillas."),
            raw=True, classifier=CLASSIFIER)
        self.assertEqual(sentences, [
            u'Aqu\xed est\xe1 m\xed primera frase.',
            u'Aqu\xed est\xe1 la segunda.',
            u'Escribo frases muy sencillas.',
        ])

    def test_newlines(self):
        sentences = es.segment(decode("Aquí está mí\nprimera frase."),
            raw=True, classifier=CLASSIFIER)
        self.assertEqual(sentences, [
            u'Aqu\xed est\xe1 m\xed',
            u'primera frase.',
        ])

    def test_stack(self):
        sentences = es.segment(decode("Yo respondo a eso con \"¡N... sí!\""),
            raw=True, classifier=CLASSIFIER)
        self.assertEqual(len(sentences), 1)

    def test_stack_regression(self):
        sentences = es.segment(decode("¿Qué? ¿Qué? ¿Qué?"),
            raw=True, classifier=CLASSIFIER)
        self.assertEqual(len(sentences), 3)

        sentences = es.segment(decode("¿Qué? ¡Qué! ¿Qué?"),
            raw=True, classifier=CLASSIFIER)
        self.assertEqual(len(sentences), 3)

    def test_name_continuation(self):
        sentences = es.segment(decode("Según Juan H. Vigueras, autor de \"La Europa opaca de las finanzas\", la economía global está metida en un laberinto financiero del que no sabe cómo salir."),
            raw=True, classifier=CLASSIFIER)
        self.assertEqual(len(sentences), 1)
