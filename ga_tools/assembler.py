
# ::::GA*
# ::::Tools

# GA144/F18a assembler

from .defs import *
from .ga144_asm import *
from .parse import *

import re

chip = None
node = None

directives = {}

compile_0_as_dup_dup_or = True
auto_nop_insert = True

baud=None

node_stack = []

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
    if name in directives:
        throw_error("name '{}' is reserved (directive)".format(name))
    # Removed this check for the SRAM code from greenarrays
    # elif name in node.rom_names:
    #     throw_error("name '{}' already defined (rom)".format(name))
    node.start_def(name)

@directive('boot')
def _start_boot(_):
    if not node.current_word.empty() or node.current_word.prev:
        throw_error('boot directive must be first in node definition')
    node.boot_code = True
    node.boot = node.current_word

@directive('if')
def _if(_):
    node.compile_if('if')

@directive('-if')
def _if(_):
    node.compile_if('-if')

@directive('if:')
def _if_label(p):
    node.compile_call('if', node.make_ref(p.read_word()))

@directive('-if:')
def __if_label(p):
    node.compile_call('-if', node.make_ref(p.read_word()))

@directive('then')
def _if(_):
    node.compile_then()

@directive('while')
def _while(_):
    node.compile_if('if')
    node.swap()

@directive('-while')
def __while(_):
    node.compile_if('-if')
    node.swap()

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

@directive('next:')
def _if_label(p):
    node.compile_call('next', node.make_ref(p.read_word()))

@directive('unext')
def _unext(_):
    node.compile_op('unext')
    node.pop()

@directive('unext,')
def _unext_comma(_):
    node.compile_op('unext')

def compile_without_nop(op):
    x = node.auto_nop_insert
    node.auto_nop_insert = False
    node.compile_op(op)
    node.auto_nop_insert = x

@directive('+,')
def _plus(_):
    compile_without_nop('+')

@directive('+*,')
def _plus(_):
    compile_without_nop('+*')

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

def read_ref(p):
    return node.make_ref(p.read_word())

@directive(',')
def _comma(p):
    node.set_next_const(read_ref(p))

@directive("'")
def _tick(p):
    word = p.read_word()
    # symbols.get is type Word, read_ref is type Ref
    # functions like compile_next expect a word to be on the stack,
    # not a reference.
    # todo - fix this by using references for everything.
    value = node.symbols.get(word)
    if not value:
        throw_error('tick: undefined word ' + str(word))
    node.push(value)

@directive("lit")
def _lit(p):
    #TODO: values from ' are Words so this does not work
    node.compile_constant(node.pop())

@directive('coord')
def _coord(_):
    node.compile_constant(node.coord)

@directive('/a')
def _init_a(p):
    node.init_a = read_ref(p)

@directive('/b')
def _init_b(p):
    node.init_b = read_ref(p)

@directive('/p')
def _init_p(p):
    node.init_p = read_ref(p)

@directive('/io')
def _init_io(p):
    node.init_io = read_ref(p)

def read_stream_options(r):
    into, thru = None, None
    while True:
        val = r.peak()
        if val == 'into':
            r.read_word() #discard
            into = r.read_coord()
            continue
        if val == 'thru':
            r.read_word() #discard
            thru = r.read_word()
            if thru not in ['!', '!b', '!p']:
                throw_error("invalid value for 'thru': " + thru)
            continue
        if into is None:
            throw_error("'stream{' requires 'node' argument")
        return into, thru

@directive('stream{')
def _start_stream(r):
    global node
    node_stack.append(node)
    into, thru = read_stream_options(r)
    stream = chip.new_stream(into, thru)
    node.start_stream(stream)
    node = stream

@directive('}stream')
def _end_stream(r):
    global node
    assert node.stream
    if not node_stack:
        throw_error('unmatched }stream')
    node.fill_rest_with_nops()
    node = node_stack.pop()

# { and } are implemented as a stream that have a limit
# to a single word and the current node as the destination node.

@directive('{')
def _start_asm(r):
    global node
    node_stack.append(node)
    stream = chip.new_stream(node.coord, None)
    stream.single_word = True
    node.start_stream1(stream)
    node = stream

@directive('}')
def _end_asm(r):
    global node
    assert node.stream
    if not node_stack:
        throw_error('unmatched }')
    node.fill_rest_with_nops()
    node = node_stack.pop()

def error_directive(msg):
    def fn(_):
        throw_error(msg)
    return fn

# These words should be handled by the parser
for word in ('include', 'chip', 'node', 'asm',
             '\n', '(', '\\', 'wire', 'into', 'thru'):
    directives[word] = error_directive('parser error: ' + word)

def set_baud(n):
    global baud
    baud = n

@directive('baud')
def _baud(_):
    node.compile_constant(baud)

@directive('unext_baud')
def _unext_baud(_):
    node.compile_constant(int((1/baud)/(2.4*10**-9)))

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
    ref = node.make_ref(word)
    if ref.node == node:
        if word not in node.symbol_names and not node.stream:
            #TODO: handle streams
            m = "node {} - name '{}' is not defined"
            throw_error(m.format(node.coord, word))
    next_word = reader.peak()
    if next_word == ';':
        node.compile_call('jump', ref)
        reader.read_word() # discard ;
        return
    node.compile_call('call', ref)

def process_aforth(coord, data):
    reader = data.token_reader(node)
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
    for line in data.tokens:
        if len(line) == 1 and line[0].value not in op_i:
            fn = directives.get(line[0].value)
            if fn:
                fn(None)
                continue
        if type(line) is not list:
            throw_error('why?')
        ops = [t.value for t in line]
        node.asm_word(ops, add_to_node=True)

def process_chip(nodes):
    for coord, data in nodes.items():
        set_node(coord)
        node.symbol_names.extend(data.symbols)
        if data.asm:
            process_asm(coord, data)
        else:
            process_aforth(coord, data)
        node.finish()

def process_include(parser, top_level=True):
    tokens = parser.parse()
    for chip, nodes in tokens.items():
        set_chip(chip)
        process_chip(nodes)

def include_file(filename, top_level=True):
    p = Parser()
    p.include_file(filename)
    process_include(p, top_level)

def include_string(string, source_file=None):
    p = Parser()
    p.include_string(string, source_file)
    process_include(p, True)

def do_compile():
    for chip in get_chips().values():
        chip.compile_nodes()

def compile_file(filename):
    clear_chips()
    include_file(filename)
    do_compile()
    return get_chips()

def compile_string(filename):
    clear_chips()
    include_string(filename)
    do_compile()
    return get_chips()

def print_nodes(simple=False, coord=None):
    chips = get_chips()
    print_names = len(chips) > 1
    for name, chip in chips.items():
        if print_names:
            print('\n\nchip:', name)
        nodes = list(chip.nodes.values())
        nodes.sort(key=lambda x: x.coord)
        for node in nodes:
            if coord is None or node.coord == coord:
                node.print(simple)
