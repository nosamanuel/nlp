# -*- coding: utf-8 -*-
import unittest

from nlp.html import get_text, sanitize


TEST_DOCUMENT = u"""
<doctype html>
<html>
    <head>
        <title>Title</title>
    </head>
    <body>
        <h1>Header</h1>
        <p>Text</p>
    </body>
</html>
"""


class TestPunctuation(unittest.TestCase):
    def test_get_text(self):
        html = u"""
        <div>
            <p>Here is my HTML.</p>
            <p>It has my text in it.</p>
        </div>
        """
        text = get_text(html)
        self.assertEqual(text, u"""
            Here is my HTML.
            It has my text in it.
        """)

    def test_sanitize(self):
        html = sanitize(TEST_DOCUMENT)
        self.assertEqual(html, (u"<h1>Header</h1>\n\n<p>Text</p>\n\n"))

    def test_sanitized_get_text(self):
        sanitized_html = sanitize(TEST_DOCUMENT)
        text = get_text(sanitized_html)
        self.assertEqual(text, u"Header\n\nText")
