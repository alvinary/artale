from lark import Lark, Tree, Token

IS_DISJUNCTION = "vee"
IS_ASSERTION = "wedge"
IS_CLAUSE = "arrow"

grammar = ""

with open("grammar") as grammar_file:
    for line in grammar_file:
        grammar = grammar + line


def normalize(term_string):
    '''Remove all excess whitespace from a string encoding a term and remove
    its sort, if present (e.g. 'my   sample term   : some sort') maps
    to 'my sample term').'''

    while "  " in term_string:
        term_string = term_string.replace("  ", " ")

    return clear_sorts(term_string).strip()


def clear_sorts(term_string):
    '''Remove a term's sort from its string encoding (e.g. 'some pony : pony'
    maps to 'some pony').'''

    if ":" in term_string:
        colon_index = term_string.index(":")
        return term_string[:colon_index].strip()

    else:
        return term_string


def get_preterminal(lark_tree):
    '''Given a Lark Tree object, return the name of the corresponding 
    preterminal symbol in the grammar as a string (e.g. if a parse 
    was derived from the rule many_as -> a _many_as, return the string 
    'many_as').'''
    return lark_tree.data[0:]


def get_head(rule_tree):
    '''Given a Lark Tree object matching the preterminal 'rule', return
    the Lark object matching its head, and return None if the rule does
    not have any positive literal/atom (e.g. a parse of the rule 
    'p(x), q(x, y) => r(x)' maps to the parse of 'r(x)', and 'r(x) => False'
    maps to None).'''

    atomic_children = [
        c for c in rule_tree.children if not isinstance(c, Token)
    ]
    if len(atomic_children) >= 2:
        return atomic_children[1]
    else:
        return None


def get_body(rule_tree):
    '''Given a Lark Tree object matching the preterminal 'rule', return
    the Lark object matching its body (e.g. a parse of the rule 
    'p(x, y), q(y, x) => r(x, y)' maps to the parse of 'p(x, y), q(y, x)').'''
    
    atomic_children = [
        c for c in rule_tree.children if not isinstance(c, Token)
    ]
    return atomic_children[0]

def get_disjuncts(rule_tree):
    disjuncts = [
        c for c in rule_tree.children if not isinstance(c, Token)
    ]
    return [d for d in disjuncts if get_preterminal(d) == "atom"]

def get_atoms(atoms_tree):
    '''Return all atoms in the parse of a programs segment matching
    the 'atoms' preterminal (i.e. all of its children that are not
    terminals/tokens, which should be newlines or whitespaces).
    For instance, 'p(x, y), q(x), r(y)' maps to the parses of
    each of its atoms ('p(x, y)', 'q(x)' and 'r(y)').'''
    return [c for c in atoms_tree.children if isinstance(c, Tree)]


def get_terms(atom_tree):
    '''Return a list containing all parse trees matching a term
    given an atom tree (this function is identical to get_atoms(), but
    was defined and named differently to favor clarity by making
    the purpose of each call explicit).'''
    return [c for c in atom_tree.children if isinstance(c, Tree)]


def get_tokens(term_tree):
    '''Given the parse tree of a term, return a string encoding that
    term (e.g. a term resulting from parsing 'a.f.g' maps directly to
    'a.f.g').'''
    tokens = []
    for i, c in enumerate(
        [t for t in term_tree.children if isinstance(t, Tree)]):
        if i != 0:
            tokens.append(".")
        tokens = tokens + (
            [_c.strip() for _c in c.children if isinstance(_c, Token)])
    return tokens


def get_variables(term_lists):
    '''Given a list of terms encoded as strings, return a set
    of (variable name, variable sort) pairs. All variables 
    mentioned in terms from the input list are included.

    If a term has function applications, the part considered
    to be a variable is the first, so 'a.f.g : A' results
    in the name 'a' being taken as a variable drawn from sort
    A.
    Only terms where the sort membership symbol ':' is included
    are considered variables. All other terms are treated as
    constants.
    If two different sorts are assigned to the same variable symbol
    -as in p(a: A, a: B)-, behavior is undefined.'''
    variables = set()

    for terms in term_lists:
        new_variables = {
            tuple([s.strip() for s in t.split(":")])
            for t in terms if ":" in t
        }
        variables |= new_variables

    variables = {(normalize(v), normalize(s)) for v, s in variables}
    return sorted(list(variables))

def get_sorts(term_lists):
    '''Return a list containing all distinct sort names included
    in sort membership declarations in terms from the input list. '''
    return [s for v, s in get_variables(term_lists)]


class Parser:

    def __init__(self):

        self.parser = Lark(grammar)

    def preprocess(self, program):
        '''Preprocess an input program to match the preconditions of the parser (by
        removing duplicate whitespace and whitespace before newlines, and adding
        whitespace after or before some punctuation symbols -',', '(' and ')'-, and
        making sure instances of the '=>' symbol are surrounded by whitespace). '''

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
        '''Given a program, return a pair '(sorts_part, rules_part)`, provided parsing succeeds.
        'rules_part' is a list of tuples containing the data necessary to create a Rule object
        in the 'models' module, which is
 
       * The body of a rule and its head, both represented as lists
        of atoms, which are lists of strings where each string encodes a term,

       * The list of variables in the rule, with their sorts, and

       * The second component of each element on the previous list.

       Sorts are not yet implemented.'''

        program = self.preprocess(program)
        parsed_program = self.parser.parse(program)
        statements = [
            s for s in parsed_program.children if isinstance(s, Tree)
        ]
        sorts = [s for s in statements if get_preterminal(s) == "sort"]
        rules = [s for s in statements if get_preterminal(s) == "rule"]
        assertions = [
            s for s in statements if get_preterminal(s) == "assertion"
        ]
        disjunctions = [
            s for s in statements if get_preterminal(s) == "disjunction"
        ]

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

            body = [[" ".join(get_tokens(t)).strip() for t in get_terms(a)]
                    for a in body_atoms]
            head = [[" ".join(get_tokens(t)).strip() for t in get_terms(a)]
                    for a in head_atoms]

            variables = get_variables(body + head)
            sorts = get_sorts(body + head)

            body = [[normalize(s) for s in a] for a in body]
            head = [[normalize(s) for s in a] for a in head]

            rule_parts.append((body, head, variables, sorts, {IS_CLAUSE}))

        for assertion in assertions:

            head_atoms = get_atoms(get_body(assertion))

            head = [[" ".join(get_tokens(t)).strip() for t in get_terms(a)]
                    for a in head_atoms]

            variables = get_variables(head)
            sorts = get_sorts(head)

            head = [[normalize(s) for s in a] for a in head]

            rule_parts.append(([], head, variables, sorts, {IS_ASSERTION}))

        for disjunction in disjunctions:

            disjunction_atoms = get_disjuncts(disjunction)

            body = [[" ".join(get_tokens(t)).strip() for t in get_terms(a)]
                    for a in disjunction_atoms]

            variables = get_variables(body)
            sorts = get_variables(body)

            body = [[normalize(s) for s in a] for a in body]

            rule_parts.append((body, [], variables, sorts, {IS_DISJUNCTION}))
        
        return sorts_parts, rule_parts

    def check(program):
        '''Return True if a program is recognized by the parser's grammar, False
        otherwise.'''
        # Should check if the program is valid semantically too!
        # - No variable is declared as being a member of two separate sorts 
        
        try:
            pass

        except:
            pass

