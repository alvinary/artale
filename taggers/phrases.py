from artale.constants import *
from artale.parser import read_into, normalize
from artale.models import Relation, Rule, Clause, HornSolver, TERM_SEPARATOR
from artale.specs import trees as trees_spec

node_sort = "node"
tree_size = 14

solver = HornSolver()
solver.fill_sort(node_sort, tree_size)
read_into(trees_spec, solver)
solver.unfold_instance()
solver.unfold_una()

sat, model = solver.get_model()
readable_model = solver.show_model(model)
print(readable_model)

nodes = solver.sorts["node"]

root_is_phrase = "phrase node1"
next_is_next = [f"next node{i + 1} node{i + 2}" for i in range(len(nodes))]

not_befores = [f"not before {n1} {n2}" for n1 in nodes for n2 in nodes if n1 >= n2]
befores = [f"before {n1} {n2}" for n1 in nodes for n2 in nodes if n1 < n2]
rights = [f"right {n1} {n2}" for n1 in nodes for n2 in nodes if n1 < n2]
lefts = [f"left {n1} {n2}" for n1 in nodes for n2 in nodes if n1 < n2]

additional_facts = [root_is_phrase] + not_befores + befores

for f in additional_facts:
    solver.add_assertion(f)


if __name__ == "__main__":    
    for c, d in solver.show_clauses():
        print(c, d)
        print("")

    for f in rights + lefts:
        print(f"Try with '{f}':")
        sat, model = solver.model_with([f])
        if sat:
            print("Instance is satisfiable! A model is: \n")
            print(solver.show_model(model))
            
        else:
            print("Instance is not satisfiable")
        print("\n\n")
