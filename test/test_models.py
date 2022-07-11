import pytest

from artale.parser import Parser
from artale.models import Relation, Rule, HornSolver
from artale.constants import TEMPLATE
from test_old_parser import complete as program

sorts_part, rules_part = Parser().parse(program)
heavy_sorts, heavy_rules = Parser().parse(TEMPLATE)

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

def test_string_encoding():
    relation_a = Relation(["weaves", "spider", "spiderweb"])
    relation_b = Relation(["weaves", "spider . mother", "spiderweb"])
    assert relation_a.as_string() == "weaves--spider--spiderweb"
    assert relation_b.as_string() == "weaves--spider . mother--spiderweb"

def test_unfolding():

    solver = HornSolver()

    rules = []

    for rule in rules_part:

        body, head, variables, sorts, flags = rule

        print(body)
        print(variables)
        print(sorts)
        print(flags)

        models_module_rule = Rule([Relation([term for term in atom]) for atom in head],
                                  [Relation([term for term in atom]) for atom in body],
                                  [s for v, s in variables], [v for v, s in variables],
                                  solver, {}, flags)

        rules.append(models_module_rule)

    solver.rules = rules

    solver.sorts["pony"] = [f"pony{i}" for i in range(30)]
    solver.sorts["island"] = [f"island{i}" for i in range(30)]

    solver.unfold_instance()
    solver.una_equality()

    models = []

    for m in range(1, 101):
        res = solver.solver.solve([m])
        if res:
            models.append(solver.solver.get_model())

    for m in models:
        print(solver.show_model(m))

def test_una_equality():
    rules = []
    
    solver = HornSolver()

    solver.sorts["pony"] = [f"p{i}" for i in range(4)]

    solver.una_equality()

    models = []

    res = solver.solver.solve()
    if res:
        model = solver.solver.get_model()

    readable_model = set()
    for p in model:
        readable_model.add(solver.reverse_literal_map[p])

    print(readable_model)

    cond = ("p0 = p0" in readable_model
            and "p1 = p1" in readable_model
            and "p1 != p0" in readable_model
            and "p0 != p1" in readable_model
            and "p3 != p0" in readable_model)

    assert cond

def test_show_models():
    solver = HornSolver()
    nums = [int(c) for c in "123456789"]
    letters = [c for c in "abcdefghi"]
    solver.reverse_literal_map = dict(zip(nums, letters))
    model = [-1, 3, 5, -6, -7, 2, 8]
    solver.show_model(model)
    solver.show_model(model, show_false=True)

def test_json_dump():
    pass

if __name__ == "__main__":
    test_unfolding()
    test_una_equality()

