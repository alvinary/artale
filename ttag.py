from parser import Parser
from models import Relation, Rule, Clause, HornSolver, TERM_SEPARATOR
from scaffoldings import tree, binary_tree

SIZE_BOUND = 13
TYPE_DEPTH = 2

# Initialize solver object

solver = HornSolver()

# Read program specification from file and parse it

theory_program = ""

with open("./specs/trees") as theory_file:
    for line in theory_file:
        theory_program = theory_program + line

sort_declarations, rule_declarations = Parser().parse(theory_program)

for rule in rule_declarations:
    body, head, variables, sorts, flags = rule
    solver.rules.append(Rule([Relation([term for term in atom]) for atom in head],
                             [Relation([term for term in atom]) for atom in body],
                             [s for _, s in variables], [v for v, _ in variables],
                             solver, {}, flags))

# Ground rules / clauses and apply tree scaffolding

print("Assembling tree scaffolding...")

tree_constants, tree_facts = tree("node", SIZE_BOUND)

paired_constants = []

for i in range(SIZE_BOUND):
    for j in range(i+1, SIZE_BOUND):
        paired_constants.append((f"c{i}", f"c{j}"))

right_facts = [f"right {a} {b}" for a, b in paired_constants]

solver.sorts["node"] = list(tree_constants)


for f in tree_facts:

    clause_literal = " ".join(f)

    if "not " not in clause_literal:
        solver.add_assertion(clause_literal)

    if "not " == clause_literal[:4]:
        #TODO: This is bodge, please fix it
        positive_literal = clause_literal[4:]
        tree_clause = Clause("", [positive_literal])
        solver.update_maps([tree_clause])
        solver.solver.add_clause(solver.dimacs(tree_clause))


for t in tree_constants:

    node_drs = f"{t}.drs"
    node_type = f"{t}.type"
    
    solver.value_map[t, "drs"] = node_drs
    solver.value_map[t, "type"] = node_type

    solver.sorts["type"].append(node_type)
    solver.sorts["drs"].append(node_drs)

    for semitem in ["self", "1", "2", "3", "4"]:
        solver.value_map[node_drs, semitem] = f"{node_drs}.{semitem}"
        solver.sorts["semitem"].append(f"{node_drs}.{semitem}")

    for i in range(1, 3):
        solver.value_map[f"{t}.{str(i)}", "next"] = f"{t}.{str(i+1)}"
        solver.value_map[f"{t}.{str(i+1)}", "previous"] = f"{t}.{str(i)}"
    
    solver.value_map[f"{t}.4", "next"] = "blanksemitem"
    solver.value_map[f"{t}.1", "previous"] = "blanksemitem"

    solver.value_map[node_drs, "self"] = f"{node_drs}.self"

    type_constants, type_tree = binary_tree("", ["input", "output"], TYPE_DEPTH, prefix=node_type)

    solver.sorts["type"] = sorted(list(set(solver.sorts["type"]) | set(type_constants)))

    print("Types: ")
    for c in solver.sorts["type"]:
        print(c)
    
    chomeur = set(type_constants)

    for f, k, v in type_tree:
        solver.value_map[k, f] = v
        chomeur.discard(k)

    for k in chomeur:
        for f in ["input", "output"]:
            solver.value_map[k, f] = "blanktype"

print("Done")

print("Unfolding...")

solver.unfold_instance()
solver.una_equality()

print("Done")

print("Looking for models...")

# If the program is run as main, print a few models, provided
# some are found when fixing any of the literals from 1 to 300
# as true. This is bodge as well, so please fix it too - TODO

if __name__ == "__main__":

    for i in range(1, 300):
        res = solver.solver.solve([i])
        if res:
            print(f"Instance is satisfiable when fixing atom {i} to true")
            m = solver.solver.get_model()
            tree_facts = set()
            for a in m:
                if abs(a) in solver.reverse_literal_map:
                    readable_atom = solver.reverse_literal_map[abs(a)]
                    if "=" not in readable_atom and a > 0:
                        tree_facts.add(readable_atom)
                    if "=" not in readable_atom and a < 0:
                        tree_facts.add("- " + readable_atom)
            print("\n".join(sorted(list(tree_facts))), "\n")
            print(len(m), "", len([a for a in m if a > 0]))
        else:
            print(f"\nInstance is not satisfiable when fixing atom {i} ({solver.reverse_literal_map[i]}) to true!!\n")
