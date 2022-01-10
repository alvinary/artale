import pytest
from parser import Parser

# test case: Könisberg Ponies

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
