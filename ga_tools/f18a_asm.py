
import re

from .defs import *
from .word import *

class F18a:
    def __init__(self, chip, coord):
        #self.rom = None
        self.symbols = {} # maps names to Word objects
        self.symbol_names = []
        self.rom_names = []
        self.boot = None # first boot word
        w = Word()
        self.ram = w # first instruction word
        self.current_word = w
        self.last_word = w
        self.current_slot = 0
        self.stack = []
        self.prev_op = None
        self.boot_code = False
        self.chip = chip
        self.coord = coord
        self.port_addrs = node_ports(coord)
        self.node_port_names = node_port_names(coord)
        self.extended_arith = 0
        self.asm_node = False
        self.next_asm_symbol = None
        self.finished = False
        self.compile_0_as_dup_dup_or = True
        self.auto_nop_insert = True
        self.const_refs = []
        self.init_a = None
        self.init_b = None
        self.init_p = None
        self.init_io = None
        self.stream = False
        self.name = None

    def pop(self):
        if not self.stack:
            throw_error('assembler stack underflow')
        return self.stack.pop(-1)

    def push(self, val):
        self.stack.append(val)

    def swap(self):
        t = self.pop()
        s = self.pop()
        self.push(t)
        self.push(s)

    def count_ram(self):
        word = self.ram
        count = 0
        last = None
        while word:
            if word.stream:
                count += word.stream.count_ram()
            else:
                count += 1
            last = word
            word = word.next
        if last and last.empty():
            count -= 1
        return count

    def finish_word(self):
        # fill rest of current_word with nops
        pass

    def parse_ref(self, name):
        m = re.search('([^ ]+)@([0-9]+)', name)
        if m:
            return m.group(1), self.chip.node(int(m.group(2)))
        m = re.search('([0-9]+)[.]([^ ]+)', name)
        if m:
            return m.group(2), self.chip.node(int(m.group(1)))
        return name, self

    def make_ref(self, name):
        if type(name) is int:
            return Ref(node=self, value=name)
        try:
            return Ref(node=self, value=int(name, 0))
        except ValueError as e:
            pass
        word, location = self.parse_ref(name)
        if word in port_names:
            word = self.node_port_names[port_names.index(name)]
        return Ref(node=location, name=word)

    def new_word(self, set_current=True):
        # start a new word. return it
        assert not self.finished
        w = Word()
        w.extended_arith = self.extended_arith
        w.prev = self.last_word
        self.last_word.next = w
        self.last_word = w
        if set_current:
            self.current_word = w
            self.current_slot = 0
        if not self.boot_code and not self.ram:
            self.ram = w
        return w

    def fill_rest_with_nops(self):
        # force word alignment. Fills rest of current word with nops
        while self.current_slot != 0:
            self.add_to_next_slot('.')

    def inc_slot(self):
        #TODO: should not be necessary. Needed now because of methods
        #      like Word.compile_next that add ops to word without
        #      using F18a.add_to_next_slot
        self.current_slot += 1
        if self.current_slot == 4:
            self.new_word()

    def add_to_next_slot(self, op):
        assert not self.finished
        self.current_word.set_op(op)
        self.prev_op = op
        self.inc_slot()

    def set_next_const(self, const):
        if self.current_slot == 0:
            self.current_word.set_const(const)
            w = self.current_word
            self.new_word()
            return w
        w = self.new_word(set_current=False)
        w.set_const(const)
        return w

    def maybe_insert_nop(self, op):
        if not self.auto_nop_insert:
            return
        if op not in ops_preceded_by_nops:
            return
        if self.prev_op in ops_completing_carry:
            return
        self.add_to_next_slot(NOP)

    def compile_op(self, op):
        check_op(op)
        self.maybe_insert_nop(op)
        if self.current_slot == 3 and op not in last_slot_ops:
            self.add_to_next_slot(NOP)
        self.add_to_next_slot(op)
        if op in ops_using_rest_of_word:
            self.fill_rest_with_nops()

    def compile_constant(self, const):
        if const == 0 and self.compile_0_as_dup_dup_or:
            self.compile_op(DUP)
            self.compile_op(DUP)
            self.compile_op(XOR)
        else:
            self.compile_op(READ_P)
            self.set_next_const(const)

    def compile_call(self, op, ref):
        if self.current_slot == 3:
            self.fill_rest_with_nops()
        self.current_word.set_call(op, ref)
        self.prev_op = op
        self.new_word()

    def end_boot_code(self):
        node = self.current_word
        self.ram = node
        if node.prev:
            # unlink from boot code chain
            node.prev.next = None
            node.prev = None
        self.boot_code = False

    def start_def(self, name):
        self.fill_rest_with_nops()
        if self.boot_code:
            self.end_boot_code()

        if name == 'boot':
            self.boot_code = True
            self.boot = self.current_word
        self.symbols[name] = self.current_word

    def compile_if(self, op):
        if self.current_slot == 3:
            self.add_to_next_slot(NOP)
        self.current_word.set_if(op)
        self.prev_op = op
        self.push(self.current_word)
        self.new_word()

    def compile_then(self):
        self.fill_rest_with_nops()
        word = self.pop()
        word.dest_word = self.current_word

    def compile_next(self, op):
        if self.current_slot == 3:
            self.add_to_next_slot(NOP)
        self.current_word.set_next(op, self.pop())
        self.inc_slot()
        if self.current_slot != 0:
            self.new_word()

    def compile_port(self, port):
        self.compile_constant(self.port_addrs[port])

    def start_stream(self, stream):
        self.fill_rest_with_nops()
        self.current_word.stream = stream
        self.new_word()

    def start_stream1(self, stream):
        self.compile_op(READ_P)
        w = self.set_next_const(12345)
        w.stream = stream

    def port_addr(self, port, opposite=False):
        if opposite:
            port = (SOUTH, WEST, NORTH, EAST)[port]
        return self.port_addrs[port]

    def add_asm_word(self, w):
        self.asm.append(w)

    def finish(self):
        # Finish assembling this node
#        if self.current_word.empty():
#            return
        if self.current_word.type == INST:
            self.fill_rest_with_nops()
        # can't trim word from nodes yet because the last
        # word might be the destination for an addresss node
        #self.trim_last_word()
        if self.asm_node:
            if self.next_asm_symbol:
                self.symbols[self.next_asm_symbol] = self.current_word
        self.finished = True

    def trim_last_word(self):
        if self.last_word.empty():
            if self.last_word.prev:
                self.last_word = self.last_word.prev
                self.last_word.next = None
            else:
                self.ram = None
                self.last_word = None
        self.finished = True

    def get_asm_ref(self, word):
        if type(word) == int:
            return Ref(node=self, value=word)
        if len(word)==1 and word[0] not in ops:
            return self.make_ref(word[0])
        return None

    def do_asm_word(self, ops, word):
        const = self.get_asm_ref(ops)
        if const is not None:
            word.set_const(const)
        else:
            for op in ops:
                if op in address_required:
                    word.set_call(op, self.make_ref(ops[-1]))
                    return word
                else:
                    word.set_op(op)
                    if op in ops_using_rest_of_word:
                        word.fill_rest_with_nops()
                        return word
        word.fill_rest_with_nops()
        return word

    def asm_word(self, ops, add_to_node=False):
        if add_to_node:
            if ops[0] == ':':
                self.next_asm_symbol = ops[1]
                return None
            if self.next_asm_symbol:
                self.symbols[self.next_asm_symbol] = self.current_word
                self.next_asm_symbol = None
            asm = self.do_asm_word(ops, self.current_word)
            self.new_word()
            return asm
        word = self.do_asm_word(ops, Word())
        word.extended_arith = self.extended_arith
        if word.type == ADDR:
            word.resolve_symbol()
        return word.asm()

    def asm_words(self, words, add_to_node=False):
        #return [self.asm_word(w) for w in words]
        if add_to_node:
            for w in words:
                self.asm_word(w, add_to_node)
            return None
        for i, w in enumerate(words):
            words[i] = self.asm_word(w, add_to_node)
        return words

    def start_addr(self, with_extended_arith=True):
        # Returns the start address - address of 'main' or 0
        w = self.symbols.get('main')
        if w:
            if self.init_p is not None:
                throw_error("conflicting /p and 'main'")
            addr = w.word_addr
            if with_extended_arith:
                addr |= w.extended_arith
            return addr
        if self.init_p:
            return self.init_p.resolve()
        return 0

    def symbol_addr(self, name):
        # return address of symbol NAME, or None if it's not known yet
        w = self.symbols.get(name)
        if w is None:
            return None
        return w.word_addr

    def set_word_addresses(self):
        # Set the address in ram of each word
        a = 0
        word = self.ram
        while word:
            word.word_addr = a
            word = word.next
            a += 1

    def resolve_transfers(self):
        # Set the transfer address in each word
        word = self.ram
        while word:
            if word.dest_word:
                addr = word.dest_word.word_addr
                assert addr is not None
                word.set_addr(addr)
            word = word.next

    def assemble_list(self, lst):
        # Assembles a linked list of words
        ret = []
        while lst:
            ret.append(lst.asm())
            lst = lst.next
        # # Wrap words around for greenarray aforth compatibility
        # if len(ret) > 64:
        #     last = ret[64:]
        #     ret = last + ret[len(last):64]
        return ret

    def assemble(self, check_size=False):
        # returns list of assembled RAM
        asm = self.assemble_list(self.ram)
        if check_size and len(asm) > 64:
            m = 'node {} code is too large: {} words'
            throw_error(m.format(self.coord, len(asm)), False)
        return asm

    def assemble_boot_code(self):
        return self.assemble_list(self.boot)

    def aforth_list(self):
        ret = []
        word = self.ram
        while word:
            ret.append(word.aforth_list())
            word = word.next
        return ret

    def resolve_calls(self):
        # Set the symbol address in each word
        word = self.ram
        while word:
            if word.addr_sym:
                word.resolve_symbol()
            word = word.next

    def shift_addr_words(self):
        # Move transfer to new word if it doesn't fit.
        # It's fast enough
        word = self.ram
        while word:
            if not self.word_addr_fits(word):
                self.shift_addr_word(word)
                self.set_word_addresses()
                word = self.ram
            word = word.next

    def word_addr_fits(self, word, p=None):
        # Return True if the address WORD its in the available slots
        if word.type != ADDR:
            return True
        sym = word.addr_sym
        dest_addr = sym.resolve() if sym else word.dest_word.word_addr
        mask = word_address_masks[word.op_index]
        _mask = ~mask & 0x3ffff
        p = word.word_addr + 1 if p is None else p
        min_dest = _mask & p
        max_dest = (_mask & p) | (mask & dest_addr)
        return (dest_addr >= min_dest) & (dest_addr <= max_dest)

    def find_shift_dest(self, word):
        ret = word
        for i in range(4):
            if word._slots[i] == OP_READ_P:
                ret = ret.next
        return ret

    def shift_addr_word(self, word):
        # Creates a new word following WORD and moves the
        # transfer to the new word.
        # If instruction has @p instructions, insert the instruction
        # after the last word they read.
        new = Word()
        new.move_addr(word)
        after = self.find_shift_dest(word)
        after.next.prev = new
        new.prev = after
        new.next = after.next
        after.next = new
        if new.next is None:
            self.last_word = new

    def insert_streams(self):
        word = self.ram
        while word:
            if word.stream:
                self.insert_stream(word, word.stream)
            word = word.next

    def insert_stream(self, word, stream):
        # replace WORD with the words in STREAM
        if stream.single_word:
            return self.insert_stream1(word, stream)
        first = self.get_stream_ram(stream)
        if word.prev:
            word.prev.next = first
            first.prev = word.prev
        else:
            self.asm = first
        last = stream.last_word
        stream.trim_last_word
        if word.next:
            word.next.prev = last
            last.next = word.next
        else:
            self.last_word = last

    def insert_stream1(self, word, stream):
        asm = stream.assemble()
        if len(asm) > 1:
            for i, word in enumerate(asm):
                print(i, word, disasm_to_str(word))
            fmt = '{{...}} is too long (4 ops max): {}'
            throw_error(fmt.format(asm))
        elif len(asm) == 0:
            throw_error('empty {...}')
        word.set_const(asm[0])

    def get_stream_ram(self, stream):
        ram = stream.ram
        if stream.into:
            pass #TODO
        return ram

    def move_forward(self, n):
        if not self.current_word.empty():
            self.fill_rest_with_nops()
        if self.boot_code:
            self.end_boot_code()
        length = self.count_ram()
        if n < length:
            throw_error("cannot 'org' backwards")
        for _ in range(n - length):
            self.new_word()

    def print_list(self, ll, names={}):
        a = 0
        while ll:
            s = names.get(a)
            if s:
                print(':', s)
            asm = ll.asm()
            disasm = disasm_to_str(asm)
            addr = hex(a)[2:].ljust(5)
            comp = str(ll).ljust(20)
            asm = str(asm).ljust(13)
            print(addr, comp, asm, disasm)
            ll = ll.next
            a += 1

    def print(self, simple=False):
        # pretty print this node
        # TODO: -should call self.assemble since that wraps the words
        #       -handle the word wrapping better...
        if simple:
            return self.simple_print()
        print('\n'+'_'*53)
        print('      Compiled             Assembled     Disassembled')
        print('node ', self.coord, '  ASM' if self.asm_node else '')
        p = self.start_addr()
        if p:
            print('/p', p)
        if self.init_a is not None:
            print('/a', self.init_a)
        if self.init_b is not None:
            print('/b', self.init_b)
        if self.boot:
            print(': boot')
            self.print_list(self.boot)
            print('- '*27)
        names = {w.word_addr:s for s,w in self.symbols.items()}
        self.print_list(self.ram, names)

    def simple_print(self):
        print('node', self.coord)
        word = self.ram
        while word:
            print(word.asm())
            word = word.next

    def json(self):
        return {'coord': self.coord,
                'ram': self.assemble(),
                'forth': self.aforth_list(),
                'boot_code': self.assemble_boot_code(),
                'symbols': {n:w.word_addr
                            for n,w in self.symbols.items()},
                'a': self.init_a.resolve() if self.init_a else None,
                'b': self.init_b.resolve() if self.init_b else None,
                'p': self.start_addr(False),
                'io': self.init_io.resolve() if self.init_io else None}

class Stream(F18a):
    counter = 0
    def __init__(self, chip, node, address=0x195, into=None):
        super(Stream, self).__init__(chip, node.coord)
        self.node = node
        self.address = address
        self.into = into # store instruction: ! !b !p
        self.symbol_names = node.symbol_names
        self.symbols = node.symbols
        self.rom_names = node.rom_names
        self.stream = True
        self.single_word = True
        self.name = 'Stream_{}_{}'.format(self.coord, Stream.counter)
        Stream.counter += 1

    def set_word_addresses(self):
        a = self.address
        word = self.ram
        while word:
            word.word_addr = a
            word = word.next

    def count_ram(self):
        count = super(Stream, self).count_ram()
        if self.into:
            # reserve space for stream logic
            count += 3
        return count
