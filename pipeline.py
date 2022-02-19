import parser
import models
from scaffoldings import tree as tree

program = ""
with open("./specs/theory") as le_file:
    for line in le_file:
        program = f"{program}{line}\n"

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

models = []
counter = 0

tree_constants, tree_relation = tree("node", ["head", "modifier"], 5)

for c in tree_constants:
    solver.sorts["node"].append(c)

checked = set()

for r in tree_relation:
    f, a, b = r
    solver.value_map[a, f] = b
    checked.add(a)

for e in tree_constants - checked:
    solver.value_map[e, "head"] = "null"
    solver.value_map[e, "modifier"] = "null"

solver.value_map["null", "head"] = "null"
solver.value_map["null", "modifier"] = "null"
solver.value_map["null", "type"] = "null_type"
solver.value_map["null_type", "input"] = "null_type"
solver.value_map["null_type", "output"] = "null_type"

solver.sorts["category"].append("name")
solver.sorts["category"].append("sentence")

solver.sorts["node"].append("null")

for node_constant in tree_constants:
    node_prefix = f"{node_constant}."
    node_types, node_type_tree = tree("type", ["input", "output"], 2, prefix=node_prefix)
    solver.sorts["type"] = solver.sorts["type"] + list(node_types)
    root_name = f"{node_constant}.type"
    solver.value_map[node_constant, "type"] = root_name
    for triple in node_type_tree:
        function, domain, image = triple
        solver.value_map[domain, function] = image

solver.unfold_instance()

for c in tree_constants:
    b, l, p = f"blank {c}", f"leaf {c}", f"phrase {c}"
    b, l, p = solver.literal_map[b], solver.literal_map[l], solver.literal_map[p]
    solver.solver.add_clause([b, l, p])

for m in range(1, 101):
    res = solver.solver.solve([m])
    if res:
        models.append(solver.solver.get_model())

for m in models:
    for a in m:
        if a > 0 and a in solver.reverse_literal_map:
            print(solver.reverse_literal_map[a])
    print("\n"*2)
