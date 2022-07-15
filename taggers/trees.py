from artale.constants import *

from artale.parser import read_into, normalize
from artale.models import Relation, Rule, Clause, HornSolver, TERM_SEPARATOR
from artale.scaffoldings import tree, binary_tree
from artale.specs import trees as trees_spec
from artale.specs import types as types_spec

SIZE_BOUND = 8
TYPE_DEPTH = 3

NODE_PREFIX = "node"

# Initialize solver object

solver = HornSolver()

# Read program specification from file and parse it

trees_spec = normalize(trees_spec + types_spec)
print(trees_spec)
read_into(trees_spec, solver)

'''

trees_lines = trees_spec.split("\n\n")
tree_programs = []

for i in range(3, len(trees_lines)):
    tree_programs.append("\n\n".join(trees_lines[:i]))

solvers = []

for i in range(3, len(trees_lines)):
    solvers.append(HornSolver())

ccc = 0
for i, ts in enumerate(tree_programs):
    read_into(ts, solvers[i])
    solvers[i].fill_sort("node", SIZE_BOUND)
    solvers[i].unfold_instance()
    solvers[i].una_equality()
    res = solvers[i].solver.solve()
    if res:
        print("!")
        ccc += 1

print("ccc", ccc)

'''
   
# Ground rules / clauses and apply tree scaffolding

print("\nAssembling tree scaffolding...")


tree_constants, tree_facts = tree(NODE_PREFIX, SIZE_BOUND)

solver.sorts["node"] = list(tree_constants)
solver.sorts["litem"] = LEXICON

paired_constants = []

for i in range(SIZE_BOUND):
    for j in range(i + 1, SIZE_BOUND):
        paired_constants.append((f"node{i + 1}", f"node{j + 1}"))

right_facts = [f"right {a} {b}" for a, b in paired_constants]

for r in right_facts:
    solver.add_assertion(r)

solver.add_assertion("root node1")

for f in tree_facts:

    # Turn the relation triple into a clause
    clause_literal = " ".join(f)

    # Check if the literal is negated
    is_assertion = "not " != clause_literal[:4]
    is_negation = not is_assertion

    # If the literal is positive, add it as an assertion /
    # horn clause with a single positive atom.
    
    # If it's not, add it as a negative assertion /
    # headless clause with just one body atom.
    
    print("clause literal: ", clause_literal)

    if is_assertion:

        solver.add_assertion(clause_literal)

    if is_negation:
        
        # Get the non-negated version of the literal
        positive_literal = clause_literal[4:]

        # Turn it into a clause
        tree_clause = Clause("", [positive_literal])

        # Update solver literal maps
        solver.update_maps([tree_clause])

        # Add dimacs form of that clause to solver
        solver.solver.add_clause(solver.dimacs(tree_clause))

# Make DRS and type constant for each node,
# adding their arguments (for DRS) and a small
# binary tree (for types)

for tree_node in tree_constants:

    prefix = tree_node + "."

    # Make DRS and type constants

    drs_node = prefix + "drs"
    type_node = prefix + "type"

    # Make sure they are assigned to their node in the value map
    
    solver.value_map["drs", tree_node] = drs_node
    solver.value_map["type", tree_node] = type_node

    # Add them to their respective sort in the solver's record

    solver.sorts["type"].append(type_node)
    solver.sorts["drs"].append(drs_node)

    # Add DRS item arguments

    for argument in ["self", "1", "2", "3", "4"]:

        # Name the argument
        new_argument = f"{drs_node}.{argument}"

        # Assign it to its DRS
        solver.value_map[argument, drs_node] = new_argument

        # Add it to its corresponding sort
        solver.sorts["semitem"].append(new_argument)

    # Make sure every DRS argument has a next and previous argument

    for i in range(1, 3):
        pred = prefix + str(i)
        succ = prefix + str(i + 1)
        solver.value_map["next", pred] = succ
        solver.value_map["previous", succ] = pred

    # Handle corners (the first and last arguments)
    
    first = prefix + "1"
    last = prefix + "4"
    solver.value_map["previous", first] = "blanksemitem"
    solver.value_map["next", last] = "blanksemitem"

    # Assign drs_node.self as self to drs_node
    solver.value_map["self", drs_node] = f"{drs_node}.self"

    # Assemble a small binary tree
    type_constants, type_tree = binary_tree("", ["input", "output"], TYPE_DEPTH, prefix=type_node)

    # Add new type constants to their respective sort
    for new_type_node in set(type_constants):
        solver.sorts["type"].append(new_type_node)

    # Make sure all nodes without input and output nodes
    # have a dummy input and output, so that unfolding
    # does not break (unfolding cannot handle partial
    # functions, so in order to make functions total,
    # all elements in the domain that do not yet have
    # an image are assigned the dummy element as image)
    
    # A constant is chomeur if it does not have an input
    # or output. So we start with all constants and remove
    # the ones that do have an input or output (i.e. the
    # ones that are in some triple in the relation that
    # specifies the input tree)

    chomeur = set(type_constants)

    for f, k, v in type_tree:
        solver.value_map[f, k] = v
        chomeur.discard(k)

    # Assign dummy image to chomeur type nodes
    for k in sorted(chomeur):
        for f in ["input", "output"]:
            solver.value_map[f, k] = "blanktype"
            
    solver.value_map["input", "blanktype"] = "blanktype"
    solver.value_map["output", "blanktype"] = "blanktype"
            
            
print("Done\n")

solver.fill_sort(NODE_PREFIX, SIZE_BOUND)

print("Unfolding instance...")

solver.unfold_instance()

print("Done\n")

print("Unfolding equality...")

solver.unfold_una()

print("Done\n")


for c in solver.cnf_clauses:
    print(c)
    neg = [solver.reverse_literal_map[abs(a)] for a in c if a < 0]
    pos = [solver.reverse_literal_map[abs(a)] for a in c if a > 0]
    print(", ".join(neg) + " => " + ", ".join(pos))


print("Looking for models...\n")

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
