from models import Relation, Rule
from models import IS_DISJUNCTION as DISJUNCTION_FLAG

IMPLICATION = " => "
DISJUNCTION = " v "
ASSERTION = "."
CONTRADICTION = "False"
CONJUNCTION = ", "
SORT_ASSIGNMENT = " : "

EQUALS = "="
NEQUALS = "!="

PUNCTUATION = ") .".split()

HORN_SEPARATOR = "), "

LPAREN = " ("
RPAREN = ")"

def normalize(text):
    
    '''
    Rewrite a program so it can be suitably processed by
    read_program()
    '''

    lines = text.split("\n\n")
    lines = [l.strip() for l in lines]
    lines = [l.replace("\n", " ") for l in lines]

    text = "\n\n".join(lines)

    for punct in PUNCTUATION:
        space_before = " " + punct
        space_after = punct + " "
        text = text.replace(space_before, punct)
        text = text.replace(space_after, punct)

    text = text.replace("=>", IMPLICATION)
    text = text.replace(",", CONJUNCTION)
    text = text.replace("(", LPAREN)
    text = text.replace(":", SORT_ASSIGNMENT)

    while "  " in text:
        text = text.replace("  ", " ")

    text = text.replace(" ,", ",")
    text = text.replace(")v", ") v")

    return text

def read_program(text):

    '''
    Input a program and return a list of sort specifications
    and a list of rule specifications.
    '''

    text = normalize(text)
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
    
    lines = text.split("\n\n")
    
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
    # n predicates, n > 1, and n - 1 vees
    # n predicates, n > 1, and n - 1 conjunctions
    # => and False
    # head is well formed
    # body is well formed
    # Exactly one = or !=
    pass

def read_rule(text):

    is_disjunction = " v " in text
    is_contradiction = "=> False" in text
    is_implication = "=>" in text and not is_contradiction
    is_assertion = "=>" not in text and not is_disjunction

    if is_implication:

        body_part, head_part = tuple(text.split("=>"))
        body, body_sorts = split_predicates(body_part)
        head, head_sorts = split_predicates(head_part)
        sorts = body_sorts | head_sorts

        return (IMPLICATION, sorts, body, head)

    if is_contradiction:

        body_part = text[:-8]
        body, sorts = split_predicates(body_part)

        return (CONTRADICTION, sorts, body)

    if is_disjunction:

        head, sorts = split_predicates(text)

        return (DISJUNCTION, sorts, head)

    # Assertions with variables are allowed

    if is_assertion:

        head, sorts = split_predicates(text)

        return (ASSERTION, sorts, head)


def split_predicates(text):

    predicates = []
    sorts = {}

    while text:
        predicate, chunk_sorts, text = chunk_predicate(text)
        predicates.append(predicate)
        sorts |= chunk_sorts

    return predicates, sorts


def chunk_predicate(text):

    _chunk, text = chunk(text)
    terms, sorts = get_terms(_chunk)

    return terms, sorts, text


def chunk(text):
    
    is_disjunction = DISJUNCTION in text
    is_horn = HORN_SEPARATOR in text
    is_last = not is_disjunction and not is_horn

    if is_horn:
        chunk_end = text.index(HORN_SEPARATOR) + 1 # Add one to make up for the ')' in '), '
        connective_skip = chunk_end + len(HORN_SEPARATOR) - 1

    if is_disjunction:
        chunk_end = text.index(DISJUNCTION)
        connective_skip = chunk_end + len(DISJUNCTION)

    if is_last:
        chunk_end = len(text)
        connective_skip = 0

    chunk = text[:chunk_end]
    text = text[connective_skip:]

    return chunk, text

def get_terms(text):

    sorts = {}

    is_comparison = EQUALS in text or NEQUALS in text
    is_predicate = LPAREN in text and RPAREN in text

    # Make sure you never have an overlap
    # between these conditions

    if is_comparison and NEQUALS in text:
        left_term, right_term = [t.strip() for t in text.split(NEQUALS)]
        terms = [left_term, NEQUALS, right_term]
        sorts |= get_sorts(terms)

    elif is_comparison:
        left_term, right_term = [t.strip() for t in text.split(EQUALS)]
        terms = [left_term, EQUALS, right_term]
        sorts |= get_sorts(terms)

    elif is_predicate: 

        terms = []

        lparen_index = text.index("(")
        rparen_index = text.index(")")

        predicate_term = text[:lparen_index]
        term_segment = text[lparen_index + 1 : rparen_index]
        terms = [predicate_term]
        terms = terms + term_segment.split(CONJUNCTION)
        terms = [t.strip() for t in terms]
        sorts |= get_sorts(terms)

    else:
        print(text)
        assert False

    return terms, sorts

def get_sorts(terms):

    sorts = []
    sorted_terms = [t for t in terms if SORT_ASSIGNMENT in t]

    for t in sorted_terms:
        parts = [r.strip() for r in t.split(SORT_ASSIGNMENT)]
        sorts.append(tuple(parts))

    return dict(sorts)

def make_rule(rule_tuple, solver):

    rule_type = rule_tuple[0]

    is_implication = rule_type == IMPLICATION
    is_assertion = rule_type == ASSERTION
    is_disjunction  = rule_type = DISJUNCTION
    is_contradiction = rule_type == CONTRADICTION

    sorts = {}
    body = []
    head = []
    flags = {}

    if is_implication:

        _, sorts, body, head = rule_tuple

    if is_assertion:

        _, sorts, head = rule_tuple

    if is_disjunction:

        _, sorts, head = rule_tuple

        flags = {DISJUNCTION_FLAG}

    if is_contradiction:

        sorts, body = rule_tuple

    body_relations = [Relation(terms) for terms in body]
    head_relations = [Relation(terms) for terms in head]

    sorts_items = list(sorts.items())

    rule_sorts = [v for k, v in sorts_items]
    rule_variables = [k for k, v in sorts_items]
        # Is this the right order?
        # p(k : v)?

    bindings = {}

    return Rule(head_relations,
                body_relations,
                rule_sorts,
                rule_variables,
                solver,
                bindings,
                flags)