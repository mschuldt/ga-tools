
# ::::GA*
# ::::Tools

chips = {} # maps names to GA144 instances

from .defs import *
from .f18a_asm import *
from .ga144_rom import get_node_rom
from .word import Word

class GA144:
    def __init__(self, name):
        self.name = name
        self.nodes = {}
        self.current_node = None
        chips[name] = self

    def node(self, coord):
        n = self.nodes.get(coord)
        if not n:
            n = F18a(self, coord)
            self.set_rom(n)
            self.nodes[coord] = n
        return n

    def set_node(self, coord):
        if self.current_node == coord:
            return
        node = self.node(coord)
        self.current_node = node
        return node

    def compile_nodes(self):
        nodes = self.nodes.values()
        for node in nodes:
            node.set_word_addresses()
        aforth_nodes = []
        for node in nodes:
            if node.asm_node:
                node.resolve_calls()
                node.trim_last_word()
            else:
                node.shift_addr_words()
                node.resolve_transfers()
                aforth_nodes.append(node)
        for node in aforth_nodes:
            node.resolve_calls()
            node.trim_last_word()
        for node in aforth_nodes:
            node.insert_streams()
        self.delete_streams()

    def set_rom(self, node):
        rom = get_node_rom(node.coord)
        rom.update(io_places)
        node.symbol_names.extend(list(rom.keys()))
        node.rom_names.extend(node.symbol_names)
        for name, addr in rom.items():
            node.symbols[name] = Word(addr=addr)

    def new_stream(self, coord, into):
        s = Stream(self, self.node(coord), into=into)
        self.nodes[s.name] = s
        return s

    def delete_streams(self):
        # delete stream nodes so they don't show up in assembly output
        for coord, node in list(self.nodes.items()):
            if node.stream:
                del self.nodes[coord]

    def print_size(self, print_name=False):
        print('Node  Size  Percent')
        print('-------------------')
        if print_name:
            print('chip', self.name)
        nodes = list(self.nodes.items())
        nodes.sort()
        for coord, node in nodes:
            n = len(node.assemble())
            print(str(coord).ljust(5),str(n).ljust(5), str(n/64*100)+'%')

def get_chips():
    return chips

def get_chip(name=None):
    if name is not None:
        return get_chips().get(name)
    chips = list(get_chips().values())
    return len(chips) and chips[0]

def clear_chips():
    global chips
    chips = {}
