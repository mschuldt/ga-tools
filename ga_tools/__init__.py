
from .ga144_asm import *
from .assembler import *
from .ga_serial import *
from .bootstream import *

version = 0.2


def chip_json(chip, bootstream_type=None, simulation=False):
    data = {'nodes': {coord:node.json() for coord, node
                      in chip.nodes.items()}}
    if bootstream_type:
        bs = make_bootstream(bootstream_type, [chip])
        data['bootstream'] = {'type':bootstream_type,
                              'node': bs.start_coord,
                              'stream': bs.stream(not simulation)}
    return data

