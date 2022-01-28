import pytest
from parser import Parser
from models import Relation, Rule, HornSolver
from test_parser import sorted_program as program

sorts_part, rules_part = Parser().parse(program)

rules = []

def check_invariants(term_string):

    assert term_string.strip() == term_string
    assert "  " not in term_string
    assert ":" not in term_string

# if there are function applications (".") surrounded by spaces in a term, 
# that should not affect program behavior, as long as term parts are stripped
# before being returned / handled. Check that is effectively the case everywhere!

def normalize(term_string):

    while "  " in term_string:
        term_string = term_string.replace("  ", " ")

    return clear_sorts(term_string).strip()

def clear_sorts(term_string):

    if ":" in term_string: 
        return term_string[:colon_index].strip()

    else:
        return term_string


for rule in rules_part:

    body, head, variables, sorts = rule

    models_module_rule = Rule([Relation([term for term in atom]) for atom in head],
                              [Relation([term for term in atom]) for atom in body],
                              [v for v, s in variables], {}, [], {})

    rules.append(models_module_rule)


def test_string_encoding():
    relation_a = Relation(["weaves", "spider", "spiderweb"])
    relation_b = Relation(["weaves", "spider . mother", "spiderweb"])
    assert relation_a.get_string_encoding() == "weaves--spider--spiderweb"
    assert relation_b.get_string_encoding() == "weaves--spider . mother--spiderweb"

def test_bind_variables():
    pass
    
