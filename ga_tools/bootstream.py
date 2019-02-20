
from .defs import *
from .assembler import compile_string

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

    @staticmethod
    def set_a(node):
        return [('@p', 'a!', '.', '.'),
                node.get_init_a()]

    @staticmethod
    def set_b(node):
        return [('@p', 'b!', '.', '.'),
                node.get_init_b()]

    @staticmethod
    def set_io(node):
        return [('@p', '@p', 'b!', '.'),
                node.get_init_io(),
                0x15D, # io
                ('!b', '.', '.', '.')]

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

    def add_init_code(self, stream, node):
        if node.init_a:
            stream.extend(node.asm_words(self.set_a(node)))
        if node.init_io:
            stream.extend(node.asm_words(self.set_io(node)))
        if node.init_b:
            stream.extend(node.asm_words(self.set_b(node)))
        return stream

    def node_code(self, node, iport, oport, stream):
        # IPORT stream input port. OPORT output port
        stream_len = len(stream)
        s = [node.asm_word(('call', iport))] # focusing call
        # move previous code through this node
        if stream_len > 0:
            s.extend(node.asm_words(self.port_pump(oport, stream_len)))
            s.extend(stream)
        # then load this nodes code into ram
        code = node.assemble(check_size=True)
        s.extend(node.asm_words(self.load_pump(len(code))))
        s.extend(code)
        s.extend(node.assemble_boot_code())
        self.add_init_code(s, node)
        s.append(node.asm_word(('jump', node.start_addr())))
        return s

    def head_frame(self):
        # create bootstream for all nodes except boot node
        stream = []
        path = self.path
        if not path:
            return stream
        rpath = list(reversed(self.path))
        for node, p, p_out in zip(self.ordered_nodes(),
                                   [None]+rpath,
                                   rpath+[self.path[0]]):
            iport = node.port_addr(p_out, opposite=True)
            oport = p is not None and node.port_addr(p)
            stream = self.node_code(node, iport, oport, stream)
        # create the bootframe
        # boot frame format:
        #  0  completion(jump) address
        #  1  transfer (store) address
        #  2  transfer size in words
        #  3+ data words (if size != 0)
        addr = self.start_node().port_addr(self.path[0])
        return [0xae, addr, len(stream)] + stream

    def tail_frame(self):
        # create frame for boot node
        node = self.start_node()
        boot = node.assemble_boot_code()
        # TODO: Add this boot code earlier so it's visable with --print
        # TODO: how else to do this?
        boot.extend(self.add_init_code([],node))
        code = node.assemble()
        start = node.start_addr()
        if boot:
            boot.append(node.asm_word(('jump', start)))
            start = max(len(code), 0)
        code.extend(boot)
        return [start, 0, len(code)] + code

    def stream(self, _=None):
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

    def stream(self, serial_convert=True):
        s = super(AsyncBootstream, self).stream()
        if serial_convert:
            # Option to not do conversion for use by the simulator
            return self.sget_convert(s)
        return s

    def sget_convert(self, stream):
        new = []
        for w in stream:
            new.append((((w << 6) & 0xc0) | 0x2d) ^ 0xff)
            new.append(((w >> 2) & 0xff) ^ 0xff)
            new.append(((w >> 10) & 0xff) ^ 0xff)
        return new

class SyncBootstream(Bootstream):
    # Sync bootstream for loading in node 300
    def __init__(self, chip):
        super(SyncBootstream, self).__init__(chip)
        #path0 from DB004 page 31
        swse = [SOUTH] + [WEST]*16 + [SOUTH] + [EAST]*16
        sw = [SOUTH] + [WEST]*17
        self.path = ([NORTH]*4 + [EAST]*17 + swse + swse + sw
                     + [SOUTH] + [EAST]*17 + sw)
        self.start_coord = 300

class AsyncBootstream_GA4(AsyncBootstream):
    # Async bootstream for loading into GA4 node 0
    def __init__(self, chip):
        super(AsyncBootstream_GA4, self).__init__(chip)
        self.path = (NORTH, EAST, SOUTH)
        self.start_coord = 0

host_loader_code  = """
chip __host_loader__
node 608
  north a! west b!
  ( read stream length and pass a copy next node )
  @ dup !b
  ( send stream to next node )
  for @ !b unext
node 607 east a! west b! @ dup !b for @ !b unext
node 606 east a! west b! @ dup !b for @ !b unext
node 605 east a! west b! @ dup !b for @ !b unext
node 604 east a! west b! @ dup !b for @ !b unext
node 603 east a! west b! @ dup !b for @ !b unext
node 602 east a! west b! @ dup !b for @ !b unext
node 601 east a! west b! @ dup !b for @ !b unext
node 600 east a! south b! @ dup !b for @ !b unext
node 500 0x20000 io b! !b ( reset target chip)
 10000 for . . next
 0 !b
 north a! south b!
@ dup !b for @ !b unext
node 400 north a! south b! @ dup !b for @ !b unext
node 300
 ( reference: block 632 )
: dly !b 32 for unext ;
: 1bt dup dly 0x10000 or dly ;
: c+d+ 0x30003 1bt ; ( set clock high, data high, etc)
: c+d- 0x30002 1bt ;
: c-d+ 0x20003 1bt ;
: c-d- 0x20002 1bt ;
: bit0
   -if c+d+ ; then c+d- ;
: bit1
   -if c-d+ ; then c-d- ;
: send
  8 for
    bit0 2*
    bit1 2*
  next ;
: main
 north a! io b!
@ push @ 0x30000 dly send
pop -1 . + for @ send next
"""

class AsyncTargetBootstream():
      # bootstream that is loaded into target chip through
      # node 300 sync port
    def __init__(self, chip):
        self.target = SyncBootstream(chip)
        self.loader = None

    def loader_stream(self, length):
        chips = compile_string(host_loader_code)
        self.loader = AsyncBootstream(chips['__host_loader__'])
        return self.loader.head_frame()

    def start_node(self):
        return self.loader.start_node()

    def stream(self, serial_convert=True):
        target_stream = self.target.stream()
        target_stream = [len(target_stream)-1] + target_stream
        loader_bs = self.loader_stream(len(target_stream)-1)
        addr = self.start_node().port_addr(SOUTH)
        target_bs = [0xae, addr, len(target_stream)] + target_stream
        s = loader_bs + target_bs
        if serial_convert:
            s = self.loader.sget_convert(s)
        return s

class AsyncHostTargetBootstream():
    # bootstream for loading both 'host' and 'target' chips
    def __init__(self, chips):
        assert len(chips) == 2
        chipmap = {c.name:c for c in chips}
        if 'target' not in chipmap or 'host' not in chipmap:
            print('Mulitple chips must have names "host" and "target"')
            exit()
        self.host = AsyncBootstream(chipmap['host'])
        self.target = AsyncTargetBootstream(chipmap['target'])

    def stream(self, serial_convert=True):
        host_stream = self.host.stream(serial_convert)
        target_stream = self.target.stream(serial_convert)
        return target_stream + host_stream

bootstream_aliases = { 'async' : '708',
                       'async-target' :'708-300',
                       'target': '708-300' }

def make_bootstream(bootstream_type, chips):
    chip = chips[0]
    multiple_chips = len(chips) > 1
    bootstream_type = bootstream_aliases.get(bootstream_type,
                                             bootstream_type)
    if bootstream_type == '708':
        assert not multiple_chips
        return AsyncBootstream(chip)
    if bootstream_type == '300':
        assert not multiple_chips
        return SyncBootstream(chip)
    if bootstream_type == '708-300':
        if multiple_chips:
            return AsyncHostTargetBootstream(chips)
        return AsyncTargetBootstream(chip)
    if bootstream_type == 'ga4':
        return AsyncBootstream_GA4(chip)
    raise Exception('Invalid bootstream type: ' + str(bootstream_type))
