# -*- coding: utf-8 -*-
import unittest

from nlp.encoding import decode
from nlp.word import is_word
from nlp.punctuation import PUNCTUATION_ES


class TestWord(unittest.TestCase):
    def test_simple(self):
        for word in map(decode, ['bloquedor', 'socio-politico', 'política']):
            self.assertEqual(is_word(word), True)

    def test_punctuation(self):
        for i, p in enumerate(list(PUNCTUATION_ES)):
            self.assertEqual(is_word(p), False)

    def test_numbers(self):
        for number in ('1', '123', '.123', '0.123', '1.', '1.23'):
            self.assertEqual(is_word(number), False)
            self.assertEqual(is_word(number, exclude_numbers=False), True)

    def test_es_words(self):
        for letter in 'bcdfghijklmnpqrstvwxz':
            self.assertEqual(is_word(letter, language='es'), False)
