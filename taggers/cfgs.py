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
VOID = "void"

# Define artale.n_models(n, rels=[], program)

# Embed a string

def instancify(string, name, solver):
    chars = set()
    next_to_last = len(string) - 1
    
    new_constants = []
    
    if not name:
        name = string
    for i, c in enumerate(string):
        new_string = f"{name}:{i+1}"
        char_assertion = f"is {new_string} {c}"
        solver.add_assertion(char_assertion)
        chars.add(c)
        solver.add_element(STRINGS, new_string)
        new_constants.append(new_string)
        if i < next_to_last:
            next_string = f"{name}:{i+2}"
            solver.value_map[NEXT, new_string] = next_string
        elif i == next_to_last:
            solver.value_map[NEXT, new_string] = VOID
    
    for c in chars:
        if c not in solver.sorts[CHARS]:
            solver.add_element(CHARS, c)
    
    return new_constants
    
def make_instance(pos, neg):

    solver = HornSolver()
    solver.verbose = True
    read_into(cfg, solver)
    solver.fill_sort("T", 8)
    solver.add_element(PRETERMINALS, "start")
    
    is_local = lambda x : STRINGS in x.sorts
    is_global = lambda x : STRINGS not in x.sorts
    
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

    for i, p in enumerate(pos):
        positive_example = f"p{i}"
        local_sorts[positive_example] = instancify(p, positive_example, solver)
        solver.add_element(POSITIVE, positive_example)
        
    for i, n in enumerate(neg):
        negative_example = f"n{i}"
        local_sorts[negative_example] = instancify(n, negative_example, solver)
        solver.add_element(NEGATIVE, negative_example)
        
    for k in solver.value_map.keys():
        print(f"{str(k)} : {solver.value_map[k]}")
        
    print("String data added, unfolding instance...")

    for global_rule in global_rules:
        solver.unfold_rule(global_rule)
        
    for local_rule in local_rules:
        for string in local_sorts.keys():
            local_restrictions = {}
            local_restrictions[STRINGS] = local_sorts[string]
            solver.unfold_rule(local_rule, local_restrictions)
            
    solver.unfold_una()
    
    print("Unfolded instance, showing clauses...")
    
    sat, model = solver.get_model()
    
    if sat:
        print("Instance found: ")
        model = solver.show_model(model)
        print(model)
    else:
        print("Hmhhh, something went wrong")
        
paren_pos = ["(a+b)+b", "(a+(b+c))", "((a+a)+b)+c", "(a+((c+b)+(a +((c+a)+b)))", "a+((b+c)+b)"]
paren_neg = ["(a+b+c)", "(a)+)b", "((a+)c(", "(a)+(b+)+(c+c)"]
make_instance(["aa", "aaaa"], ["a", "aaa"])
