# -*- coding: utf-8 -*-
import unittest

from nlp.encoding import decode
from nlp.tokenizers import es


class TestSpanishTokenizer(unittest.TestCase):
    def test_simple(self):
        tokens = es.tokenize(decode("¿A qué le temen los afganos?"), as_unicode=True)
        self.assertEqual(tokens, [
            u'\xbf', u'A', u'qu\xe9',
            u'le', u'temen', u'los', u'afganos', u'?'])

    def test_compounds(self):
        tokens = es.tokenize(decode("Desde allí, consigna el documento, los aviones C-17 podrían alcanzar casi todo el continente sudamericano sin necesidad de reabastecimiento de combustible."), as_unicode=True)
        self.failUnless(u'C-17' in tokens)
        self.failUnless(decode('allí') in tokens)

        tokens = es.tokenize(decode("La empresa dueña del proyecto es DE-LIO Company"), as_unicode=True)
        self.failUnless(u'DE-LIO' in tokens)

    def test_numerics(self):
        tokens = es.tokenize(decode("En total 2.113 civiles perdieron la vida en 2008."), as_unicode=True)
        self.failUnless(u'2.113' in tokens)
        self.failUnless(u'2008' in tokens)

        tokens = es.tokenize(decode(r"registró un aumento del 24% en 2009"), as_unicode=True)
        self.failUnless(u'24%' in tokens)

        tokens = es.tokenize(decode("Es vergonzoso que se haya gastado US$38.000 millones en armas"), as_unicode=True)
        self.failUnless(u'US$38.000' in tokens)

    def test_urls(self):
        tokens = es.tokenize(decode("que se desarrolló \"debido a la saturación de Twitter.com\""), as_unicode=True)
        self.failUnless(u'Twitter.com' in tokens)

        tokens = es.tokenize(decode("http://www.bbc.co.uk/mundo/lg/internacional/2009/08/090723_vida_afganistan_jp.shtml"), as_unicode=True)
        self.assertEqual(len(tokens), 1)

    def test_abbreviations(self):
        tokens = es.tokenize(decode("¿deben Colombia y EE.UU. explicar los detalles del acuerdo?"), as_unicode=True)
        self.failUnless(u'EE.UU.' in tokens)

    def test_punctuation(self):
        tokens = es.tokenize(decode("Hay juegos bélicos en los que se ve gente mutilada, disparos, choques con carro, es una violencia fuerte..."), as_unicode=True)
        self.failUnless(u'...' in tokens)

    def test_compounds_regression(self):
        tokens = es.tokenize(decode("3M y McDonald´s."), as_unicode=True)
        self.assertEqual(len(tokens), 4)
