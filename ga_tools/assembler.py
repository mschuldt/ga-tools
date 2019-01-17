
# ::::GA*
# ::::Tools

# GA144/F18a assembler

from .defs import *
from .ga144 import *

current_chip = None
current_node = None

directives = {}

def directive(name):
    def decorator(fn):
        directives[name] = fn
    return decorator

def read_int(i):
    return int(next(i), 0)

def read_word(i):
    return next(i).strip().lower()

def op_directive(op):
    def fn(i):
        current_node.compile_op(op)
    return fn

for op in opcodes:
    directives[op] = op_directive(op)

@directive('include')
def _include(i):
    include_file(read_word(i))

@directive('chip')
def _chip(i):
    set_current_chip(read_word(i))

@directive('node')
def _node(i):
    global process_line
    process_line = process_line_aforth
    set_current_node(read_int(i))

@directive('ASM')
def _asm(i):
    global process_line
    current_node.asm_node = True
    process_line = process_line_asm

@directive(':')
def start_def(i):
    current_node.start_def(read_word(i))

@directive('if')
def _if(i):
    current_node.compile_if('if')

@directive('-if')
def _if(i):
    current_node.compile_if('-if')

@directive('then')
def _if(i):
    current_node.compile_then()

def here():
    current_node.fill_rest_with_nops()
    current_node.push(current_node.current_word)

@directive('here')
def _here(i):
    here()

@directive('begin')
def _begin(i):
   here()

@directive('for')
def _for(i):
    current_node.compile_op('push')
    here()

@directive('next')
def _next(i):
    current_node.compile_next('next')

@directive('unext')
def _unext(i):
    current_node.compile_op('unext')
    current_node.pop()

@directive('end')
def _end(i):
    current_node.compile_next('end')

@directive('until')
def _until(i):
    current_node.compile_next('if')

@directive('-until')
def __until(i):
    current_node.compile_next('-if')

@directive('..')
def _align(i):
    current_node.fill_rest_with_nops()

@directive('+cy')
def _pcy(i):
    current_node.fill_rest_with_nops()
    current_node.extended_arith = 0x200

@directive('-cy')
def _mcy(i):
    current_node.fill_rest_with_nops()
    current_node.extended_arith = 0

def compile_const_directive(const):
    def fn(i):
        current_node.compile_constant(const)
    return fn

for name, addr in named_addresses.items():
    directives[name] = compile_const_directive(addr)

def compile_port_directive(port):
    def fn(i):
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

def process_line_aforth(line):
    i = iter(line.split())
    for word in i:
        w = word.strip()
        fn = directives.get(w)
        if fn:
            fn(i)
        else:
            process_number(w)

def process_line_asm(line):
    ops = line.split()
    if not ops:
        return
    current_node.asm_word(ops, add_to_node=True)

process_line = process_line_aforth

def process_include(text):
    for line in text.split('\n'):
        process_line(line.strip())

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
    f = open(filename)
    process_include(f.read())
    f.close()

def include(filename):
    include_file(filename)
    if current_node:
        current_node.finish()
