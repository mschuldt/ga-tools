
from .defs import *
from .word import *

compile_0_as_dup_dup_or = True

class F18a:
    def __init__(self, coord):
        #self.rom = None
        self.symbols = {} # maps names to Word objects
        self.boot = None # first boot word
        w = Word()
        self.ram = w # first instruction word
        self.current_word = w
        self.last_word = w
        self.current_slot = 0
        self.stack = []
        self.last_op = None
        self.boot_code = False
        self.coord = coord
        self.port_addrs = node_ports(coord)
        self.extended_arith = 0
        self.asm_node = False
        self.next_asm_symbol = None
        self.finished = False

    def pop(self):
        return self.stack.pop(-1)

    def push(self, val):
        self.stack.append(val)

    def count_ram(self):
        word = self.ram
        count = 0
        last = None
        while word:
            count += 1
            last = word
            word = word.next
        if last and last.empty():
            count -= 1
        return count

    def finish_word(self):
        # fill rest of current_word with nops
        pass

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
        self.inc_slot()
        self.last_op = op

    def set_next_const(self, const):
        if self.current_slot == 0:
            self.current_word.set_const(const)
            self.new_word()
        else:
            w = self.new_word(set_current=False)
            w.set_const(const)

    def compile_op(self, op):
        check_op(op)
        if op in ops_preceded_by_nops:
            self.add_to_next_slot(NOP)
        if self.current_slot == 3 and op not in last_slot_ops:
            self.add_to_next_slot(NOP)
        self.add_to_next_slot(op)
        if op in ops_using_rest_of_word:
            self.fill_rest_with_nops()

    def compile_constant(self, const):
        if const == 0 and compile_0_as_dup_dup_or:
            self.compile_op(DUP)
            self.compile_op(DUP)
            self.compile_op(XOR)
        else:
            self.compile_op(READ_P)
            self.set_next_const(const)

    def compile_call(self, op, word):
        if self.current_slot == 3:
            self.fill_rest_with_nops()
        self.current_word.set_call(op, word)
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

    def port_addr(self, port, opposite=False):
        if opposite:
            port = (SOUTH, WEST, NORTH, EAST)[port]
        return self.port_addrs[port]

    def add_asm_word(self, w):
        self.asm.append(w)

    def get_const(self, word):
        if type(word) == int:
            return word
        if len(word)==1:
            n = parse_int(word[0])
            if n is not None:
                return n
        return None

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
                self.last_word.prev.next = None
            else:
                self.ram = None
        self.finished = True

    def do_asm_word(self, ops, word):
        const = self.get_const(ops)
        if const is not None:
            word.set_const(const)
        else:
            for op in ops:
                if op in address_required:
                    word.set_call(op, ops[-1])
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
            word.resolve_symbol(self.symbols)
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
            addr = w.word_addr
            if with_extended_arith:
                addr |= w.extended_arith
            return addr
        return 0

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
                assert addr
                word.set_addr(addr)
            word = word.next

    def assemble_list(self, lst):
        # Assembles a linked list of words
        ret = []
        while lst:
            ret.append(lst.asm())
            lst = lst.next
        return ret

    def assemble(self):
        # returns list of assembled RAM
        return self.assemble_list(self.ram)

    def assemble_boot_code(self):
        return self.assemble_list(self.boot)

    def resolve_calls(self):
        # Set the symbol address in each word
        word = self.ram
        while word:
            if word.addr_sym:
                word.resolve_symbol(self.symbols)
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
        sym = self.symbols.get(word.addr_sym)
        dest_addr = sym.word_addr if sym else word.dest_word.word_addr
        mask = word_address_masks[word.op_index]
        _mask = ~mask & 0x3ffff
        p = word.word_addr + 1 if p is None else p
        min_dest = _mask & p
        max_dest = (_mask & p) | (mask & dest_addr)
        return (dest_addr >= min_dest) & (dest_addr <= max_dest)

    def shift_addr_word(self, word):
        # Creates a new word following WORD and moves the
        # transfer to the new word.
        new = Word()
        new.move_addr(word)
        word.next.prev = new
        new.prev = word
        new.next = word.next
        word.next = new
        if new.next is None:
            self.last_word = new

    def print(self):
        # pretty print this node
        print('\n'+'_'*53)
        print('      Compiled             Assembled     Disassembled')
        print('node ', self.coord, '  ASM' if self.asm_node else '')
        w = self.symbols.get('main')
        #print('P =', w.word_addr if w else 0)

        def print_list(ll):
            a = 0
            while ll:
                s = addrs.get(a)
                if s:
                    print(':', s)
                asm = ll.asm()
                disasm = disasm_to_str(asm)
                addr = str(a).ljust(5)
                comp = str(ll).ljust(20)
                asm = str(asm).ljust(13)
                print(addr, comp, asm, disasm)
                ll = ll.next
                a += 1
        addrs = {}
        if self.boot:
            print(': boot')
            print_list(self.boot)
            print()
        addrs = {w.word_addr:s for s,w in self.symbols.items()}
        print_list(self.ram)

    def json(self):
        data = {'ram': self.assemble()}
        data['boot_code'] = self.assemble_boot_code()
        data['start_addr'] = self.start_addr(False)
        data['symbols'] = {n:w.word_addr
                           for n,w in self.symbols.items()}
        return data
