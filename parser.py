from ctypes.wintypes import DOUBLE
import re

from artale.models import Relation, Rule
from artale.models import IS_DISJUNCTION as DISJUNCTION_FLAG

IMPLICATION = " => "
DISJUNCTION = " v "
ASSERTION = "."
CONTRADICTION = "False"
CONJUNCTION = ", "
SORT_ASSIGNMENT = " : "

VARIABLES = "var"

EQUALS = "="
NEQUALS = "!="

PUNCTUATION = ") .".split()

HORN_SEPARATOR = "), "

LPAREN = " ("
RPAREN = ")"

DOUBLE_SPACES = "  "
SINGLE_SPACE = " "

TRIPLE_LINE_BREAKS = "\n\n\n"
DOUBLE_LINE_BREAKS = "\n\n"

def normalize(text):
    
    '''
    Rewrite a program so it can be suitably processed by
    read_program()
    '''

    text = filter_comments(text)

    lines = text.split("\n\n")
    lines = [l.strip() for l in lines]
    lines = [l.replace("\n", " ") for l in lines if len(l) > 0]

    while TRIPLE_LINE_BREAKS in text:
        text = text.replace(TRIPLE_LINE_BREAKS, DOUBLE_LINE_BREAKS)

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

    while DOUBLE_SPACES in text:
        text = text.replace(DOUBLE_SPACES, SINGLE_SPACE)

    text = text.replace(" ,", ",")
    text = text.replace(")v", ") v")

    return text

def read_program(text):

    '''
    Input a program and return a list of sort specifications
    and a list of rule specifications.
    '''

    text = normalize(text)
    
    sorts = read_sorts(text)
    
    variables, text = read_variables(text)
    
    variables = dict(variables)
    
    rules = read_rules(text, variables)

    return sorts, rules, variables

def filter_comments(text):
    return re.sub("--.*--", "", text)
    
def read_variables(text):
    
    variables = []
    
    has_var = lambda tokens : tokens[0] == "var"
    has_colon = lambda tokens : ":" in tokens
    is_long = lambda tokens: len(tokens) >= 4
    
    has_vars = lambda x : has_var(x) and has_colon(x) and is_long(x)
    
    lines = [l for l in text.split(DOUBLE_LINE_BREAKS) if len(l) > 0]
    sort_lines = {l for l in lines if has_vars(l.split())}
    program_lines = [l for l in lines if l not in sort_lines]
    
    for line in sort_lines:
        sort = line.split(":")[1].strip()
        _variables = line.split(":")[0][4:].strip().split(", ")
        variables = variables + [(var, sort) for var in _variables]
        
    text = DOUBLE_LINE_BREAKS.join(program_lines)
        
    return variables, text

def read_sorts(text):

    cardinals = []
    extensions = []
    functions = []
    
    lines = text.split("\n\n")
    
    for line in lines:

        new_cardinals, new_extensions, new_functions = read_sort(line)

        cardinals = cardinals + new_cardinals
        extensions = extensions + new_extensions
        functions = functions + new_functions

    return (cardinals, extensions, functions)

def read_sort(line):

    cardinals = []
    extensions = []
    functions = []

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
        cardinals = cardinals + read_filling(tokens)

    if is_distinguished:
        extensions = extensions + read_distinguished_element(tokens)

    if is_function:
        functions = functions + read_functions(tokens)

    if is_sort and not is_distinguished and not is_cardinal and not is_function:
        pass # Raise ill-formed sort declaration error, show line

    return cardinals, extensions, functions

def read_filling(tokens):

    sort_name = tokens[1]
    size = int(tokens[2])
    filling = (sort_name, size)

    return [filling]

def read_distinguished_element(tokens):

    extensions = []

    sort_name = tokens[1]
    distinguished_elements = tokens[3:]
    for elem in distinguished_elements:
        extensions.append((sort_name, elem))

    return extensions

def read_functions(tokens):

    functions = []

    dot_parts = tuple(tokens[1].split("."))

    if len(dot_parts) == 2:

        domain, f = dot_parts
        image = tokens[2]
        functions.append((domain, f, image))

    else:
        pass # Raise ill-formed sort declaration error, show line

    return functions

def read_rules(text, default_variables):

    lines = [t.strip() for t in text.split("\n\n")]

    rules = []

    for rule_candidate in lines:

        if check_line(rule_candidate):
            rules.append(read_rule(rule_candidate, default_variables))

        else:
            pass # Raise ill-formed rule error

    return rules

def check_line(text):
    # Exactly one =>
    # n predicates, n > 1, and n - 1 vees
    # n predicates, n > 1, and n - 1 conjunctions
    # => and False
    # head is well formed
    # body is well formed
    # Exactly one = or != per clause predicate

    checks = True
    
    not_empty = len(text) > 0
    checks = checks and not_empty

    if not checks:
        return checks

    not_a_sort = text[0:5] != "sort "
    checks = checks and not_a_sort

    implies = re.findall("=>", text)
    only_one_imply = len(implies) <= 1
    checks = checks and only_one_imply

    return checks

def read_rule(line, defaults):

    is_disjunction = " v " in line
    is_contradiction = "=> False" in line
    is_implication = "=>" in line and not is_contradiction
    is_assertion = "=>" not in line and not is_disjunction

    if is_implication:
        return read_implication(line, defaults)

    if is_contradiction:
        return read_contradiction(line, defaults)

    if is_disjunction:
        return read_disjunction(line, defaults)

    # Assertions with variables are allowed

    if is_assertion:
        return read_assertion(line, defaults)

def read_implication(line, defaults):
    body_part, head_part = tuple(line.split("=>")) # Shouldn't this be stripped?
    body, body_sorts = split_predicates(body_part, defaults)
    head, head_sorts = split_predicates(head_part, defaults)
    sorts = body_sorts | head_sorts
    return (IMPLICATION, sorts, body, head)

def read_contradiction(line, defaults):
    body_part = line[:-8]
    body, sorts = split_predicates(body_part, defaults)
    return (CONTRADICTION, sorts, body)

def read_disjunction(line, defaults):
    body, sorts = split_predicates(line, defaults)
    return (DISJUNCTION, sorts, body)

def read_assertion(line, defaults):
    head, sorts = split_predicates(line, defaults)
    return (ASSERTION, sorts, head)

def split_predicates(text, default_sorts):

    predicates = []
    sorts = {}

    while text:
        predicate, chunk_sorts, text = chunk_predicate(text, default_sorts)
        predicates.append(predicate)
        sorts |= chunk_sorts

    return predicates, sorts


def chunk_predicate(text, defaults):
    _chunk, text = chunk(text)
    terms, sorts = get_terms(_chunk, defaults)
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
        connective_skip = chunk_end

    chunk = text[:chunk_end]
    text = text[connective_skip:]

    return chunk, text

def get_terms(text, defaults):

    terms = []
    sorts = {}

    is_comparison = EQUALS in text or NEQUALS in text
    is_predicate = LPAREN in text and RPAREN in text

    # Make sure you never have an overlap
    # between these conditions

    if is_comparison:
        terms, sorts = get_comparison_parts(text, defaults)

    elif is_predicate:
        terms, sorts = get_predicate_parts(text, defaults)

    else:
        print(text)
        assert False

    terms = [strip_sort(t) for t in terms]

    return terms, sorts

def get_predicate_parts(text, defaults):
    lparen_index = text.index("(")
    rparen_index = text.index(")")
    predicate_term = text[:lparen_index]
    term_segment = text[lparen_index + 1 : rparen_index]
    terms = [predicate_term]
    terms = terms + term_segment.split(CONJUNCTION)
    terms = [t.strip() for t in terms]
    sorts = get_term_sorts(terms, defaults)
    return terms, sorts

def get_comparison_parts(text, default_sorts):

    if NEQUALS in text:
        left_term, right_term = [t.strip() for t in text.split(NEQUALS)]
        terms = [left_term, NEQUALS, right_term]
        sorts = get_term_sorts(terms, default_sorts)

    elif EQUALS in text:
        left_term, right_term = [t.strip() for t in text.split(EQUALS)]
        terms = [left_term, EQUALS, right_term]
        sorts = get_term_sorts(terms, default_sorts)

    return terms, sorts

def get_term_sorts(terms, default_sorts):

    sorts = []
    sorted_terms = [t for t in terms if SORT_ASSIGNMENT in t]
    default_sorted_terms = [t for t in terms if t in default_sorts.keys()]

    for t in sorted_terms:
        parts = [r.strip() for r in t.split(SORT_ASSIGNMENT)]
        sorts.append(tuple(parts))
        
    for t in default_sorted_terms:
        sorts.append((t, default_sorts[t]))

    return dict(sorts)

def strip_sort(term):

    if SORT_ASSIGNMENT not in term:
        return term
    
    else:
        return term.split(SORT_ASSIGNMENT).pop(0).strip()

def make_rule(rule_tuple, solver):

    rule_type = rule_tuple[0]

    is_implication = rule_type == IMPLICATION
    is_assertion = rule_type == ASSERTION
    is_disjunction  = rule_type == DISJUNCTION
    is_contradiction = rule_type == CONTRADICTION

    conditions = [is_implication, is_disjunction, is_assertion, is_contradiction]

    sorts = set({})
    body = []
    head = []
    flags = set({})

    if is_implication:

        _, sorts, body, head = rule_tuple

    elif is_assertion:

        _, sorts, head = rule_tuple
        
    elif is_contradiction:

        _, sorts, body = rule_tuple

    elif is_disjunction:

        _, sorts, body = rule_tuple

        flags = {DISJUNCTION_FLAG}

    body_relations = [Relation(terms) for terms in body]
    head_relations = [Relation(terms) for terms in head]

    sorts_items = list(sorts.items())

    rule_sorts = [v for k, v in sorts_items]
    rule_variables = [k for k, v in sorts_items]

    bindings = {}

    return Rule(head_relations,
                body_relations,
                rule_sorts,
                rule_variables,
                solver,
                bindings,
                flags)
                
def read_into(program, solver, verbose=False):

    if verbose:
        print("Program: ", program)
    
    normalized_program = normalize(program)
    _, rules, variables = read_program(normalized_program)
    
    if verbose:
        for r in rules:
            print("Rule: ", r)
    
    for rule_data in rules:
        new_rule = make_rule(rule_data, solver)
        if verbose:
            print(new_rule)
        solver.rules.append(new_rule)

