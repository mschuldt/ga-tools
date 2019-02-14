
import os

from .defs import *
from .word import Ref

class Token:
    def __init__(self, value, line, col, source):
        self.value = value
        self.line = line
        self.col = col - len(value)
        #self.filename = intern(filename)
        self.source = source

    def __repr__(self):
        s = 'NEWLINE' if self.value == '\n' else self.value
        return 'token({})'.format(s)

class Node:
    def __init__(self, coord):
        self.coord = coord
        self.asm = False
        self.tokens = []
        self.symbols = []
        self.index = 0
        self.next_token = None

    def copy(self, coord):
        node = Node(coord)
        node.asm = self.asm
        node.tokens = self.tokens
        node.symbols = self.symbols
        return node

    def token_reader(self, node):
        return TokenReader(node, self.tokens)

    def finish(self):
        pass

class AforthNode(Node):
    def __init__(self, coord):
        super(AforthNode, self).__init__(coord)
    def add_token(self, token):
        v = token.value
        if v == '\n':
            return
        if v == 'asm':
            throw_error("'ASM' must come after 'node'")
        self.tokens.append(token)

class AsmNode(Node):
    def __init__(self, coord):
        super(AsmNode, self).__init__(coord)
        self.asm = True
        self.line = []

    def add_token(self, token):
        v = token.value
        if v == '\n':
            if self.line:
                self.tokens.append(self.line)
                self.line = []
        else:
            self.line.append(token)

    def finish(self):
        if self.line:
            self.tokens.append(self.line)

class Tokenizer:
    def __init__(self, s, source=None):
        self.source = source
        self.current_line = 1
        self.current_column = 1
        self.text = None
        self.last_word = None
        self.unread_word = None
        self.index = 0
        self.text = tuple(s)
        self.last = len(self.text) - 1

    def eof(self):
        return self.index > self.last

    def read_char(self):
        if self.unread_word == '\n':
            self.unread_word = None
            return '\n'
        c = self.text[self.index]
        self.index += 1
        self.current_column += 1
        if is_newline(c):
            self.current_line += 1
            self.current_column = 1
        return c

    def peak(self):
        return self.text[self.index]

    def skip_to(self, char, exclusive=False):
        while True:
            if self.eof():
                return
            c = self.read_char()
            if c == char:
                if exclusive:
                    self.index -= 1
                return

    def skip(self, fn):
        while True:
            if self.eof():
                return None
            c = self.peak()
            if not fn(c):
                break
            self.read_char()

    def skip_space(self):
        self.skip(is_space)

    def skip_whitespace(self):
        self.skip(is_whitespace)

    def read_token(self):
        self.skip_space()
        word = []
        while True:
            if self.eof():
                break
            if is_newline(self.peak()):
                if not word:
                    self.read_char()
                    word = ['\n']
                break
            else:
                char = self.read_char()
                if is_space(char):
                    break
                word.append(char)
        value = ''.join(word).lower() or None
        if value is None:
            return None
        t = Token(value, self.current_line,
                  self.current_column, self.source)
        self.last_word = t
        return t

    def skip_comments(self, val):
        if val == '(':
            self.skip_to(')')
            return True
        if val == '\\':
            self.skip_to('\n', True)
            return True
        return False

    def tokens(self):
        self.skip_whitespace()
        ret = []
        while True:
            t = self.read_token()
            if t is None:
                break
            if not self.skip_comments(t.value):
                ret.append(t)
        self.token_list = ret
        return ret

class Parser:
    def __init__(self):
        self.chips = {}
        self.current_chip = None # dictionary
        self.current_node = None # list of tokens
        # list of nodes that share the source of current_node
        self.other_nodes = []
        self.current_node = None

        self.labels = []

        self.tokens = []
        self.next_token = None

    def include_string(self, s, source=None):
        tokenizer = Tokenizer(s, source)
        tokens = tokenizer.tokens()
        if self.next_token:
            self.tokens.append(self.next_token)
        else:
            tokens.append(None)
        tokens.reverse()
        self.next_token = tokens.pop()
        self.tokens.extend(tokens)

    def include_file(self, filename=None):
        if filename is None:
            tok = self.read_name_token()
            if tok.source:
                base = os.path.abspath(os.path.dirname(tok.source))
                filename = os.path.join(base, tok.value)
            else:
                filename = tok.value
        f = open(filename)
        self.include_string(f.read(), filename)
        f.close()

    def read_token(self):
        t = self.next_token
        if t:
            self.next_token = self.tokens.pop()
        set_current_token(t)
        return t

    def eof(self):
        return self.next_token is None

    def peak(self):
        t = self.next_token
        return t.value if t else t

    def to_int(self, s):
        try:
            return int(s, 0)
        except ValueError as e:
            throw_error(e)

    def read_name_token(self):
        while True:
            t = self.read_token()
            if t is None:
                throw_error('invalid name')
            name = t.value
            if name == '\n':
                continue
            return t

    def read_name(self):
        t = self.read_name_token()
        return t.value if t else None

    def new_chip(self, default=False):
        if default:
            name = '__default__'
        else:
            name = self.read_name()
        chip = {}
        if name in self.chips:
            throw_error('repeated chip: ' + str(name))
        self.chips[name] = chip
        self.current_chip = chip
        return chip

    def finish_node(self):
        # handle multiple nodes
        if self.current_node is None:
            return
        node = self.current_node
        node.finish()
        for coord in self.other_nodes:
            self.current_chip[coord] = node.copy(coord)
        self.other_nodes = []
        self.current_node = None

    def expand_range(self, a, b):
        a, b = self.to_coord(a), self.to_coord(b)
        if a//100 == b//100:
            inc = 1
        else:
            inc = 100
            if a%100 != b%100:
                throw_error('invalid node range')
        coord, end = min(a,b), max(a,b)
        ret = [coord]
        while coord != end:
            coord += inc
            ret.append(coord)
        return ret

    def to_coord(self, s):
        n = self.to_int(s)
        if not valid_coord(n):
            throw_error('invalid node coordinate: ' + str(n))
        return n

    def expand_coords(self, s):
        ret = []
        for coord in s.split(','):
            crange = coord.split('-')
            if len(crange) == 1:
                ret.append(self.to_coord(crange[0]))
            else:
                if len(crange) != 2:
                    msg = 'invalid node coordinate range: ' +str(crange)
                    throw_error(msg)
                ret.extend(self.expand_range(crange[0], crange[1]))
        return ret

    def read_coord(self):
        assert not self.other_nodes
        coords = self.expand_coords(self.read_name())
        if len(coords) > 1:
            self.other_nodes = coords[1:]
        return coords[0]

    def read_port_name(self):
        name = self.read_name()
        if name not in port_names:
            throw_error('Invalid port: {}'.format(name))
        return name

    def make_wire(self):
        from_port = self.read_port_name()
        to_port = self.read_port_name()
        # TODO: faster wire code - double unext with preloaded stacks
        code = '''boot {} a! {} b!
        : loop 0x3ffff for @ !b unext loop'''.format(from_port, to_port)
        source = '<wire_{}_{}>'.format(from_port, to_port)
        self.include_string(code, source)

    def make_node(self, coord):
        w = self.peak()
        if w == 'asm':
            self.read_token() # discard 'asm'
            return AsmNode(coord)
        else:
            return AforthNode(coord)

    def new_node(self):
        assert self.current_chip is not None
        self.finish_node()
        coord = self.read_coord()
        if coord in self.current_chip:
            throw_error('repeated node: ' + str(coord))
        node = self.make_node(coord)
        self.current_node = node
        self.current_chip[coord] = node
        return node

    def do_colon(self, t):
        name = self.read_name_token()
        node = self.current_node
        if not node:
            throw_error('node is unspecified')
        if name.value in node.symbols:
            throw_error("name '{}' already defined".format(name.value))
        node.symbols.append(name.value)
        node.add_token(t)
        node.add_token(name)

    def parse(self):
        while True:
            t = self.read_token()
            if t is None:
                break
            w = t.value
            if w == 'chip':
                self.new_chip()
                continue
            if self.current_chip is None:
                self.new_chip(True)
            if w == 'node':
                self.new_node()
                continue
            if w == 'include':
                self.include_file()
                continue
            if w == 'wire':
                self.make_wire()
                continue
            if w == ':':
                self.do_colon(t)
                continue
            if w == '\n' and not self.current_node:
                continue
            self.current_node.add_token(t)
        self.finish_node()
        return self.chips

class TokenReader:
    def __init__(self, node, tokens):
        self.tokens = tokens
        self.index = 0
        self.last = len(tokens) -1
        self.node = node

    def peak(self):
        return self.read_word(True)

    def read_token(self, peak=False):
        if self.index > self.last:
            return None
        w = self.tokens[self.index]
        if not peak:
            self.index += 1
            set_current_token(w)
        return w

    def read_word(self, peak=False):
        t = self.read_token(peak)
        return t.value if t else None

    def read_int(self):
        w = self.read_word()
        try:
            return int(w, 0)
        except ValueError as e:
            throw_error(e)

    def read_coord(self):
        n = self.read_int()
        if not valid_coord(n):
            throw_error('invalid node coordinate: ' + str(n))
        return n

    def error(self, msg):
        pass

def is_space(c):
    n = ord(c)
    return n < 33 and n != 13 and n != 10

def is_newline(c):
    return c == '\n' or c == '\r'

def is_whitespace(c):
    return ord(c) < 33
