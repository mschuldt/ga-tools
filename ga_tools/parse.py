
from .defs import *

class Token:
    def __init__(self, value, line, col, filename):
        self.value = value
        self.line = line
        self.col = col
        #self.filename = intern(filename)
        self.filename = filename

class Parser:
    def __init__(self):
        self.current_line = 1
        self.current_column = 1
        self.word_start_column = 0
        self.current_line_start = 0
        self.text = None
        self.last_word = None
        self.unread_word = None
        self.last = 0
        self.index = 0
        self.initialized = False
        self.filename = None
        self.chips = {}
        self.current_chip = None # dictionary
        self.current_node = None # list of tokens
        # list of nodes that share the source of current_node
        self.other_nodes = []
        self.labels = []
        self.asm_line = []
        self.asm = False
        self.current_coord = None

    def set_string(self, s):
        assert not self.initialized
        self.text = tuple(s)
        self.last = len(self.text) - 1
        self.parse()
        self.initialized = True

    def set_file(self, filename):
        f = open(filename)
        self.set_string(f.read())
        f.close()
        self.filename = filename

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
            self.current_line_start = self.index
        return c

    def skip_to(self, char):
        while True:
            if self.eof():
                return
            c = self.read_char()
            if c == char:
                return

    def peak(self):
        if self.unread_word:
            return self.unread_word[0]
        return self.text[self.index]

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
        if self.unread_word:
            w = self.unread_word
            self.unread_word = None
            return w
        self.skip_space()
        self.word_start_column = self.current_column
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
        t = Token(value, self.current_column,
                  self.current_line, self.filename)
        self.last_word = t
        return t

    def to_int(self, s):
        try:
            return int(s, 0)
        except ValueError as e:
            throw_error(e)

    def read_int(self):
        return self.to_int(self.read_word())

    def unread(self):
        self.unread_word = self.last_word

    def read_name(self):
        while True:
            t = self.read_token()
            if t is None:
                throw_error('invalid name')
            name = t.value
            if name == '\n':
                continue
            return name

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
        assert self.current_coord
        if self.asm_line:
            assert self.asm
            self.current_node.append(self.asm_line)
        data = {'tokens': self.current_node,
                'labels': self.labels,
                'filename': self.filename,
                'asm': self.asm}
        self.current_chip[self.current_coord] = data
        for node in self.other_nodes:
            self.current_chip[node] = data
        self.asm = False
        self.asm_line = []
        self.other_nodes = []
        self.current_node = None

    def read_coord(self):
        assert not self.other_nodes
        s = self.read_name()
        coords = list(map(self.to_int, s.split(',')))
        if len(coords) > 1:
            self.other_nodes = coords[1:]
        return coords[0]

    def check_asm(self):
        t = self.read_token()
        if t is None:
            return False
        if t.value == 'asm':
            self.asm = True
        else:
            self.unread()

    def new_node(self, global_code=False):
        self.finish_node()
        if global_code:
            coord = 'global'
        else:
            coord = self.read_coord()
        self.current_coord = coord
        node = []
        if coord in self.current_chip:
            throw_error('repeated node: ' + str(coord))
        self.current_node = node
        self.check_asm()
        return node

    def process_token_aforth(self, t, v):
        if v == '\n':
            return
        if v == '(':
            self.skip_to(')')
            return
        if v == '\\':
            self.skip_to('\n')
            return
        if v == 'asm':
            throw_error("'ASM' must come after 'node'")
        self.current_node.append(t)

    def process_token_asm(self, t, v):
        if v == '\\':
            self.skip_to('\n')
            v = '\n'
        if v == '\n':
            if self.asm_line:
                self.current_node.append(self.asm_line)
                self.asm_line = []
        else:
            self.asm_line.append(t)

    def process_token(self, t):
        v = t.value
        if v == ':':
            self.labels.append(self.read_name())
            self.unread()
        if self.asm:
            self.process_token_asm(t, v)
        else:
            self.process_token_aforth(t, v)

    def merge_tokens(self, data):
        for chip, nodes in data.items():
            if chip not in self.chips:
                self.chips[chip] = nodes
                continue
            our_nodes = self.chips[chip]
            for coord, data in nodes.items():
                if coord in our_nodes:
                    throw_error('included duplicate node: '+str(coord))
                if coord == 'global':
                    self.current_node.extend(data)
                else:
                    our_nodes[coord] = data

    def include(self):
        filename = self.read_name()
        p = Parser()
        p.set_file(filename)
        data = p.parse()
        self.merge_tokens(data)

    def parse(self):
        self.skip_whitespace()
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
            if self.current_node is None:
                #TODO: should not be happening
                self.new_node(True)
            if w == 'include':
                self.include()
                continue
            self.process_token(t)
        self.finish_node()
        return self.chips

    def print_current_source_line(self):
        i = self.current_line_start
        s = []
        while True:
            if i > self.last:
                break
            c = self.text[i]
            if is_newline(c):
                break
            s.append(c)
            i += 1
        print(''.join(s))

    def print_location(self):
        if not self.filename:
            print('   String... position', self.index)
        else:
            print('   File "{}"'.format(self.filename),
                  'line', self.current_line,
                  'column', self.current_column)
        print('      ',end='')
        self.print_current_source_line()

class TokenReader:
    def __init__(self, tokens, filename):
        self.tokens = tokens
        self.filename = filename
        self.index = 0
        self.last = len(tokens) -1


    def eof(self):
        return self.index > self.last

    def peak(self):
        return self.read_word(True)

    #    def next_word(self): #TODO: rename
    def read_word(self, peak=False):
        if self.eof():
            return None
        w = self.tokens[self.index]
        if not peak:
            self.index += 1
        return w.value

#    def next_int(self): #TODO: rename
    def read_int(self):
        w = self.read_word()
        try:
            return int(w, 0)
        except ValueError as e:
            throw_error(e)

    def error(self, msg):
        pass

def is_space(c):
    n = ord(c)
    return n < 33 and n != 13 and n != 10

def is_newline(c):
    return c == '\n' or c == '\r'

def is_whitespace(c):
    return ord(c) < 33
