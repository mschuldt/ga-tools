
from .defs import *

addr_masks = (0x3ff, 0xff, 0x7)
xor_bits = (0b1010, 0b10101, 0b1010, 0b101)
xor_bits2 = (0b1010, 0b10101, 0b1010, 0b10100)

INST = 0
CONST = 1
ADDR = 2

class Word:
    def __init__(self, prev=None, addr=None):
        self._slots = [None, None, None, None]
        if prev:
            self.prev.next = self
        self.next = None
        self.prev = None
        self.symbol = None
        self._const = None # Ref type set for number literals
        self.op_index = 0 # Index of next empty slot
        # If word type is ADDR, op_index will be left
        # pointing to the last op before the address
        self.dest_word = None # forward transfer destination word
        self._addr = None # set when word contains an address
        # set to True when addr is not yet determined
        self.addr_sym = None # Ref
        self.addr_slot = None
        self.type = INST
        self.label = None
        self.word_addr = addr # address of this word in RAM
        self.extended_arith = 0
        self.stream = False

    def empty(self):
        #return self.op_index == 0
        return self._const is None and self._slots == [None, None, None, None]

    def fill_rest_with_nops(self):
        while self.op_index < 4:
            self.set_op(NOP)

    def set_op(self, op, final_slot=False):
        if self.op_index > 3:
            slots = [ops[self._slots[i]] for i in range(4)]
            throw_error('slot overflow: {}, {}'.format(slots, op))
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

    def set_const(self, const, tok=None):
        if type(const) == Ref:
            self._const = const
        else:
            self._const = Ref(value=const, tok=tok)
        self.type = CONST

    def get_const(self, required=True):
        return self._const.resolve(required)

    def set_call(self, op, name):
        assert type(name) == Ref
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

    def resolve_symbol(self):
        if type(self.addr_sym) == int:
            self.set_addr(self.addr_sym)
        else:
            dest = self.addr_sym.resolve()
            if dest is None:
                m = 'Unresolved symbol: ->{}<-'.format(
                    self.addr_sym.name)
                throw_error(m)
            self.set_addr(dest)

    def asm_op(self, slot, shift, xor_bits):
        op = self._slots[slot]
        if op is None:
            return 0
        if slot == 3:
            op >>= 2
        return (op ^ xor_bits) << shift

    def asm(self):
        # return assembled word
        if self.empty():
            return 0x134a9 # call warm
        typ = self.type
        if typ == CONST:
            w = self.get_const(True) & 0x3ffff
        elif typ == INST or typ == ADDR:
            f = self.asm_op
            w = f(3, 0, 5) | f(2, 3, 10) | f(1, 8, 21) | f(0, 13, 10)
            if typ == ADDR:
                w |= self._addr & addr_masks[self.op_index]
        return w

    def aforth_list(self):
        if self.type == CONST:
            return self.get_const(True) & 0x3ffff
        if self.type == INST:
            return [ops[op] if op else '.' for op in self._slots]
        if self.type == ADDR:
            x = [ops[op] for op in range(self.op_index)]
            x.append(self._addr)
            return x

    def disasm(self, w):
        # disassemble W into this object
        # TODO: to properly disassemble addresses need to know P
        addr_shift = 0
        for x in xor_bits2:
            op = ((w & 0x3e000) >> 13) ^ x
            w = (w << 5) & 0x3ffff
            addr_shift += 5
            self._slots[self.op_index] = op
            name = ops[op]
            if name in address_required:
                self._addr = (w >> addr_shift) & 0x1ff
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
            return str(self._const)
        if typ == ADDR:
            return self.inst_str() + ' ' + hex(self._addr)[2:]
        return 'Error unhandled word type'

class Ref:
    def __init__(self, node=None, name=None, value=None, tok=None):
        # a reference to the address of NAME in NODE
        self.node = node
        self.name = name
        self.value = value
        self.tok = tok

    def resolve(self, required=True):
        if self.value is not None:
            return self.value
        v = self.node.symbol_addr(self.name)
        if required and v is None:
            throw_error('unresolved reference: ' + self.name,
                        token=self.tok)
        # Don't cache value, it can change as words shift
        # self.value = v
        return v
    def __str__(self):
        v = self.resolve()
        if v is None:
            return "Ref('{}')".format(self.name)
        return str(v)

def disasm_to_str(n):
    w = Word()
    w.disasm(n)
    return str(w)

def dis_list(lst):
    for w in lst:
        print(w, disasm_to_str(w))
