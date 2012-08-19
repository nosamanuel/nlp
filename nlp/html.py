import re

import html5lib
from html5lib.tokenizer import HTMLTokenizer
from html5lib.sanitizer import HTMLSanitizerMixin
from html5lib.serializer.htmlserializer import HTMLSerializer
from html5lib.treewalkers import lxmletree
from lxml.html import fromstring

WHITESPACE_RE = re.compile(r'^(&nbsp;|\s)*$', re.U)

namespace = u'http://www.w3.org/1999/xhtml'
container_elements = ['div', 'span']
readable_elements = (
    'a', 'abbr', 'acronym', 'address', 'b', 'bdo', 'big', 'blockquote',
    'caption', 'center', 'cite', 'code', 'dd', 'del', 'dfn', 'dir',
    'div', 'dl', 'dt', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'i',
    'img', 'ins', 'kbd', 'label', 'legend', 'li', 'menu', 'ol', 'p', 'pre',
    'q', 's', 'samp', 'small', 'span', 'strike', 'strong', 'style',
    'sub', 'sup', 'table', 'tt', 'u', 'ul', 'var'
)
inline_elements = (
    'a', 'abbr', 'acronym', 'b', 'basefont', 'bdo', 'big', 'br',
    'cite', 'code', 'dfn', 'em', 'font', 'i', 'img', 'input', 'kbd',
    'label', 'q', 's', 'samp', 'select', 'small', 'span', 'strike',
    'strong', 'sub', 'sup', 'textarea', 'tt', 'u', 'var'
)
block_elements = (
    'address', 'blockquote', 'center', 'dir', 'div', 'dl',
    'fieldset', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr',
    'isindex', 'menu', 'noframes', 'noscript', 'ol', 'p', 'pre', 'table', 'ul'
)
form_elements = (
    'form', 'input', 'textarea', 'label', 'fieldset',
    'legend', 'select', 'optgroup', 'option', 'button',
)
readable_blocks = (
    'address', 'blockquote', 'center', 'dir', 'dl',
    'fieldset', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ol', 'p', 'pre', 'ul',
    # 'table' # Tables are out for now
)
text_types = ('Characters', 'SpaceCharacters')
empty_types = ('StartTag', 'EndTag', 'SpaceCharacters', 'EmptyTag',)
newlines = {'data': u'\n\n', 'type': 'Characters'}


def is_empty(inline_cache):
    for e in inline_cache:
        if e['type'] in text_types:
            if WHITESPACE_RE.match(e['data']) is None:
                return False
            else:
                pass
        elif e['type'] not in empty_types:
            return False
    return True


class ReadableTokenizer(HTMLTokenizer, HTMLSanitizerMixin):
    """
    First-pass tokenizer used to filter and sanitize non-readable elements.
    """
    def __iter__(self):
        super_iter = super(ReadableTokenizer, self).__iter__()
        for token in super_iter:
            if 'name' in token:
                if token['name'] == u'title':
                    # Skip the title tag
                    token = next(super_iter)
                    while token.get('name') != 'title':
                        token = next(super_iter)
                elif not token['name'] in readable_elements:
                    # Skip any tag that isn't readable
                    continue

            token = self.sanitize_token(token)
            if token:
                yield token


class ReadableTreewalker(lxmletree.TreeWalker):
    """
    A tree walker that only yields the readable elements of a document.

    Readable inline elements are grouped into paragraphs and emitted at
    the start of the next readable block, non-readable element, or end
    of the document.

    A blank line is also emitted between readable blocks.
    """
    def __iter__(self):
        inline_cache, block_cache, block_stack = [], [], []
        for e in super(ReadableTreewalker, self).__iter__():
            # Push the next readable block start tag onto the stack
            if e.get('name') in readable_blocks and e['type'] == 'StartTag':
                # Push a new block to the stack if the stack is empty or
                # if a block of the same type is nested in our current stack
                if not block_stack or block_stack[-1] == e['name']:
                    block_stack.append(e['name'])
                    block_cache.append(e)
                # If this is the start of a new top-level reading block,
                # flush the inline cache as a new P element
                if len(block_stack) == 1 and inline_cache:
                    if not is_empty(inline_cache):
                        yield {'namespace': namespace,
                               'type': 'StartTag', 'name': u'p', 'data': {}}
                        for i in inline_cache:
                            yield i
                        yield {'namespace': namespace,
                               'type': 'EndTag', 'name': u'p', 'data': {}}
                        yield newlines
                    inline_cache = []
            # Pop the next level of nested block from the stack on end tag
            elif ('name' in e and e['type'] == 'EndTag' and
                    block_stack and block_stack[-1] == e['name']):
                block_stack.pop()
                block_cache.append(e)
                # If we're back at the top, flush the current readable block
                if not block_stack:
                    if not is_empty(block_cache):
                        for e in block_cache:
                            yield e
                        yield newlines
                    block_cache = []
            # If we encounter a text element outside a readable block,
            # cache it until we encounter the next readable block
            elif not block_stack and e['type'] in text_types:
                inline_cache.append(e)
            # Include all other elements in the current block
            elif block_stack and e.get('name') not in container_elements:
                block_cache.append(e)


def sanitize(html, strip_whitespace=False):
    """
    Sanitize HTML to leave only the readable top-level elements.
    """
    TreeBuilder = html5lib.treebuilders.getTreeBuilder("lxml")
    parser = html5lib.HTMLParser(tree=TreeBuilder, tokenizer=ReadableTokenizer)
    tree = parser.parse(html)
    walker = ReadableTreewalker(tree)
    serializer = HTMLSerializer(strip_whitespace=strip_whitespace)
    return serializer.render(walker)


def get_text(html):
    root = fromstring(html)
    return root.text_content()
