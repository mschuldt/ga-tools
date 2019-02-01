
from .defs import named_addresses, io_places


extra_names = dict(named_addresses)
extra_names.update(io_places)

def get_node_rom(coord):
    rom = node_rom_type.get(coord, basic_rom)
    rom.update(extra_names)
    return rom


# block 1418  math rom anywhere

basic_rom  = {"relay": 0xa1, # 1388
              "warm": 0xa9,  # warm
              "*.17": 0xb0, # 1390  multiply
              "*.": 0xb7, # 1396  fractional multiply
              "taps": 0xbc, # 1386
              "interp": 0xc4, # 1384  interpolate
              "triangle": 0xce, # 1394
              "clc": 0xd3, # 1398
              "--u/mod": 0x2d5,  # 1398
              "-u/mod": 0x2d6, # 1398
              "poly": 0xaa} # 1382  polynomial approximation

# block 1432  analog
analog_rom = {"relay": 0xa1, # 1388
              "warm": 0xa9,  # warm
              "*.17": 0xb0, # 1390  multiply
              "*.": 0xb7, # 1396  fractional multiply
              "-dac": 0xbc, # 1434
              "interp": 0xc4, # 1384  interpolate
              "triangle": 0xce, # 1394
              "clc": 0xd3, # 1398
              "--u/mod": 0x2d5,  # 1398
              "-u/mod": 0x2d6, # 1398
              "poly": 0xaa} # 1382  polynomial approximation

# block 1420  serdes top/bot
serdes_boot_rom = {"relay": 0xa1, # 1388
                   "warm": 0xa9,
                   "cold": 0xaa,
                   "*.17": 0xb0, # 1390  multiply
                   "*.": 0xb7, # 1396  fractional multiply
                   "taps": 0xbc, # 1386
                   "interp": 0xc4, # 1384  interpolate
                   "triangle": 0xce, # 1394
                   "clc": 0xd3, # 1398
                   "--u/mod": 0x2d5,  # 1398
                   "-u/mod": 0x2d6, # 1398
                   "poly": 0xaa} # 1382  polynomial approximation

# block 1422  sync serial boot side
sync_boot_rom  = {"relay": 0xa1, # 1388
                  "warm": 0xa9,
                  "cold": 0xaa,
                  "ser-exec": 0xb6,
                  "ser-copy": 0xb9,
                  "sget": 0xbe,
                  "6in": 0xc0,
                  "2in": 0xc2,
                  "*.17": 0xcc, # 1390  multiply
                  "taps": 0xd3, # 1386
                  "triangle": 0xdb} # 1394

# block 1424  async serial boot top/bot
async_boot_rom  = {"relay": 0xa1, # 1388
                   "warm": 0xa9,
                   "cold": 0xaa,
                   "ser-exec": 0xae,
                   "ser-copy": 0xb3,
                   "wait": 0xbb,
                   "sync": 0xbe,
                   "start": 0xc5,
                   "delay": 0xc8,
                   "18ibits": 0xcb, # 1426
                   "byte": 0xd0, # 1426
                   "4bits": 0xd2, # 1426
                   "2bits": 0xd3, # 1426
                   "1bit": 0xd4, # 1426
                   "lsh": 0xd9, # 1392
                   "rsh": 0xdb}
# 1392 ;???????

# block 1428  spi boot top/bot
spi_boot_rom = {"relay": 0xa1, # 1388
                "warm": 0xa9,
                "8obits": 0xc2,
                "ibit": 0xc7,
                "half": 0xca,
                "select": 0xcc,
                "obit": 0xd0,
                "rbit": 0xd5,
                "18ibits": 0xd9,
                #?? ibits, u2/
                # block 1430
                         "cold": 0xaa,
                "spi-boot": 0xb0,
                "spi-exec": 0xb6,
                "spi-copy": 0xbc}

# block 1436  1-wire
one_wire_rom = {"rcv": 0x9e,
                "bit": 0xa1,
                "warm": 0xa9,
                "cold": 0xaa,
                "triangle": 0xbe, # 1394
                "*.17": 0xc3, # 1390
                "*.": 0xca, # 1396
                "interp": 0xcf, # 1384
                "clc": 0xcf, # 1398
                "--u/mod": 0x2d1,  # 1398
                "-u/mod": 0x2d2} # 1398 #TODO: check

# node 9 block 1320
SDRAM_addr_rom = {"warm":  0xa9,
                  "cmd": 0xaa}

# node 8 block 1322
SDRAM_control_rom = {"warm":  0xa9}

 # node 7 block 1324
SDRAM_data_rom = {"warm": 0xa9,
                  "db@": 0xaa,
                  "db!": 0xb,
                  "inpt": 0xad}

 # node 105 block 1306
eForth_bitsy_rom = {"warm":  0xa9,
                    "rp--": 0xaa,
                    "bs@": 0xac,
                    "'else": 0xac,
                    "rp@": 0xb0,
                    "pshbs": 0xb1,
                    "'r@": 0xb3,
                    "@w": 0xb4,
                    "rfrom": 0xb6,
                    "popbs": 0xb9,
                    "pshr": 0xbb,
                    "rp++": 0xbf,
                    "ip++": 0xbf,
                    "tor": 0xc1,
                    "rp!": 0xc4,
                    "'con": 0xc7,
                    "'var": 0xc8,
                    "'exit": 0xc9,
                    "bitsy": 0xce,
                    "xxt": 0xd0,
                    "'ex": 0xd3,
                    "'lit": 0xd5,
                    "'if": 0xd8}

#node 106 block 1310
eForth_stack_rom= {"warm": 0xa9,
                   "'c@": 0xaa,
                   "'@": 0xaa,
                   "x@": 0xaa,
                   "sp++": 0xac,
                   "char+": 0xac,
                   "cell+": 0xac,
                   "1+": 0xac,
                   "popt": 0xae,
                   "sp--": 0xb0,
                   "char-": 0xb0,
                   "cell-": 0xb0,
                   "1-": 0xb0,
                   "psht": 0xb2,
                   "x!": 0xb4,
                   "'c!": 0xb6,
                   "'!": 0xb6,
                   "popts": 0xb7,
                   "pops": 0xb8,
                   "pshs": 0xba,
                   "page@": 0xbc,
                   "pshw": 0xbe,
                   "page!": 0xc0,
                   "sp@": 0xc3,
                   "sp!": 0xc6,
                   "'drop": 0xc8,
                   "'over": 0xc9,
                   "'dup": 0xca,
                   "'swap": 0xcb,
                   "'2/": 0xcd,
                   "um+": 0xcf,
                   "'nc": 0xd2,
                   "'cy": 0xd3,
                   "zless": 0xd8,
                   "'or": 0xdb,
                   "'xor": 0xdc,
                   "'and": 0xdd,
                   "negate": 0xde,
                   "invert": 0xdf,
                   "zeq": 0xe0,
                   "'+": 0xe2,
                   "swap-": 0xe3 }

# node 107 block 1328
SDRAM_mux_rom = {"warm": 0xa9,
                 "a2rc": 0xaa,
                 "row!": 0xaf,
                 "sd@": 0xbb,
                 "sd!": 0xc5,  #TODO: sd! and poll are not in dumped rom
                 "poll": 0xcf}

SDRAM_idle_rom = {"warm":  0xa9,
                  "noop": 0xaa,
                  "cmd": 0xac,
                  "idle": 0xae,
                  "init": 0xc0}

node_rom_type = {300: sync_boot_rom,
                 708: async_boot_rom,
                 705: spi_boot_rom,
                 200: one_wire_rom,
                 9: SDRAM_addr_rom,
                 8: SDRAM_control_rom,
                 7: SDRAM_data_rom,
                 105: eForth_bitsy_rom,
                 106: eForth_stack_rom,
                 107: SDRAM_mux_rom,
                 108: SDRAM_idle_rom,
                 1: serdes_boot_rom,
                 107: serdes_boot_rom,
                 709: analog_rom,
                 713: analog_rom,
                 717: analog_rom,
                 617: analog_rom,
                 117: analog_rom}
