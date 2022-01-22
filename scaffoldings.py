def tree(sort_name, relations, size, prefix=""):
    '''Optionally add a prefix to constant names.'''

    tree_constants = set()
    tree_relation = set()
    
    root = sort_name

    rows = [[root]]
    tree_constants.add(root)

    for index in range(0, size):
        rows.append([])
        for tree_elem in rows[index]:
            for rel in relations:
                child_name = f"{tree_elem}.{rel}"
                tree_constants.add(child_name)
                tree_relation.add((rel, tree_elem, child_name))
                rows[index + 1].append(child_name)

    return tree_constants, tree_relation
                

def bounded_state_world(constants, constant_sorts, n):

    new_constants, new_sorts, function_map  = set(), {}, {}

    for i in range(1, n+1):
        for c in constants:

            fresh_constant = c + f".{i}"
            new_constants.append(fresh_constant)
            new_sorts[fresh_constant] = constant_sorts[c]

            if i == 1:
                function_map[c] = fresh_constant

            else:
                previous_constant = c + ".{i - 1}"
                function_map[previous_constant] = fresh_constant
            
