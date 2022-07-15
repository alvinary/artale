from artale.models import HornSolver
from artale.parser import read_into
from artale.specs import cfg

STRING_LENGTH = 30
STRING_SORT = "S"
NEXT = "next"

# Define artale.n_models(n, rels=[], program)

solver = HornSolver()
read_into(cfg, solver)

# Embed a string

for i in range(1, STRING_LENGTH + 1):
    new_string = f"s{i}"
    next_string = f"s{i+1}"
    solver.add_element(STRING_SORT, new_string)
    solver.value_map[NEXT, new_string] = next_string
    
solver.unfold_instance()
solver.unfold_una()

solver.add_assertion("parses start s1")
    
# Write a string

def write_string(solver, s):
    for (i, c) in enumerate(s):
        char_assertion = f"is s{i+1} {c}"
        solver.add_assertion(char_assertion)
    last_char = f"s{len(s)+1}"
    string_end = f"empty {last_char}"
    solver.add_assertion(string_end)
