# -*- coding: utf-8 -*-
import unittest

from nlp.punctuation import collapse


class TestPunctuation(unittest.TestCase):
    def test_collapse(self):
        sub1 = "Si vamos a matar a esa cosa,\n" \
               "necesitamos esas páginas."
        sub2 = "Pues bajemos a ese sótano\n" \
               "a trinchar una bruja."
        sub3 = "Vale, puede que sí.\n" \
               "Pero ¿por cuánto tiempo?"

        reg1 = "¡Si! Tu amante es mía, y ahora está ardiendo \n" \
               "en el infierno."

        # These should be collapsed to one line
        self.assertEqual(collapse(sub1), sub1.replace('\n', ' '))
        self.assertEqual(collapse(sub2), sub2.replace('\n', ' '))
        self.assertEqual(collapse(reg1), reg1.replace('\n', ''))

        # These should be unchanged
        self.assertEqual(collapse(sub3), sub3)
