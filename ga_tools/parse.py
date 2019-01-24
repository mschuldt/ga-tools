
from .defs import *

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

    def set_string(self, s):
        assert not self.initialized
        self.text = tuple(s)
        self.last = len(self.text) - 1
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

    def read_word(self):
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
        self.last_word = ''.join(word).lower() or None
        return self.last_word

    def read_line(self):
        line = []
        self.skip_whitespace()
        while True:
            word = self.read_word()
            if word == '\n' or not word:
                return line
            if word == '\\':
                self.skip_to('\n')
                return line
            line.append(word)

    def read_int(self):
        try:
            return int(self.read_word(), 0)
        except ValueError as e:
            throw_error(e)

    def unread(self):
        self.unread_word = self.last_word

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

def is_space(c):
    n = ord(c)
    return n < 33 and n != 13 and n != 10

def is_newline(c):
    return c == '\n' or c == '\r'

def is_whitespace(c):
    return ord(c) < 33
