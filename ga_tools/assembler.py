
# ::::GA*
# ::::Tools

# GA144/F18a assembler

from .defs import *
from .ga144 import *
from .parse import *

current_chip = None
current_node = None

directives = {}

def directive(name):
    def decorator(fn):
        directives[name] = fn
    return decorator

def op_directive(op):
    def fn(_):
        current_node.compile_op(op)
    return fn

for op in opcodes:
    directives[op] = op_directive(op)

@directive('include')
def _include(p):
    include_file(p.read_word())

@directive('chip')
def _chip(p):
    set_current_chip(p.read_word())

def node_directive(p):
    global process_next
    process_next = process_next_aforth
    set_current_node(p.read_int())

@directive('node')
def _node(p):
    node_directive(p)

@directive('ASM')
def _asm(_):
    global process_next
    current_node.asm_node = True
    process_next = process_next_asm

@directive(':')
def start_def(p):
    current_node.start_def(p.read_word())

@directive('if')
def _if(_):
    current_node.compile_if('if')

@directive('-if')
def _if(_):
    current_node.compile_if('-if')

@directive('then')
def _if(_):
    current_node.compile_then()

def here():
    current_node.fill_rest_with_nops()
    current_node.push(current_node.current_word)

@directive('here')
def _here(_):
    here()

@directive('begin')
def _begin(_):
   here()

@directive('for')
def _for(_):
    current_node.compile_op('push')
    here()

@directive('next')
def _next(_):
    current_node.compile_next('next')

@directive('unext')
def _unext(_):
    current_node.compile_op('unext')
    current_node.pop()

@directive('end')
def _end(_):
    current_node.compile_next('end')

@directive('until')
def _until(_):
    current_node.compile_next('if')

@directive('-until')
def __until(_):
    current_node.compile_next('-if')

@directive('..')
def _align(_):
    current_node.fill_rest_with_nops()

@directive('+cy')
def _pcy(_):
    current_node.fill_rest_with_nops()
    current_node.extended_arith = 0x200

@directive('-cy')
def _mcy(_):
    current_node.fill_rest_with_nops()
    current_node.extended_arith = 0

@directive('\n')
def _nl(_):
    pass

def compile_const_directive(const):
    def fn(_):
        current_node.compile_constant(const)
    return fn

for name, addr in named_addresses.items():
    directives[name] = compile_const_directive(addr)

def compile_port_directive(port):
    def fn(_):
        current_node.compile_port(port)
    return fn

for port_index, name in enumerate(('north', 'east', 'south', 'west')):
    directives[name] = compile_port_directive(port_index)

def set_current_chip(name):
    global current_chip
    chip = chips.get(name)
    if chip is None:
        chip = GA144(name)
    current_chip = chip

def set_current_node(coord):
    global current_node
    if not current_chip:
        set_current_chip('__default')
    if current_node:
        current_node.finish()
    current_node = current_chip.set_node(coord)

def process_number(word):
    n = parse_int(word)
    if n is None:
        current_node.compile_call(word)
    else:
        current_node.compile_constant(n)

def process_next_aforth(parser):
    w = parser.read_word()
    if w is None:
        return False
    fn = directives.get(w)
    if fn:
        fn(parser)
    else:
        process_number(w)
    return True

def check_asm_exit(parser):
    global process_next
    w = parser.read_word()
    if w == 'node':
        node_directive(parser)
        process_next = process_next_aforth
        return True
    if w == 'chip':
        set_current_chip(parser.read_word())
        process_next = process_next_aforth
        return True
    parser.unread()
    return False

def process_next_asm(parser):
    if check_asm_exit(parser):
        return True
    ops = parser.next_line()
    if not ops:
        return False
    current_node.asm_word(ops, add_to_node=True)
    return True

process_next = process_next_aforth

def process_include(parser):
    while process_next(parser):
        pass

def do_compile():
    for chip in chips.values():
        chip.compile_nodes()

def print_nodes():
    print_names = len(chips) > 1
    for name, chip in chips.items():
        if print_names:
            print('chip:', name)
        for node in chip.nodes.values():
            node.print()

def include_file(filename):
    '''digest FILENAME, which may have recursive includes'''
    p = Parser()
    p.set_file(filename)
    process_include(p)

def include(filename):
    include_file(filename)
    if current_node:
        current_node.finish()
