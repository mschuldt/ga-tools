
def is_whitespace(c):
    n = ord(c)
    return n < 33 and n != 13 and n != 10

def is_newline(c):
    return c == '\n' or c == '\r'

class Parser:
    def __init__(self):
        self.current_line = 0
        self.current_column = 0
        self.word_start_column = 0
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
        c = self.text[self.index]
        self.index += 1
        self.current_column += 1
        if is_newline(c):
            self.current_line += 1
            self.current_column = 0
        return c

    def skip_to(self, char):
        while True:
            if self.eof():
                return
            c = self.read_char()
            if c == char:
                return

    def peak(self):
        return self.text[self.index]

    def skip_whitespace(self):
        while True:
            if self.eof():
                return None
            if not is_whitespace(self.peak()):
                break
            self.read_char()

    def read_word(self):
        if self.unread_word:
            w = self.unread_word
            self.unread_word = None
            return w
        self.skip_whitespace()
        self.word_start_column = self.current_column
        word = []
        while True:
            if self.eof():
                break
            next_char = self.peak()
            if is_newline(next_char):
                if not word:
                    self.read_char()
                    return '\n'
                break
            char = self.read_char()
            if is_whitespace(char):
                break
            word.append(char)
        self.last_word = ''.join(word).lower() or None
        return self.last_word

    def read_line(self):
        line = []
        while True:
            word = self.read_word()
            if is_newline(word) or not word:
                return line
            line.append(word)

    def read_int(self):
        return int(self.read_word(), 0)

    def unread(self):
        self.unread_word = self.last_word
