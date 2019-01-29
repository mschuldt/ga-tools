
NOP='.'
XOR = 'or'
DUP = 'dup'
READ_P = '@p'

ops = (';', 'ex', 'jump', 'call', 'unext', 'next', 'if',
       '-if', READ_P, '@+', '@b', '@', '!p', '!+', '!b', '!',
       '+*', '2*', '2/', '-', '+', 'and', XOR, 'drop',
       DUP, 'pop', 'over', 'a', NOP, 'push', 'b!', 'a!')

op_i = {op:i for i, op in enumerate(ops)}

def get_op_i(op):
    x = op_i.get(op)
    return x

OP_NOP = get_op_i('.')

opcodes = frozenset(ops)

address_required = frozenset(['jump', 'call', 'next', 'if', '-if'])

last_slot_ops = frozenset([';', 'unext', '@p', '!p', '+*', '+',
                           'dup', '.'])

ops_preceded_by_nops = ('+', '+*')

ops_completing_carry = ('.', 'call', ';', 'if', '-if', 'next', 'unext')

ops_using_rest_of_word = (';', 'ex')

named_addresses = { 'right': 0x1D5,
                    'down': 0x115,
                    'left': 0x175,
                    'up': 0x145,
                    'io': 0x15D,
                    'ldata': 0x171,
                    'data': 0x141,
                    'warp': 0x157,
                    'center': 0x1A5,
                    'top': 0x1B5,
                    'side': 0x185,
                    'corner': 0x195 }

port_names = ('north', 'east', 'south', 'west',
              'up', 'right', 'down', 'left')

word_address_masks = (0x3ff, 0xff, 0x7)

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

UP = 0x145
DOWN = 0x115
RIGHT = 0x1d5
LEFT = 0x175
IO = 0x15d
DATA = 0x141

def parse_int(s):
    try:
        return int(s, 0)
    except ValueError:
        return None

def node_ports(coord):
    # Returns a tuple of addresses: (north, east, south, west)
    x = coord % 100
    y = coord // 100
    return ((DOWN, UP)[y % 2],
            (RIGHT, LEFT)[x % 2],
            (UP, DOWN)[y % 2],
            (LEFT, RIGHT)[x % 2])

def check_op(op):
    if op not in op_i:
        throw_error('invalid op: ' + str(op))

current_token = None

def set_current_token(t):
    global current_token
    if t and t != '\n':
        current_token = t

def throw_error(msg, print_source):
    if current_token and print_source:
        print('Exception:', msg)
        print('   Source:' , current_token.source,
              'line:', current_token.line,
              '~column:', current_token.col)
        exit()
    raise Exception(msg)

def valid_coord(coord):
  return coord >= 0 and coord%100 < 18 and coord // 100 < 8
