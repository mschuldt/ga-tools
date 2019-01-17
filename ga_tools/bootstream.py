
from .defs import *

class Bootstream:
    def __init__(self, chip):
        self.chip = chip

    @staticmethod
    def port_pump(port, stream_len):
        return [('@p', 'dup', 'a!', '.'),
                ('call', port),
                ('@p', 'push', '!', '.'),
                stream_len - 1,
                ('@p', '!', 'unext', '.')]

    @staticmethod
    def load_pump(code_len):
        if code_len == 0:
            return [(';')]
        return [('@p', 'a!', '@p', '.'),
                0,
                code_len - 1,
                ('push', '.', '.', '.'),
                ('@p', '!+', 'unext', '.')]

    def start_node(self):
        return self.chip.node(self.start_coord)

    def ordered_nodes(self):
        # constructs a list of nodes in bootstream order
        coord_changes = (100, 1, -100, -1)
        coord = self.start_coord
        nodes = []
        for direction in self.path:
            coord += coord_changes[direction]
            nodes.append(self.chip.node(coord))
        return reversed(nodes)

    def node_boot_code(self, node, iport, oport, stream):
        # IPORT stream input port. OPORT output port
        stream_len = len(stream)
        s = [node.asm_word(('call', iport))] # focusing call
        # move previous code through this node
        if stream_len > 0:
            s.extend(node.asm_words(self.port_pump(oport, stream_len)))
            s.extend(stream)
        # then load this nodes code into ram
        code = node.assemble()
        s.extend(node.asm_words(self.load_pump(len(code))))
        if code:
            s.extend(code)
            s.append(node.asm_word(('jump', node.start_addr())))
        return s

    def head_frame(self):
        # create bootstream for all nodes except boot node
        stream = []
        path = self.path
        rpath = list(reversed(self.path))
        for node, p, p_out in zip(self.ordered_nodes(),
                                   [None]+rpath,
                                   rpath+[self.path[0]]):
            iport = node.port_addr(p_out, opposite=True)
            oport = p is not None and node.port_addr(p)
            stream = self.node_boot_code(node, iport, oport, stream)
        # create the bootframe
        addr = self.start_node().port_addr(self.path[1])
        return [0xae, addr, len(stream)] + stream

    def tail_frame(self):
        # create frame for boot node
        node = self.start_node()
        code = node.assemble()
        return [node.start_addr(), 0, len(code)] + code

    def stream(self):
        # creates the bootstream
        s = self.head_frame()
        s.extend(self.tail_frame())
        return s

    def stream_str(self):
        return ''.join(map(chr, self.stream()))

class AsyncBootstream(Bootstream):
    # Async bootstream for loading in node 708
    def __init__(self, chip):
        super(AsyncBootstream, self).__init__(chip)
        # DB004 page 31
        nenw = [NORTH] + [EAST]*16 + [NORTH] + [WEST]*16
        self.path = ([EAST]*9 + [SOUTH]*7 + [WEST]*17
                     + nenw + nenw + nenw + [NORTH] + [EAST]*7)
        self.start_coord = 708

    def stream(self):
        return self.sget_convert(super(AsyncBootstream, self).stream())

    def sget_convert(self, stream):
        new = []
        for w in stream:
            new.append((((w << 6) & 0xc0) | 0x2d) ^ 0xff)
            new.append(((w >> 2) & 0xff) ^ 0xff)
            new.append(((w >> 10) & 0xff) ^ 0xff)
        return new

def make_bootstream(bootstream_type, chip):
    if bootstream_type == 'async':
        return AsyncBootstream(chip)
    raise Exception('Invalid bootstream type: ' + str(bootstream_type))
