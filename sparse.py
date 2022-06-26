def read_program(text):
    text = filter_comments(text)
    sorts = read_sorts(text)
    rules = read_rules(text)
    return sorts, rules

def filter_comments(text):

    separator = "---"
    separator_length = len(separator)

    separator_count = text.count(separator)

    if separator_count % 2 == 1:
        pass # Raise parity error

    while "---" in text:
        begin = text.index("---")
        end = text[begin + separator_length:].index("---")
        end = end + separator_length
        text = text[:begin] + text[end:]

    return text

def read_sorts(text):

    cardinals = []
    extensions = []
    functions = []
    
    lines = text.split("\n")
    
    for line in lines:

        tokens = line.split(" ")
        is_sort = "sort " == line[0:5]
        three_tokens = len(tokens) == 3

        if len(tokens) >= 3:

            has_number = tokens[2].isdigit()
            has_add = tokens[2] == "add"
            has_dot = "." in tokens[1]
            has_in = tokens[2] == "in" 
            many_tokens = len(tokens) > 3

        else:

            has_number = False
            has_add = False
            many_tokens = False
            has_in = False
            has_dot = False

        is_cardinal = is_sort and three_tokens and has_number
        is_distinguished = is_sort and has_add and many_tokens
        is_function = is_sort and has_dot and has_in

        if is_cardinal:

            sort_name = tokens[1]
            size = int(tokens[2])
            cardinals.append((sort_name, size))

        if is_distinguished:

            sort_name = tokens[1]
            distinguished_elements = tokens[3:]
            for elem in distinguished_elements:
                extensions.append((sort_name, elem))

        if is_function:

            dot_parts = tuple(tokens[1].split("."))

            if len(dot_parts) == 2:

                domain, f = dot_parts
                image = tokens[2]
                functions.add((domain, f, image))

            else:
                pass # Raise ill-formed sort declaration error, show line

        if is_sort and not is_distinguished and not is_cardinal and not is_function:
            pass # Raise ill-formed sort declaration error, show line

    return (cardinals, extensions, functions)

def read_rules(text):

    text = text.replace("\n", " ")
    rule_parts = text.split(".")

    rules = []

    for rule_part in rule_parts:

        if check_part(rule_part):
            rules.append(read_rule(rule_part))

        else:
            pass # Raise ill-formed rule error

    return rules

def check_part(text):
    pass

def read_rule(text):
    pass