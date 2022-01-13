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


