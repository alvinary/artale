from numpy import split


IMPLICATION = "=>"
DISJUNCTION = " v "
ASSERTION = "."
CONTRADICTION = "False"
CONJUNCTION = " , "

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
    # Exactly one =>
    # One predicate
    # n predicates, n > 1, and n - 1 vees
    # => and False
    # head is well formed
    # body is well formed
    pass

def read_rule(text):
    is_disjunction = " v " in text
    is_contradiction = "=> False" in text
    is_implication = "=>" in text and not is_contradiction
    is_assertion = "=>" not in text and not is_disjunction

    if is_implication:
        body_part, head_part = tuple(text.split("=>"))
        body = split_predicates(body_part)
        head = split_predicates(head_part)
        return (IMPLICATION, body, head)

    if is_contradiction:
        body_part = text[:-8]
        body = split_predicates(body_part)
        return (CONTRADICTION, body)

    if is_disjunction:
        head = split_predicates(text)
        return (DISJUNCTION, head)

    # Assertions with variables are allowed

    if is_assertion:
        head = split_predicates(text)
        return (ASSERTION, head)


def split_predicates(text):

    predicates = []

    while text:
        predicate, text = chunk_predicate(text)
        predicates.append(predicate)

    return predicates
        
def chunk_predicate(text):

    terms = []

    lparen_index = text.index("(")
    rparen_index = text.index(")")

    predicate_term = text[:lparen_index]
    term_segment = text[lparen_index + 1, rparen_index]
    terms = [predicate_term]
    terms = terms + term_segment.split(", ") # Make sure spacing is right

    text = text[rparen_index + 1:]

    if DISJUNCTION in text:
        skip_index = text.index(DISJUNCTION)
        skip_index += len(DISJUNCTION)

    if CONJUNCTION in text:
        skip_index = text.index(CONJUNCTION)
        skip_index += len(CONJUNCTION)

    text = text[skip_index:]

    return terms, text