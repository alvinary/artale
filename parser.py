from lark import Lark, Tree, Token

grammar = ""

with open("grammar") as grammar_file:
    for line in grammar_file:
        grammar = grammar + line

def get_preterminal(lark_tree):
    return lark_tree.data[0:]

def get_head(rule_tree):
    pass

def get_body(rule_tree):
    pass

def get_atoms(atoms_tree):
    pass

def get_terms(atom_tree):
    pass

def get_tokens(term_tree):
    pass

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
        program = self.prepocess(program)
        parsed_program = self.parser.parse(program)
        statements = [s for s in parsed_program.children if isinstance(s, Tree)]
        sorts = [s for s in statements if get_preterminal(s) == "sort"]
        rules = [s for s in statements if get_preterminal(s) == "rule"]

    def declutter_tree(self, tree):

        if isinstance(tree, Tree):
            if get_preterminal(tree) == "sort":
                return 
        
        if isinstance(tree, Token):
            pass

    def get_rules(self, program):

        return "Je"
        
