import pytest

from artale.parser import *
from artale.models import HornSolver, Relation

# TODO:

# Duplicate sort declarations (e.g. sort animal 20, sort animal 30)
# Conflicting sort declarations (e.g. sort animal.species in taxa, 
# sort animal.species in onto)
# Conflicting sort assignment to constant in rule

# Unpaired comment delimiters

# Assigned entity to nonexistent sort

# Rule mixes conjunction and disjunction

# Name in rule is not a variable assigned to a sort and it is not
# a distinguished constant either

# Warning: Potential typo in name (hamming distance)

# Error and warning classes with check, handle, and notify methods

# TODO:
# Syntax errors after normalization (line is neither a sort,
# rule, assertion, comment or disjunction)

# Multiple comparisons in a single predicate (e.g. p(a, b), a = b != c => False)

complete = '''
sort number 40
sort character 40
sort spell 10
sort place 40
sort effect 40
sort place add earth
sort character add you
sort text 1
sort character.next in character
sort spell.effect in effect

one well formed program (haha : text) => False

the thing (thing : character), not in planet (thing, you.planet) => ok (you)

has issues (guy : character),
likes (gal, guy),
has 98 problems (gal : character) =>
has 99 problems (gal.next)

area (spell),
within (creature, spell.range) =>
sustain (creature.next, spell.effect)

cast spell (character, spell),
level n (spell),
n level spells (character, m) =>
n level spells (character.next, m.previous)

cast spell (character, spell),
level n (spell),
n level spells (character, zero) =>
False


the rock (actor : character), not the rock (actor) => False

the rock (actor) => bald (actor)

horse (animal : character) => precocious (animal), hoofy (animal)

'''

wrong_spacing = '''
sort number 40

sort character 40

sort spell 10

sort place 40

sort effect 40

sort place add earth

sort character add you

sort text 1

sort character.next in character

sort spell.effect in effect

one  well formed  program ( haha : text)    => 
False

the thing ( thing : character) ,  not in planet (thing ,  you.planet)  = > ok (you)

has issues (guy : character), 
likes (gal, guy),   
has 98 problems (gal : character) => 
has 99 problems (gal.next)  

area (spell),   
within (creature, spell.range) =>   
sustain (creature.next, spell.effect)  

cast spell (character, spell),  
level n (spell),  
n level spells (character, m) =>  
n level spells (character.next, m.previous)

cast spell (character, spell),
level n (spell),  
n level spells (character, zero) =>
False

the rock (actor : character),  not  the rock (actor) => False

the rock (actor) => bald (actor)

horse (animal :   character)   => precocious (animal), hoofy (animal)

'''

comments = '''
sort vieje 10

-- les viejes son viejes --

-- no es chiste --

vieje (a : vieje) => vieje posta (a)

'''

def test_normalize():

    assert True

def test_strip_comments():

    pass

def test_get_terms():

    chunk_a = "p (a, b)"
    chunk_b = "pred (b, c)"
    chunk_c = "long pred (long const, const.dot)"
    chunk_d = "a != b"
    chunk_e = "const.fun = other const.fun"
    # Names with spaces are rather questionable
    
    terms_a = "p a b".split()
    sorts_a = {}

    terms_b = "pred b c".split()
    sorts_b = {}

    terms_c = "long pred, long const, const.dot".split(", ")
    sorts_c = {}

    terms_d = "a != b".split()
    sorts_d = {}

    terms_e = "const.fun, =, other const.fun".split(", ")
    sorts_e = {}

    ta, sa = get_terms(chunk_a)
    tb, sb = get_terms(chunk_b)
    tc, sc = get_terms(chunk_c)
    td, sd = get_terms(chunk_d)
    te, _se = get_terms(chunk_e)

    assert terms_a == ta
    assert sorts_a == sa

    assert terms_b == tb
    assert sorts_b == sb

    assert terms_c == tc
    assert sorts_c == sc

    assert terms_d == td
    assert sorts_d == sd

    assert terms_e == te
    assert sorts_e == _se


def test_chunk_predicate():
    test_conjunction = normalize("p(b, a), q(b, a), r(b) => s(a)")
    
    print(test_conjunction)

    test_terms = ["p", "b", "a"]
    test_remainder = "q (b, a), r (b) => s (a)"
    test_sorts = {}
    
    terms, sorts, text = chunk_predicate(test_conjunction)
    
    assert terms == test_terms
    assert sorts == test_sorts
    assert text == test_remainder

    test_disjunction = normalize("p (b, a) v q (b, a) v r (b) v s (a)")
    
    print(test_disjunction)

    test_terms = ["p", "b", "a"]
    test_remainder = "q (b, a) v r (b) v s (a)"
    test_sorts = {}
    
    terms, sorts, text = chunk_predicate(test_disjunction)
    
    assert terms == test_terms
    assert sorts == test_sorts
    assert text == test_remainder

def test_check_part():

    wrong_part_a = "p(a, b) q(a, c) " # no comma 
    wrong_part_b = "p(a, b, c(d, e)), f(g, h)" # nested parentheses
    wrong_part_c = "" # unmatched parenthesis
    wrong_part_d = "" # mixed v and ,
    wrong_part_e = "" # terms with dot and spurious spaces

    assert True

def test_split_predicates():
    pass

def get_rule(rule_text):

    solver = HornSolver()
    
    rule_data = read_rule(normalize(rule_text))
    rulo = make_rule(rule_data, solver)

    return rulo

def test_make_rule():
    
    r1 = get_rule("p (a : sort a, b : sort b), q (b) => r (a)")
    r2 = get_rule("pepa (char : character), pig (char) => pepa pig (char)")
    r3 = get_rule("holy (t : thing) v neutral (t) v unholy (t)")
    r4 = get_rule("unholy (brad the unholy)")

    assert "sort a" in r1.sorts
    assert "sort b" in r1.sorts
    assert 'a' in r1.variables
    assert Relation(["q", "b"]) in r1.body
    assert Relation(['r', 'a']) in r1.heads

    assert 'character' in r2.sorts
    assert "char" in r2.variables
    assert Relation(['pepa pig', 'char']) in r2.heads
    assert Relation(['pig', 'char']) in r2.body
    assert Relation(['pepa', 'char']) in r2.body
    
   
