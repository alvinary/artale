import parser
import models
from test_parser import sorted_program as program

parts = parser.Parser().parse(program)[1]
rules = []

def clear_sorts(term):
    while " ." in term or ". " in term:
        term = term.replace(" .", ".")
        term = term.replace(". ", ".")

    while "  " in term:
        term = term.replace("  ", " ")
    
    if ":" in term:
        return " ".join(term[:term.index(":")].strip().split())
    
    else:
        return " ".join(term.split())

for p in parts:
    body, head, variables, sorts = p
    rules.append(models.Rule([models.Relation([clear_sorts(hp) for hp in h]) for h in head],
                             [models.Relation([clear_sorts(bp) for bp in b]) for b in body],
                             sorts,
                             [v for v, s in variables],
                             {},
                             []))

solver = models.HornSolver()
solver.rules = rules

for i in range(21):
    solver.sorts["pony"].append(f"pony {i}")

for i in range(6):
    solver.sorts["gift"].append(f"thing {i}")

for i in range(21):
    solver.value_map[f"pony {i}" ,"sibling"] = f"pony {(i + 1) % 21}"

solver.unfold_instance()
for c in solver.clauses:
    print(c)

for j in range(6):
    print(solver.solver.solve())
    model = solver.solver.get_model()
    for i in model:
        if i > 0:
            print(solver.reverse_literal_map[i])
    print("\n\n\n")
