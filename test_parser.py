import pytest
from parser import Parser

# test case: Könisberg Ponies

sample_program = '''
sort pony 5
sort island 12


bridge(a, b) => bridge(b, a)
bridge(a, b) => access(a, b)
bridge(a, b), bridge(b, c) => access(a, c)

'''

complex_terms_program = '''

sort pony 12
sort island 13

at(pony, island) => blocked(island)
blocked.not (island b) ,
bridge (island a, island b) ,
at(pony, island a) =>
can go (pony, island b)

at(pony, island), at(pony.lover, island) => happy(pony)

happy(pony) => happy(pony.lover)

'''

# Test line breaks, spaces in terms, and functions
# in terms with spaces, and simple terms (such as "False")

program_with_line_breaks = '''

sort pony 1
sort island 666
sort exit 1

at.not(exit, all) => False

at(pony, island),
at.not(exit, island) =>
check off (pony, island)

at(pony, island),
at(exit, island) =>
escaped(pony)

can move (pony, island),
choose (pony, island) =>
at (pony.next, island)

can move.not (pony  , island ), choose (pony, island ) => False 

'''

sorted_program = '''
sort pony 10
sort gift add jewelry, clothing, flowers or stones, books, art, food, sweets

gives (some pony : pony, other pony : pony, thing : gift),
likes (other pony, thing),
birthday (other pony) =>
glad (other pony)

'''

# all accessible islands were already visited (go back) 

def test_preprocessing_a():
    raw_program = '''
        sort pony 5
        sort island 12


        bridge(a , b ) =>bridge(b , a)    
             bridge(a, b)=> access( a,b ) 
        bridge(a, b), bridge(b, c) => access(a, c)
        
    '''

    target_program = '''
sort pony 5
sort island 12


bridge(a, b) => bridge(b, a)
bridge(a, b) => access(a, b)
bridge(a, b), bridge(b, c) => access(a, c)

'''

    parser = Parser()
    result_program = parser.preprocess(raw_program)

    print(result_program)

    assert parser.preprocess(raw_program) == target_program

def test_parse():
    jorge = Parser().parser.parse(sample_program)
    manuel = Parser().parser.parse(Parser().preprocess(complex_terms_program))
    parse = Parser().parse(complex_terms_program)
    rogelio = Parser().parser.parse(sorted_program)

