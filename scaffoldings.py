def tree(sort_name, relations, size, prefix=""):
    facts = set()
    constants = [f"c{i}" for i in range(size)]
    for i in range(size):
        if i <= size - 2:
            facts.add(("next", f"c{i}", f"c{i+1}"))
        for j in range(i, size):
            facts.add(("before", f"c{i}", f"c{j}"))
    return constants, facts
    

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

def leveled_relation(sort_name, base_sizes, window_size):

    new_constants = set()
    new_relations = set()

    levels = []

    current_level = [f"{sort_name}{i}" for i in range(base_size)]

    new_constants |= set(current_level)

    levels.append(current_level)

    while len(levels[-1]) > 1:
        current_level = []
        print(len(levels))
        print(f"Previous level length: {len(levels[-1])}")
        for i in range(len(levels[-1]) - window_size + 1):
            new_component = f"{sort_name}l{len(levels)}:{i}:{i+window_size}"
            current_level.append(new_component)
            new_constants.add(new_component)
            window_start, window_finish = i, i + window_size
            component_parts = levels[-1][window_start : window_finish]
            for part in component_parts:
                new_relations.add(("part", new_component, part))
        levels.append(current_level)

    return new_constants, new_relations

