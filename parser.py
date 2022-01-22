from lark import Lark, Tree, Token

grammar = ""

with open("grammar") as grammar_file:
    for line in grammar_file:
        grammar = grammar + line

def normalize(term_string):

    while "  " in term_string:
        term_string = term_string.replace("  ", " ")

    return clear_sorts(term_string).strip()

def clear_sorts(term_string):

    if ":" in term_string:
        colon_index = term_string.index(":")
        return term_string[:colon_index].strip()

    else:
        return term_string

def get_preterminal(lark_tree):
    return lark_tree.data[0:]

def get_head(rule_tree):
    atomic_children = [c for c in rule_tree.children if not isinstance(c, Token)]
    if len(atomic_children) >= 2:
        return atomic_children[1]
    else:
        return None

def get_body(rule_tree):
    atomic_children = [c for c in rule_tree.children if not isinstance(c, Token)]
    return atomic_children[0]

def get_atoms(atoms_tree):
    return [c for c in atoms_tree.children if isinstance(c, Tree)]

def get_terms(atom_tree):
    return [c for c in atom_tree.children if isinstance(c, Tree)]

def get_tokens(term_tree):
    tokens = []
    for i, c in enumerate([t for t in term_tree.children if isinstance(t, Tree)]):
         if i != 0:
             tokens.append(".")
         tokens = tokens + ([_c.strip() for _c in c.children if isinstance(_c, Token)])
    return tokens

def get_variables(term_lists):
    variables = set()
    for terms in term_lists:
        new_variables = {tuple([s.strip() for s in t.split(":")]) for t in terms if ":" in t}
        variables |= new_variables
    return {(normalize(v), normalize(s)) for v, s in variables}

def get_sorts(term_lists):
    return [s for v, s in get_variables(term_lists)]


class Parser:

    def __init__(self):

        self.parser = Lark(grammar)

    def preprocess(self, program):

        program = program.replace("=>", " => ")
        program = program.replace(",", ", ")

        while " \n" in program:
            program = program.replace(" \n", "\n")

        while "  " in program:
            program = program.replace("  ", " ")

        while " ," in program:
            program = program.replace(" ,", ",")

        while " )" in program:
            program = program.replace(" )", ")")

        while "( " in program:
            program = program.replace("( ", "(")

        parts = [part.strip() for part in program.split("\n")]

        return "\n".join(parts)

    def parse(self, program):
        program = self.preprocess(program)
        parsed_program = self.parser.parse(program)
        statements = [s for s in parsed_program.children if isinstance(s, Tree)]
        sorts = [s for s in statements if get_preterminal(s) == "sort"]
        rules = [s for s in statements if get_preterminal(s) == "rule"]
        assertions = [s for s in statements if get_preterminal(s) == "assertion"]

        # Fillings are sort declarations of the form 'sort name nat',
        # intended for users to define a sort populated by uniform constants
        
        # Additions are sort delcarations of the form 'sort name add c1, c2, c3, ...',
        # intended for users to define distinguished elements of a sort
        
        fillings = []
        additions = [] 
        for sort in sorts:
            if True:
                pass
            if True:
                pass

        sorts_parts = []
        rule_parts = []

        for rule in rules:

            head = get_head(rule)
            
            if not head:
                head_atoms = []
            else:
                head_atoms = get_atoms(get_head(rule))
            
            body_atoms = get_atoms(get_body(rule))
            
            body = [[" ".join(get_tokens(t)).strip() for t in get_terms(a)] for a in body_atoms]
            head = [[" ".join(get_tokens(t)).strip() for t in get_terms(a)] for a in head_atoms]
            
            variables = get_variables(body + head)
            sorts = get_sorts(body + head)

            body = [[normalize(s) for s in a] for a in body]
            head = [[normalize(s) for s in a] for a in head]

            rule_parts.append((body, head, variables, sorts))

        for assertion in assertions:
            
            head_atoms = get_atoms(get_body(assertion))

            head = [[" ".join(get_tokens(t)).strip() for t in get_terms(a)] for a in head_atoms]
            head = [[normalize(s) for s in a] for a in head]

            rule_parts.append(([], head, [], []))

        return sorts_parts, rule_parts


