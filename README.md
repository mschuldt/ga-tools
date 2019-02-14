
![logo](/images/logo_411x150.png)
---

Alternative tools for the [GA144](http://www.greenarraychips.com/home/products/index.html) multi-computer chip using Python3.

These tools are provided as a CLI script and a Python3 library.
They support two forms of assembly, bootstream generation and loading.

1. [Installation](#Installation)
2. [First program](#First-program)
3. [Usage](#Workflow)
4. [Assembly syntax](#Assembly-syntax)
   1. [Aforth syntax](#aforth-syntax)
   2. [ASM syntax](#ASM-syntax)
5. [Bootstreams](#Bootstreams)
6. [JSON output](#JSON-output)
7. [Documentation](#Documentation)
8. [Example code](#Example-code)
9. [GA144 Simulation](#GA144-Simulation)
10. [Example code](#Example-code)

# Installation
To install from pypi, run: `pip3 install ga_tools`

To install from source, first clone the repository and then run: `python setup.py install`

This will install the `ga` cli script and the `ga_tools` Python3 library.

# First program
To check that everything works, first connect the GA144 eval board or chip.
On GNU/Linux run `dmesg` to find the serial port it is connected on.
Try running the fibonacci.ga example:
```
  ga examples/fibonacci.ga --port /dev/ttyUSB0
```
Replace `/dev/ttyUSB0` with the correct serial port.
This should print out the first 15 numbers of the fibonacci
series before exiting.

# Usage
`ga -h` prints a summary of the cli options.

## Print assembly
`ga FILE.ga --print` prints a summary of the assembled program
for each node alongside its disassembly.
## Program loading
`ga FILE.ga --port NAME` streams the program into serial port NAME.

Use `--bootstream TYPE` to specify the bootstream type, default is 'async'.
See [Bootstreams](#Bootstreams) for more on the different bootstream types.

By default `ga` will listen for data being sent back from the ga144,
use option `--no-listen` to disable that.

## Show program size
`ga FILE --size` prints the RAM usage of each node.
## JSON output
`ga FILE.ga --json` prints the assembled program as JSON.
The bootstream is included with the `--bootstream TYPE` option.

use the `--outfile NAME` option to direct the JSON output to a file.

## Disabling optimization
The `--disable-0-opt` option prevents compiling '0' as 'dup dup or'.
The `--disable-plus-opt` options prevents automatic
insertions of no-ops before the + or +* instructions.

# Assembly syntax
These tools provide support for two forms of assembly.
The default form is called `aforth` and is similar to
arrayforth supported by the tools and documentation
provided by Greenarrays.

The second form is called `ASM` and is closer to a traditional assembly
language, with one line of source for every machine word.
This form is used when full transparency is needed
and can be useful for writing some kinds of optimization.

Both forms support the same basic instruction set.
Read about it [here](https://mschuldt.github.io/www.colorforth.com/inst.htm) or in the [F18a Product Brief](http://www.greenarraychips.com/home/documents/greg/PB003-110412-F18A.pdf).

Both forms are case insensitive.

## Aforth syntax
Aforth provides convient layer above raw assembly,
bringing its syntax closer to that of the Forth.
It allows reuse of existing code for the ga144 and helps with
use and comprehension of the valuable documentation from Greenarrays.
Additionally aforth syntax is easier for compilers to generate.

Aforth is intended to remain compatible with the output of the [chlorophyll](https://github.com/mangpo/chlorophyll) compiler.

TODO
## ASM syntax
To use asm syntax instead of aforth, use the `ASM` directive
after specifying the node coordinate, for example:
```
node 508 ASM
(...)
```
Each node that uses the asm syntax must be marked with `asm`.

`node`, `chip`, and other directives must start on a new line.

TODO
# Bootstreams
TODO
# JSON output
TODO
# Documentation

Greenarrays [documentation](http://www.greenarraychips.com/home/documents/index.html) is the valuable resource.

For a quick intro read the [GA144 Product Brief](http://www.greenarraychips.com/home/documents/greg/PB001-100503-GA144-1-10.pdf)
and the [F18a Product Brief](http://www.greenarraychips.com/home/documents/greg/PB003-110412-F18A.pdf)

For more serious programming the [F18A Technology reference](http://www.greenarraychips.com/home/documents/greg/DB001-171107-F18A.pdf)
and [GA144 Chip Reference](http://www.greenarraychips.com/home/documents/greg/DB002-110705-G144A12.pdf)
are very useful.

colorforth.com contained many pages useful for programming the ga144,
the site is down but mirrored here: [colorforth.com](https://mschuldt.github.io/www.colorforth.com/)
A list of useful colorforth.com links specific to the GA144 has been
collected [here](https://github.com/mschuldt/www.colorforth.com)

 - [Instructions](https://mschuldt.github.io/www.colorforth.com/inst.htm)

 - [Arithmetic routines](https://mschuldt.github.io/www.colorforth.com/arith.htm)

# GA144 Simulation

These tools do not currently provide a simulator, but they do
provide support for this emacs-based simulator:
[github.com/mschuldt/ga144-sim](https://github.com/mschuldt/ga144-sim)

After installation of that simulator, it can be run with:
`ga FILENAME --sim`

If the `--bootstream` option is provided it will simulate the
loading of the entire bootstream.This is disabled by default
as it's not usually interesting and is very slow.
The bootstream is only supported through node 708 in simulation.

# Example code
The examples/ directory provides numerous example programs
for the GA144.

See [examples/README.md](examples/README.md) for a summary of each one.

# Comparison to arrayforth
This version of aforth differs from arrayforth supported by Greenarrays
in several ways. Knowing the differences is helpful if you already
know arrayforth or if you want to use the Greenarrays documentation.

    - No semantic color
        - standard forth syntax for words and comments
        - hex,bin literals: 0xN, 0bN
        - boot descriptors and other yellow words are reserved keywords.
     - ~north~, ~east~, ~south~, and ~west~
         get resolved to correct ports: ~up~, ~down~, ~left~, or ~right~
     - Each node has a seporate namespace
         - word@coord compiles a call to =word= in node =coord=.
         - The word ~reclaim~ has no use.
     - Automatic nop insertion.
        - Can be disabled.
        - Currently inserts nops even when not actually needed
     - Arguments follow the yellow words.
         For example, use ~'node 715'~ instead of ~'715 node'~.
     - Generalized host computations during compilation are not supported.
         The compiler is not a forth interpreter.
     - There are no grey words
     - Automatically shift words when destination address does not fit in word.
        arrayforth does not compile in such situations, manual word alignment is necessary
     - words may be called before their definition
     - aforth does not support multiple labels at the same location

# Other GA144 tools

 * ga144tools (https://github.com/jamesbowman/ga144tools)[https://github.com/jamesbowman/ga144tools]
   - Assembler similar to the ASM supported here
   - Includes a flash based virtual machine and compiler for it.

 * Chlorophyll [https://github.com/mangpo/chlorophyll](https://github.com/mangpo/chlorophyll)
  - A high level c-like language with automatic partitioning for the ga144

 * Arrayforth [from Greenarrays](http://www.greenarraychips.com/home/support/download-02b.html)

# Todo

* Test Windows/mac support
* Proper guide to using aforth
* Fix line/col numbers in error messages
* GA144 Simulator
