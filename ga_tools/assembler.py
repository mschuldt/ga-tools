
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
auto_nop_insert = True

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

@directive(':')
def start_def(p):
    name = p.read_word()
# TODO: this check will not work if word is used before being defined
#    if name in directives:
#        throw_error("name '{}' is reserved".format(name))
    node.start_def(name)

@directive('if')
def _if(_):
    node.compile_if('if')

@directive('-if')
def _if(_):
    node.compile_if('-if')

@directive('if:')
def _if_label(p):
    node.compile_call('if', p.read_word())

@directive('-if:')
def __if_label(p):
    node.compile_call('-if', p.read_word())

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

def optimize_plus(x):
    global auto_nop_insert
    auto_nop_insert = x
    if node:
        node.auto_nop_insert = x

@directive('enable_0_opt')
def _enable_0_opt(_):
    optimize_0(True)

@directive('disable_0_opt')
def _disable_0_opt(_):
    optimize_0(False)

@directive('enable_plus_opt')
def _enable_plus_opt(_):
    optimize_plus(True)

@directive('disable_plus_opt')
def _disable_plus_opt(_):
    optimize_plus(False)

@directive('org')
def _org(p):
    node.move_forward(p.read_int())

@directive(',')
def _comma(p):
    node.set_next_const(p.read_int())

@directive("'")
def _tick(p):
    name = p.read_word()
    word = node.symbols.get(name)
    if not word:
        raise_error('tick: undefined word ' + name)
    node.push(word)


def error_directive(msg):
    def fn(_):
        raise_error('parser error')
    return fn

# These words should be handled by the parser
for word in ('include', 'chip', 'node', 'asm',
             '\n', '(', '\\'):
    directives[word] = error_directive('parser error')
def set_chip(name):
    global chip
    chip = get_chips().get(name)
    if chip is None:
        chip = GA144(name)
    chip = chip

def set_node(coord):
    global node
    assert chip
    node = chip.set_node(coord)
    if node.finished:
        throw_error('Repeated node {}'.format(coord))
    node.compile_0_as_dup_dup_or = compile_0_as_dup_dup_or
    node.auto_nop_insert = auto_nop_insert

def process_call(reader, word):
    next_word = reader.peak()
    if next_word == ';':
        node.compile_call('jump', word)
        reader.read_word()
        return
    node.compile_call('call', word)

def process_aforth(coord, data):
    reader = TokenReader(data['tokens'], 'TODO')
    while True:
        w = reader.read_word()
        if not w:
            break
        fn = directives.get(w)
        if fn:

            fn(reader)
            continue
        n = parse_int(w)
        if n is None:
            process_call(reader, w)
        else:
            node.compile_constant(n)

def process_asm(coord, data):
    node.asm_node = True
    for line in data['tokens']:
        if type(line) is Token:
            exit()
        ops = [t.value for t in line]
        node.asm_word(ops, add_to_node=True)

def process_chip(nodes):
    for coord, data in nodes.items():
        if coord == 'global':
            continue
        set_node(coord)
        #node.symbols = data['labels']
        if data['asm']:
            process_asm(coord, data)
        else:
            process_aforth(coord, data)
        node.finish()

def process_include(parser, top_level=True):
    tokens = parser.parse()
    for chip, nodes in tokens.items():
        set_chip(chip)
        process_chip(nodes)

def do_compile():
    for chip in get_chips().values():
        chip.compile_nodes()

def print_nodes():
    chips = get_chips()
    print_names = len(chips) > 1
    for name, chip in chips.items():
        if print_names:
            print('chip:', name)
        nodes = list(chip.nodes.values())
        nodes.sort(key=lambda x: x.coord)
        for node in nodes:
            node.print()

def include_file(filename, top_level=True):
    '''digest FILENAME, which may have recursive includes'''
    p = Parser()
    p.set_file(filename)
    process_include(p, top_level)


def include_string(string):
    p = Parser()
    p.set_string(string)
    process_include(p, True)
