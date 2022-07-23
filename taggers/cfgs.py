from itertools import product
from collections import defaultdict

# I should place these imports in 'common'

from artale.models import HornSolver
from artale.parser import read_into
from artale.specs import cfg

STRINGS = "S"
RULES = "rule"
PRETERMINALS = "T"
CHARS = "C"
NEXT = "next"
POSITIVE = "pos"
NEGATIVE = "neg"
EMPTY = "empty"
NODES = "node"

NUMBER_OF_PRETERMINALS = 6

# Define artale.n_models(n, rels=[], program)

# Embed a tree

def make_tree(size, name, solver):

    new_constants = {}
    new_constants[NODES] = []

    for i in range(size):
        new_node = f"node:{name}:{i+1}"
        new_constants[NODES].append(new_node)
        
    nodes = new_constants[NODES]
    node_indices = [i for i, n in enumerate(nodes)]
        
    make_next = lambda x : f"next node:{name}:{x} node:{name}:{x+1}"
    make_not_next = lambda i, j : f"not next node:{name}:{i} node:{name}:{j}"

    index_pairs = product(node_indices, repeat=2)
    node_pairs = lambda : product(nodes, repeat=2)
    not_nexts = [make_not_next(i, j) for i, j in index_pairs if i + 1 != j]
    nexts = [make_next(i) for i in node_indices]
    nexts = nexts + not_nexts

    not_befores = [f"not before {n1} {n2}" for n1, n2 in node_pairs() if n1 >= n2]
    befores = [f"before {n1} {n2}" for n1, n2 in node_pairs() if n1 < n2]

    rights = [f"right {n1} {n2}" for n1, n2 in node_pairs() if n1 < n2]
    lefts = [f"left {n1} {n2}" for n1, n2 in node_pairs() if n1 < n2]
    
    root_is_phrase = f"has root {name} node:{name}:1"

    additional_facts = [root_is_phrase] + not_befores + befores + nexts
    
    for fact in additional_facts:
        solver.add_assertion(fact)
        
    return new_constants
    
# Embed a string

def instancify(string, name, solver):
    chars = set()
    next_to_last = len(string) - 1
    
    new_constants = {}
    new_constants[NODES] = []
    new_constants[STRINGS] = []
    
    if not name:
        name = string
    for i, c in enumerate(string):
    
        new_string = f"{name}:{i+1}"
    
        before = lambda k : f"before {new_string} {name}:{k + 1}"
        not_before = lambda k : f"not before {name}:{k + 1} {new_string}"
        before_empty = f"before {new_string} {EMPTY}"
        empty_not_before = f"not before {EMPTY} {new_string}"
    
        char_assertion = f"is {new_string} {c}"
        before_assertions = [before(k) for k in range(i, len(string))]
        after_assertions = [not_before(k) for k in range(i)]
        before_assertions.append(before_empty)
        after_assertions.append(empty_not_before)
        
        solver.add_assertion(char_assertion)
        for b in before_assertions:
            solver.add_assertion(b)
        
        chars.add(c)
        solver.add_element(STRINGS, new_string)
        new_constants[STRINGS].append(new_string)
        if i < next_to_last:
            next_string = f"{name}:{i+2}"
            solver.value_map[NEXT, new_string] = next_string
        elif i == next_to_last:
            solver.value_map[NEXT, new_string] = EMPTY
    
    for c in chars:
        if c not in solver.sorts[CHARS]:
            solver.add_element(CHARS, c)
        
    return new_constants
    
def make_instance(pos, neg):

    solver = HornSolver()
    solver.verbose = True
    read_into(cfg, solver)
    solver.fill_sort("T", NUMBER_OF_PRETERMINALS)
    solver.add_element(PRETERMINALS, "start")
    
    is_local = lambda x : STRINGS in x.sorts or NODES in x.sorts
    is_global = lambda x : STRINGS not in x.sorts and NODES not in x.sorts
    
    local_rules = [r for r in solver.rules if is_local(r)]
    global_rules = [r for r in solver.rules if is_global(r)]
    
    print("LOCAL")
    for l in local_rules:
        print(l.as_string())
        
    print("GLOBAL")
    for r in global_rules:
        print(r.as_string())
    
    production_rules = []
    string_rules = []
    
    print("Adding string representation to problem instance...")
    
    local_sorts = {}

    for i, string in enumerate(pos):
        positive_example = f"p{i}"
        new_constants = instancify(string, positive_example, solver)
        local_sorts[positive_example] = new_constants
        first_char = f"{positive_example}:1"
        solver.add_element(POSITIVE, first_char)
        
    for i, string in enumerate(neg):
        negative_example = f"n{i}"
        tree_size = len(string) - 1
        new_constants = instancify(string, negative_example, solver)
        local_sorts[negative_example] = new_constants
        first_char = f"{negative_example}:1"
        solver.add_element(NEGATIVE, first_char)
        
    for i in solver.sorts[POSITIVE]:
        print("POSITIVEEE", i)
        
    for i in solver.sorts[NEGATIVE]:
        print("NEGATIVEEE", i)
        
    for k in solver.value_map.keys():
        print(f"{str(k)} : {solver.value_map[k]}")
        
    print("String data added, unfolding instance...")

    for global_rule in global_rules:
        solver.unfold_rule(global_rule)
        
    for local_rule in local_rules:
        for string in local_sorts.keys():
            local_restrictions = local_sorts[string]
            solver.unfold_rule(local_rule, local_restrictions)
            
    solver.unfold_una()
    
    print("Unfolded instance, solving...")
    
    sat, model = solver.get_model()
    
    if sat:
        print("Instance found: ")
        model = solver.show_model(model)
        print(model)
        return model
    else:
        print("Hmhhh, something went wrong. This instance is not satisfiable")
        print("Assertions in unsatisfiable core: ")
        solver.solver.solve()
        core = solver.solver.get_core()
        print(core)
        for a in core:
            if a < 0:
                print("not" "solver.reverse_literal_map[abs(a)]")
            if a > 0:
                print("not" "solver.reverse_literal_map[a]")
        return ""
        
def prettify(rule):
    return f"{rule[0]} -> {' '.join(rule[1:])}"
        
def show_grammar(model_text):
    facts = model_text.split(", ")
    productions = []
    for f in facts:
        if "productions" in f or "substitutions" in f:
            productions.append(f.split()[1:])
    productions = [prettify(p) for p in productions]
    return productions
    
def fill(s, t):
    return s + ' ' * (len(t) - len(s))
    
def max_len(s, t):
    if len(s) < len(t):
        return t
    else:
        return s
    
def show_parses(model_text, name, string):
    
    facts = model_text.split(", ")
    
    parse_prefix = "segment"
    prefix_length = len(parse_prefix.split())
    
    parses_on = [f for f in facts if parse_prefix in f and name in f]
    
    parses = [f.split()[prefix_length:] for f in parses_on]
    
    strings = set([f[1] for f in parses])
    strings |= set([f[2] for f in parses])
    strings = sorted(list(strings))
    
    who_parses = {}
    
    get_int = lambda s: int(''.join([t for t in s if t in '1234567890'][1:]))
    
    for A, s1, s2 in parses:
        i = get_int(s1) - 1
        j = get_int(s2) - 1
        # assert ((i, j) not in who_parses.keys())
        who_parses[i, j] = A
    
    segments = defaultdict(lambda: list())
    for i in range(len(strings)):
        for j in range(i+1, len(strings)):
            segments[j - i].append((i, j))
            
    parse_table = []
    
    segment_sizes = sorted(segments.keys())
    segment_sizes = [s for s in segment_sizes if s > 0]
    
    max_terminal = ''
            
    for size in segment_sizes:
        
        row = [' ' for s in string]
        used_segments = [(i, j) for (i, j) in segments[size] if (i, j) in who_parses]
        
        for i, j in used_segments:
            
            terminal = who_parses[i, j]
            
            if terminal == 'start':
                terminal = 'S'
            
            max_terminal = max_len(max_terminal, terminal)
            
            row[i] = terminal
                
        parse_table = [row] + parse_table
        
    parse_table = [[fill(s, max_terminal) for s in row] for row in parse_table]
    parse_table = [''.join(row) for row in parse_table]
    parse = "\n".join(parse_table)
    parse = parse + "\n" + ''.join([fill(s, max_terminal) for s in string])

    return parse
        

["((a+a)+b)+c"]

["(a+((c+b)+(a +((c+a)+b)))", "(a+(b+c))", "a+((b+c)+b)", "(a+(b+c))",]

["((a+)c(", "(a)+(b+)+(c+c)", "(a)+)b"]

paren_pos = ["(a+a)+a", "(a+(a+a))", "a+((a+a)+a)"]
paren_neg = ["(a+a+a)", "(a)+)a", "(a)+(a+)+(a+a)"]
result = make_instance(paren_pos, paren_neg)
print("\n".join(show_grammar(result)))
print(show_parses(result, "p1", "(a+(b+c))"))
