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

gives (some pony : pony, some pony . sibling, thing : gift) =>
glad (some pony . sibling)
'''

# all accessible islands were already visited (go back) 

comments = '''-- This is a comment at the very beginning --
sort pony 10
-- This is a comment between sorts, without a newline in between --

sort gift add jewelry, clothing, flowers or stones, books, art, food, sweets

-- These are incomplete declarations for an odd spec
about ponies. Mind you, this comment and the comment before
include punctuation, and in addition to that, this one two newlines --
gives (some pony : pony, other pony : pony, thing : gift),
likes (other pony, thing),
birthday (other pony) =>
glad (other pony)

-- Ok, one more comment --

gives (some pony : pony, some pony . sibling, thing : gift) =>
glad (some pony . sibling)

-- Aaand two comments at the end
--

-- hehe --
'''

disjunctions = '''-- This program contains disjunctions --
sort pony 4

tall (p : pony) v short(p)

cool (p : pony) v
cute (p) v
stern (p)

orderly (p : pony), messy(q : pony) =>
deeply loathes (p, q)

deeply loathes (p : pony, q : pony) =>
deeply loathes (q, p)
'''

complete = '''--- A fairly complete program, useful for testing model unfolding --

-- There are ten ponies and ten islands --

sort pony 10
sort island 10

-- No pony can be nowhere, and no pony can be somehwere and nowhere simultaneously --

somewhere(p : pony) v nowhere (p)
somehwere(p), nowhere(p) => False

at(p : pony, i : island) => somewhere(p)
nowhere(p : pony), at(p, i: island) => False

-- Ponies who hate each other can't be at the same island --

loathes (p: pony, q: pony),
loathes(q, p), at(p, i: island),
at(q, i) => False

-- Hatred is symmetrical for ponnies --

loathes (p : pony, q: pony) =>
loathes (q, p)

'''

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
    parser = Parser()

    jorge = parser.parse(sample_program)
    manuel = parser.parse(complex_terms_program)
    rogelio = parser.parse(sorted_program)
    egberto = parser.parse(complex_terms_program)
    jonacio = parser.parse(comments)
    anucio = parser.parse(disjunctions)

    for r in rogelio[1]:
        print(f"head {r[0]} \nbody {r[1]}\nvariables {r[2]}\nsorts {r[3]}", "")


if __name__ == "__main__":
    test_parse()


