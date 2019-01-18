![logo](/images/logo_411x150.png)

Alternative tools for the [GA144](http://www.greenarraychips.com/home/products/index.html) multi-computer chip using Python3.

These tools are provided as a simple CLI tool and a Python3 library.
They support two forms of assembly, bootstream generation and loading.

1. [Installation](#Installation)
2. [First program](#First-program)
3. [Assembly syntax](#Assembly-syntax)
   1. [aforth syntax](#aforth-syntax)
   2. [ASM syntax](#ASM-syntax)
4. [External documentation](#External-documentation)
   1. [Greenarrays docs](#Greenarrays-docs)
   2. [colorforth docs](#colorforth-docs)
5. [GA144 Simulation](#GA144-Simulation)
6. [Todo](#Todo)

# Installation
Install from pypi with `pip3 install ga_tools`

Or install from source:
```
git clone https://github.com/mschuldt/ga-tools.git
cd ga-tools
sudo python3 setup.py install
```

This will install the `ga` cli program and the `ga_tools` Python3 library.

# First program
To check that everything works, first connect the GA144 eval board or chip.
On GNU/Linux run `dmesg` to find the serial port it is connected on.
Try running the lucas series example program:
```
  ga examples/lucas-series.ga --port /dev/ttyUSB3 --baud 460800
```
Replace `/dev/ttyUSB3` with the correct serial port.
This should print out the first 15 numbers of the [lucas series](https://en.wikipedia.org/wiki/Lucas_number) before exiting

TODO: windows/mac installation


# Assembly syntax
These tools provide support for two forms of assembly.
The default form is called `aforth` and is similar to that
supported by the tools provided by Greenarrays. This makes
their aforth documentation useful. aforth is a thin layer
above assembly that brings its syntax close to that of the Forth.

The second form of assembly is closer to a traditional assembly
language, with one line of source for every machine word.
This form is used when full transparency is needed
and can be useful for writing some kinds of optimization.

Both forms are case insensitive.

## aforth syntax
TODO
## ASM syntax
To use asm syntax instead of aforth, use the `ASM` directive
after specifying the node coordinate, for example:
```
node 508 ASM
(...)
```
Each node that uses the asm syntax must be marked with `asm`.

TODO
# External documentation
## Greenarrays docs
TODO

## colorforth docs
[colorforth.com](https://mschuldt.github.io/www.colorforth.com/)
contains many pages useful for programming the ga144.

A collection of useful links specific to the GA144 has been
compiled [here](https://github.com/mschuldt/www.colorforth.com)

# GA144 Simulation

These tools do not currently provide a simulator.

A fully functional emacs-based simulator can be found at
[github.com/mschuldt/ga144](https://github.com/mschuldt/ga144)

TODO: how to use ga144 simulator with these tools

# Todo

* GA144 Simulator
* Test Windows/mac support
