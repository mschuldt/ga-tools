#!/usr/bin/env python3

import ga_tools

tests_run = 0
failed_tests = []

def run_tests():
    global tests_run
    tests_run = 0
    failed_tests.clear()

    case('empty',
         '''node 1''',
         '''node 1 ASM''',
         {1: {'ram': []}})

    case('plus',
         '''node 1
            + + + . + . +''',

         '''node 1 asm
         . + . +
         . + . +
         . + ''',
         {1: {'ram': [180656, 180656, 180658]}})

    case('literals',
         '''node 1
            1 2 3 4 5 ''',

         '''node 1 ASM
         @p @p @p @p
         1
         2
         3
         4
         @p
         5''',
         {1: {'ram': [23831, 1, 2, 3, 4, 18866, 5]}})

    case('emptySlot4',
         '''node 1
         @p @p @p @p
         over over over over ''',

         '''node 1 ASM
         @p @p @p @p
         over over over .
         over
         ''',
         {1:{'ram':[23831, 135042, 133554]}})

    case('..',
         '''node 1
         dup .. dup dup .. dup dup dup .. dup dup dup dup ..
         dup .. .. dup
         ''',
         None,
        {1:{'ram':[149938, 150962, 150930, 150931, 149938, 149938]}} )

    case('comments',
         '''node 1
         ( a) dup ( lksdjf) 
         dup ( lksdjf)
         ( ) dup ( a)dup \\ lssd
         .. dup \\
( )
\\
( x) .. dup
\\ sd''',

         '''node 1 ASM
         dup dup dup dup \\ AAA
         dup \\
\\
\\ BBBB         
         dup \\ lskd   
         ''',
         {1:{'ram':[150931, 149938, 149938]}})

    case('if/then',
         '''node 1
         dup if then
         and if . then
         over if . . . . . then
         ''',
         ''' node 1 ASM
         dup if if_1
         : if_1
         and if if_2
         .
         : if_2
         over if if_3
         . . . .
         . . . .
         : if_3
         ''',
        {1:{'ram':[152321, 258819, 182706, 135942, 182706, 182706]}} )

    case('nested-if',
         '''node 1
         if dup if over if + then then then
         ''',

         '''
         node 1 ASM
         if if_1
         dup if if_1
         over if if_1
         +
         : if_1
         ''',
         {1:{'ram':[98308, 152324, 135940, 248242]}} )

    case('for/next',
         '''node 1
         for
         for . next
         for . . next
         for . . . next
         for . . . . . next
         next
         ''',

         '''node 1 ASM
         push
         : loop_1
         push
         : loop_2
         . next loop_2
         push
         : loop_3
         . . next loop_3
         push
         : loop_4
         . . . .
         next loop_4
         push
         : loop_5
         . . . .
         . next loop_5
         next loop_1
         ''',
        {1:{'ram':[190898, 190898, 184322, 190898, 182652, 190898,
                   182706, 122886, 190898, 182706, 184329, 122881]}} )

    case('for/unext',
         '''node 1
         for . unext
         for over dup unext
         for + !p  unext
         ''',

         '''node 1 ASM
         push
         . unext push
         over dup unext
         push
         + !p  unext
         ''',
         {1:{'ram':[190898, 184762, 134514, 190898, 252274]}})


    case('aforth+asm',
         '''node 100
         +
         @p

         node 200 ASM
         over
         dup

         node 300
         @
         !

         node 400 ASM
         4
         5
         ''',
         None,
         {100: {'ram': [180498]},
          200: {'ram': [133554, 149938]},
          300: {'ram': [15026]},
          400: {'ram': [4,5]}})

    case(':/call',
         '''node 1
         : zero
         dup
         : one
         : one2
         over
         : two
         zero one one2 dup two dup dup last
         : last
         ''',

         '''node 1 ASM
         : zero
         dup
         : one
         over
         : two
         call zero
         call one
         call one
         dup call two
         dup dup call last
         : last
         ''',
         {1: {'ram': [149938, 133554, 73728, 73729,
                      73729, 153090, 150863]}})

    case('call-return',
         '''node 1
         : x dup ;
         : test test ;
         : main test test ;
         over
         ''',
         None,
         {1: {'ram': [153010, 65537, 73729, 65537, 133554]}})

    case('large-address',
         '''node 1
         push pop if
         : test dup ;
         : test2 dup ;
         . .. . .. . .. . .. . ..
         ! !b test test2
         dup dup then or

         ''',
         None,
         {1: {'ram': [191666, 98317, 153010, 153010, 182706,
                      182706, 182706, 182706, 182706, 48050, 73730,
                      73731, 150962, 231858]}})

    case('call-before-def',
         '''node 1
         : x test test2 ;
         : test ;
         : test2 ;
         ''',

         '''node 1 ASM
         call test
         jump test2
         : test
         ;
         : test2
         ;
         ''',
         {1: {'ram': [73730, 65539, 84402, 84402]}})

    case('shifted-last-word',
         '''node 601
         io b! west a! 1 0
         : fib over over + dup ! fib''',
         None,
         {601: {'ram': [19218, 349, 469, 179603, 1, 231858,
                        135088, 154290, 73734]}})

    case(',',
         '''node 1
         , 1 dup , 2 , 0x3 over , 4
         ''',
         ''' node 1 ASM
         1
         dup over
         2
         3
         4''',
         {1: {'ram': [1, 151474, 2, 3, 4]}})

    case('org',
         '''node 1 org 0
         over

         node 2 org 5
         dup
         org 8
         over''',
         None,
         {1: {'ram': [133554]},
          2: {'ram': [79017, 79017, 79017, 79017, 79017, 149938,
                      79017, 79017, 133554]}})

    case('unext,',
         '''node 1
         unext, unext, dup dup
         !b unext, unext, .
         !b !b unext, unext,
         ''',
         None,
         {1: {'ram': [119187, 37234, 39796]}})

    case('coord',
         '''node 1 coord
         node 2 coord
         node 708 coord
         ''',
         None,
         {1: {'ram':[18866, 1]},
          2: {'ram': [18866, 2]},
          708: {'ram': [18866, 708]},})

    case('multicoord',
         '''node 1,2 dup
         node 3,4,5-7 +
         node 100-300 !
         node 101-101 @
         ''',
         None,
         {1: {'ram':[149938]},
          2: {'ram': [149938]},
          3: {'ram': [180658]},
          4: {'ram': [180658]},
          5: {'ram': [180658]},
          6: {'ram': [180658]},
          7: {'ram': [180658]},
          100: {'ram': [43442]},
          200: {'ram': [43442]},
          300: {'ram': [43442]},
          101: {'ram': [10674]}})

    case('if:/-if:',
         '''node 1
         : label1
         if: label1
         -if: label2
         @ -if: label2
         : label2
         : label3
         dup
         ''',
         None,
         {1: {'ram': [98304, 106499, 12803, 149938]}})

    case('while/-while',
         '''node 1
         3 for @ -while next dup then
         4 for ! while next ; then
         ''',
         None,
         {1: {'ram': [18610, 3, 12805, 122882, 149938, 18610,
                      4, 45834, 122887, 84402]}})
         

    case('include',
         '''node 1 dup
         include _test-include.ga
         node 3 over
         ''',
         None,
         {1: {'ram': [149938]},
          5: {'ram': [21938, 1, 21938, 2, 73730, 18933, 1]},
          6: {'ram': [21938, 1, 2, 84402, 73730, 18933, 1]},
          3: {'ram': [133554]}})

    case('rom',
         '''node 1 warm *.17 poly
         node 709 -dac
         node 705 18ibits
         node 708 18ibits
         ''',
         ''' node 1 ASM
         call warm
         call *.17
         call poly
         node 709 ASM
         call -dac
         node 705 ASM
         call 18ibits
         node 708 ASM
         call 18ibits''',
         {1: {'ram': [73897, 73904, 73898]},
          709: {'ram': [73916]},
          705: {'ram': [73945]},
          708: {'ram': [73931]}})

    case('ports',
         '''node 101
         -d-u rdlu ;''',

         '''node 101 ASM
         call -d-u
         jump rdlu''',
         {101: {'ram': [73989, 65957]}})

def error(coord, asm_type, name, msg):
    print('Node', coord, asm_type,
          "Error: Test '{}' - {}".format(name, msg))

def disasm_ram(node, expect):
    len_node = len(node)
    len_expect = len(expect)
    print('____got__________________________expected____________')
    for i in range(max(len_node, len_expect)):
        print(str(i).ljust(4), end='')
        if i < len_node:
            print(str(node[i]).ljust(6), '|',
                  ga_tools.disasm_to_str(node[i]).ljust(20), end='')
        else:
            print('Nothing'.ljust(29), end='')
        if i < len_expect:
            print(str(expect[i]).ljust(6), '|',
                  ga_tools.disasm_to_str(expect[i]))
        else:
            print('Nothing')
    print('ram=', node)
    print()

def cmp_json(asm_type, name, node, expect):
    json = node.json()
    #print('json:', json)
    for coord in expect.keys():
        if coord not in json:
            msg =  "key '{}' not found".format(coord)
            error(coord, asm_type, name, msg)
            return False
        node = json[coord]
        expt = expect[coord]
        for node_k in expt.keys():
            if node_k not in node:
                msg = "node '{}' key '{}' not found".format(coord, node_k)
                error(coord, asm_type, name, msg)
                return False
            node_val = node[node_k]
            expt_val = expt[node_k]
            if node_val != expt_val:
                msg = "value mismatch for '{}'".format(node_k)
                error(coord, asm_type, name, msg)
                if node_k == 'ram':
                    disasm_ram(node_val, expt_val)
                return False
    return True

def cmp_values(value, expect, test):
    if value != expect:
        fmt = 'Error: "{}" - value mismatch: {} != {}'
        print(fmt.format(test, value, expect))
        return False
    return True


def case(name, aforth, asm, expect, fn=lambda chip: True):
    print('TEST', name)
    global tests_run
    ga_tools.reset()
    if aforth:
            ga_tools.include_string('chip test_aforth\n'
                                    + aforth, __file__)
    if asm:
        ga_tools.include_string('chip test_asm\n' + asm, __file__)
    ga_tools.do_compile()
    chips = ga_tools.get_chips()
    ok = True
    if aforth:
        chip = chips.get('test_aforth')
        ok = cmp_json('Aforth', name, chip, expect)
        ok = ok and fn(chip)
    if asm:
        chip = chips.get('test_aforth')
        ok = cmp_json('ASM', name, chips.get('test_asm'), expect) and ok
        ok = ok and fn(chip)
    tests_run += 1
    if not ok:
        failed_tests.append(name)

def test_report():
    if not failed_tests:
        print('All {} tests passed.'.format(tests_run))
    else:
        print('{}/{} Tests failed:'.format(len(failed_tests), tests_run))
        print(failed_tests)

if __name__ == '__main__':
    run_tests()
    test_report()
