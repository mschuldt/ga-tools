
from .defs import *

xor_bits = (0b1010, 0b10101, 0b1010, 0b101)
xor_bits2 = (0b1010, 0b10101, 0b1010, 0b10100)

INST = 0
CONST = 1
ADDR = 2

class Word:
    def __init__(self, prev=None):
        self._slots = [None, None, None, None]
        if prev:
            self.prev.next = self
        self.next = None
        self.prev = None
        self.symbol = None
        self.const = None # set for number literals
        self.op_index = 0 # Index of next empty slot
        # If word type is ADDR, op_index will be left
        # pointing to the last op before the address
        self.dest_word = None # forward transfer destination word
        self._addr = None # set when word contains an address
        # set to True when addr is not yet determined
        self.addr_sym = None
        self.addr_slot = None
        self.type = INST
        self.label = None
        self.word_addr = None # address of this word in RAM
        self.extended_arith = 0

    def empty(self):
        #return self.op_index == 0
        return self.const is None and self._slots == [None, None, None, None]

    def fill_rest_with_nops(self):
        while self.op_index < 4:
            self.set_op(NOP)

    def set_op(self, op, final_slot=False):
        self._slots[self.op_index] = get_op_i(op)
        if not final_slot:
            self.op_index += 1

    def set_if(self, op):
        self.set_op(op, True)
        self.type = ADDR

    def set_next(self, op, dest):
        self.set_op(op, True)
        self.dest_word = dest
        self.type = ADDR

    def set_const(self, const):
        self.const = const
        self.type = CONST

    def set_call(self, op, name):
        self.set_op(op, True)
        self.addr_sym = name
        self.type = ADDR

    def set_addr(self, val):
        self._addr = val | self.extended_arith

    def move_addr(self, from_word):
        # Move address and associated op in word FROM_WORD to self
        assert from_word.type == ADDR
        assert self.type != ADDR
        self.type = ADDR
        self.addr_sym = from_word.addr_sym
        self.dest_word = from_word.dest_word
        self._addr = from_word._addr
        self._slots[self.op_index] = from_word._slots[from_word.op_index]
        self.extended_arith = from_word.extended_arith
        from_word.fill_rest_with_nops()
        from_word.type = INST
        from_word._addr = None
        from_word.addr_sym = None

    def resolve_symbol(self, symbols):
        if type(self.addr_sym) == int:
            self.set_addr(self.addr_sym)
        else:
            dest = symbols.get(self.addr_sym)
            if not dest:
                m = 'Call to undefined word: ->{}<-'.format(self.addr_sym)
                raise Exception(m)
            self.set_addr(dest.word_addr)

    def asm_op(self, slot, shift, xor_bits):
        op = self._slots[slot]
        if op is None:
            return 0
        if slot == 3:
            op >>= 2
        return (op ^ xor_bits) << shift

    def asm(self):
        # return assembled word
        typ = self.type
        if typ == CONST:
            w = self.const
        elif typ == INST or typ == ADDR:
            f = self.asm_op
            w = f(3, 0, 5) | f(2, 3, 10) | f(1, 8, 21) | f(0, 13, 10)
            if typ == ADDR:
                w |= self._addr
        return w

    def disasm(self, w):
        # disassemble W into this object
        addr_shift = 0
        for x in xor_bits2:
            op = ((w & 0x3e000) >> 13) ^ x
            w = (w << 5) & 0x3ffff
            addr_shift += 5
            self._slots[self.op_index] = op
            name = ops[op]
            if name in address_required:
                self._addr = w >> addr_shift
                self.type = ADDR
                break
            self.op_index += 1
            if name in ops_using_rest_of_word:
                break

    def inst_str(self):
        return ' '.join([ops[x] for x in self._slots if x is not None])

    def __str__(self):
        typ = self.type
        if typ == INST:
            return self.inst_str()
        if typ == CONST:
            return str(self.const)
        if typ == ADDR:
            return self.inst_str() + ' ' + str(self._addr)
        return 'Error unhandled word type'


def disasm_to_str(n):
    w = Word()
    w.disasm(n)
    return str(w)

def dis_list(lst):
    for w in lst:
        print(w, disasm_to_str(w))
