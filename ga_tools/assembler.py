
# ::::GA*
# ::::Tools

# GA144/F18a assembler

from .defs import *
from .ga144_asm import *
from .parse import *

chip = None
node = None

directives = {}

compile_0_as_dup_dup_or = True
def directive(name):
    def decorator(fn):
        directives[name] = fn
    return decorator

def op_directive(op):
    def fn(_):
        node.compile_op(op)
    return fn

for op in opcodes:
    directives[op] = op_directive(op)

@directive('include')
def _include(p):
    include_file(p.read_word())

@directive('chip')
def _chip(p):
    set_chip(p.read_word())

def node_directive(p):
    global process_next
    process_next = process_next_aforth
    set_node(p.read_int())

@directive('node')
def _node(p):
    node_directive(p)

@directive('asm')
def _asm(_):
    global process_next
    node.asm_node = True
    process_next = process_next_asm

@directive(':')
def start_def(p):
    name = p.read_word()
# TODO: this check will not work if word is used before being defined
#    if name in directives:
#        raise Exception("name '{}' is reserved".format(name))
    node.start_def(name)

@directive('if')
def _if(_):
    node.compile_if('if')

@directive('-if')
def _if(_):
    node.compile_if('-if')

@directive('then')
def _if(_):
    node.compile_then()

def here():
    node.fill_rest_with_nops()
    node.push(node.current_word)

@directive('here')
def _here(_):
    here()

@directive('begin')
def _begin(_):
   here()

@directive('for')
def _for(_):
    node.compile_op('push')
    here()

@directive('next')
def _next(_):
    node.compile_next('next')

@directive('unext')
def _unext(_):
    node.compile_op('unext')
    node.pop()

@directive('end')
def _end(_):
    node.compile_next('end')

@directive('until')
def _until(_):
    node.compile_next('if')

@directive('-until')
def __until(_):
    node.compile_next('-if')

@directive('..')
def _align(_):
    node.fill_rest_with_nops()

@directive('+cy')
def _pcy(_):
    node.fill_rest_with_nops()
    node.extended_arith = 0x200

@directive('-cy')
def _mcy(_):
    node.fill_rest_with_nops()
    node.extended_arith = 0

@directive('\n')
def _nl(_):
    pass

@directive('(')
def _comment(p):
    p.skip_to(')')

@directive('\\')
def _linecomment(p):
    p.skip_to('\n')

def compile_const_directive(const):
    def fn(_):
        node.compile_constant(const)
    return fn

for name, addr in named_addresses.items():
    directives[name] = compile_const_directive(addr)

def compile_port_directive(port):
    def fn(_):
        node.compile_port(port)
    return fn

for port_index, name in enumerate(('north', 'east', 'south', 'west')):
    directives[name] = compile_port_directive(port_index)

def optimize_0(x):
    global compile_0_as_dup_dup_or
    compile_0_as_dup_dup_or = x
    if node:
        node.compile_0_as_dup_dup_or = x

def set_chip(name):
    global chip
    chip = get_chips().get(name)
    if chip is None:
        chip = GA144(name)
    chip = chip

def set_node(coord):
    global node
    if not chip:
        set_chip('__default')
    if node:
        node.finish()
    node = chip.set_node(coord)
    if node.finished:
        raise Exception('Repeated node {}'.format(coord))
    node.compile_0_as_dup_dup_or = compile_0_as_dup_dup_or

def process_call(parser, word):
    next_word = parser.read_word()
    if next_word == ';':
        node.compile_call('jump', word)
        return
    parser.unread()
    node.compile_call('call', word)

def process_next_aforth(parser):
    w = parser.read_word()
    if w is None:
        return False
    if w not in ('node', 'chip', '\n') and not node:
        raise Exception('node is unset')
    fn = directives.get(w)
    if fn:
        fn(parser)
    else:
       n = parse_int(w)
       if n is None:
           process_call(parser, w)
       else:
           node.compile_constant(n)

    return True

def check_asm_exit(parser):
    global process_next
    while True:
        w = parser.read_word()
        if w is None or w != '\n':
            break
    if w is None:
        return False
    if w == 'node':
        node_directive(parser)
        process_next = process_next_aforth
        return True
    if w == 'chip':
        set_chip(parser.read_word())
        process_next = process_next_aforth
        return True
    parser.unread()
    return False

def process_next_asm(parser):
    if check_asm_exit(parser):
        return True
    ops = parser.read_line()
    if not ops and parser.eof():
        return False
    if not ops: # empty line
        return True
    if not node:
        raise Exception('node is unset')
    node.asm_word(ops, add_to_node=True)
    return True

process_next = process_next_aforth

def process_include(parser):
    while process_next(parser):
        pass
    if node:
        node.finish()

def do_compile():
    for chip in get_chips().values():
        chip.compile_nodes()

def print_nodes():
    chips = get_chips()
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

def include_string(string):
    p = Parser()
    p.set_string(string)
    process_include(p)
