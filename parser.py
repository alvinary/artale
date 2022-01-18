from lark import Lark, Tree, Token

grammar = ""

with open("grammar") as grammar_file:
    for line in grammar_file:
        grammar = grammar + line

def get_preterminal(lark_tree):
    return lark_tree.data[0:]

def get_head(rule_tree):
    print("head: \n", rule_tree.pretty())
    atomic_children = [c for c in rule_tree.children if not isinstance(c, Token)]
    return atomic_children[1]

def get_body(rule_tree):
    print("body: \n", rule_tree.pretty())
    atomic_children = [c for c in rule_tree.children if not isinstance(c, Token)]
    return atomic_children[0]

def get_atoms(atoms_tree):
    print("atoms: \n", atoms_tree.pretty())
    return [c for c in atoms_tree.children if isinstance(c, Tree)]

def get_terms(atom_tree):
    print("terms: \n", atom_tree.pretty())
    return [c for c in atom_tree.children if isinstance(c, Tree)]

def get_tokens(term_tree):
    print("tokens: \n", term_tree.pretty())
    return [c.children[0][0:] for c in term_tree.children if not isinstance(c, Token)]

def get_variables(term_lists):
    return {" ".join(l).split(":") for l in term_lists if ":" in l}

def get_sorts(term_lists):
    return [pair[1] for pair in get_variables(term_lists)]


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
            head_atoms = get_atoms(get_head(rule))
            body_atoms = get_atoms(get_body(rule))
            body = [[".".join(get_tokens(t)) for t in get_terms(a)] for a in body_atoms]
            head = [[".".join(get_tokens(t)) for t in get_terms(a)] for a in head_atoms]
            variables = []
            sorts = []
            #variables = get_variables(body + head)
            #sorts = get_sorts(body + head)
            rule_parts.append((body, head, variables, sorts))

        return sorts_parts, rule_parts


