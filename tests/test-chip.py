#!/usr/bin/env python3

import argparse

import ga_tools

parser = argparse.ArgumentParser()
parser.add_argument('--port',
                    nargs=1,
                    help='Serial port')
parser.add_argument('--baud',
                    nargs=1,
                    default=[460800],
                    help='Serial port baud rate. Default=460800')

args = parser.parse_args()


ga_tools.set_baud(args.baud[0])

program = '''
node 708
: send 0 _send8 drop _send8 _send8
: _send8 0 _send1 7 for dup _send1 2/ next 1
: _send1 1 and 3 or !b unext_baud for unext ;
: exit 1 _send8 ;
: main coord send 1 4 + send exit
'''
ga_tools.include_string(program)
ga_tools.do_compile()


chip = ga_tools.get_chip()


serial = ga_tools.GA144Serial([chip], args.port[0], args.baud[0])

serial.write_bootstream('708')
serial.gather() # TODO: timeout

assert serial.data == [708, 5]
print('ok')
