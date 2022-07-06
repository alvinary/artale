import pytest

from sparse import *

# TODO:

# Duplicate sort declarations (e.g. sort animal 20, sort animal 30)
# Conflicting sort declarations (e.g. sort animal.species in taxa, 
# sort animal.species in onto)
# Conflicting sort assignment to constant in rule

# Assigned entity to nonexistent sort

# Rule mixes conjunction and disjunction

# Name in rule is not a variable assigned to a sort and it is not
# a distinguished constant either

# Warning: Potential typo in name (hamming distance)

# Error and warning classes with check, handle, and notify methods

# TODO:
# Syntax errors after normalization (line is neither a sort,
# rule, assertion, comment or disjunction)

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

def test_normalize():
    assert True

def test_chunk_predicate():
    test_text = "p(b, a), q(b, a), r(b) => s(a)"
    test_terms = ["p", "b", "a"]
    test_remainder = "q(b, a), r(b) => s(a)"
    test_sorts = {}
    terms, sorts, text = chunk_predicate(test_text)
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