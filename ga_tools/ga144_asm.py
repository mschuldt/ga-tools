
# ::::GA*
# ::::Tools

chips = {} # maps names to GA144 instances

from .defs import *
from .ga_serial import *
from .bootstream import *
from .f18a_asm import *

class GA144:
    def __init__(self, name):
        self.name = name
        self.nodes = {}
        self.current_node = None
        chips[name] = self
        self.serial = None

    def node(self, coord):
        n = self.nodes.get(coord)
        if not n:
            n = F18a(coord)
            self.nodes[coord] = n
        return n

    def set_serial(self, port, speed):
        self.serial = GA144Serial(port, speed)

    def write_bootstream(self, bootstream_type):
        assert(self.serial)
        bs = make_bootstream(bootstream_type, self)
        self.serial.write_bootstream(bs.stream())

    def set_node(self, coord):
        if self.current_node == coord:
            return
        node = self.node(coord)
        self.current_node = node
        return node

    def compile_nodes(self):
        for node in self.nodes.values():
            if node.asm_node:
                node.set_word_addresses()
                node.resolve_calls()
                node.trim_last_word()
            else:
                node.set_word_addresses()
                node.resolve_transfers()
                node.resolve_calls()
                node.trim_last_word()

    def json(self, bootstream_type=None):
        data = {coord:node.json() for coord, node in self.nodes.items()}
        if bootstream_type:
            bs = make_bootstream(bootstream_type, self)
            data['bootstream'] = bs.stream()
        return data

    def print_size(self):
        print('Node  Size  Percent')
        print('-------------------')
        for coord, node in self.nodes.items():
            n = len(node.assemble())
            print(str(coord).ljust(5),str(n).ljust(5), str(n/64*100)+'%')

def get_chips():
    return chips

def reset():
    global chips
    chips = {}
