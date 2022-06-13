from collections import defaultdict
from typing import List, Dict, Set
from itertools import product
from dataclasses import dataclass
from copy import copy
from json import dumps as as_json
from array import array

from pysat.solvers import Solver

TERM_SEPARATOR = "--"
IS_DISJUNCTION = "vee"
ANY = "any"


def is_any(name):
    return "any" in name


def index():
    return defaultdict(lambda: [])


class HornSolver:

    def __init__(self):

        self.sorts = index()
        self.rules = []
        self.literals = set()
        self.clauses = []
        self.value_map = {}
        self.literal_map = {}
        self.reverse_literal_map = {}
        self.solver = Solver()
        self.name_counter = 0
        self.cnf_clauses = list()

    def reset_maps(self):
        '''

        Assign empty dictionaries to self.literal_map, self.value_map and
        self.value_map.

        '''

        self.literal_map = {}
        self.reverse_literal_map = {}
        self.value_map = {}

    def opt_unfold(self):

        rule_groups = group_rules(self.rules)

        for signature in rule_groups:

            sort_mapping = []
            signature_rules = rule_groups[signature]

            for rule in signature_rules:
                index_permutation = get_permutation(signature, rule)
                sort_mapping.append(index_permutation)

            for signature_assignment in product():

                for rule_index, rule in enumerate(signature_rules):

                    signature_mapping = sort_mapping[rule_index]
                    rule_assignment = map_on(signature_assignment,
                                             signature_mapping)

                    # the res as usuañ




    def unfold_rule(self, rule):
        '''

        Obtain a list of clauses encoding a propositional embedding of the
        first-order input rule and add them to the CNF formula stored by the
        SAT solver in self.solver.

        As a side effect, new clauses are appended to self.cnf_clauses.

        '''

        print("Rule: ", rule.body, rule.heads)

        for assignment in product(*[self.sorts[s] for s in rule.sorts]):

            print(assignment)

            clauses = rule.get_clauses(assignment)

            pure_clauses = [self.evaluate_functions(c) for c in clauses]

            self.update_maps(pure_clauses)

            if IS_DISJUNCTION in rule.flags:
                cnf_clauses = [
                    self.disjunction_dimacs(c) for c in pure_clauses
                ]

            else:
                cnf_clauses = [self.dimacs(c) for c in pure_clauses]

            for cnf_clause in cnf_clauses:
                self.solver.add_clause(cnf_clause)
                self.cnf_clauses.append(array("l", cnf_clause))

    def unfold_instance(self):
        '''

        Embed all first-order rules stored in self.rules into a 
        propositional CNF formula and add its clauses to the CNF
        used by self.solver.

        '''

        for rule in self.rules:
            self.unfold_rule(rule)

    def reset_instance(self):
        '''

        Discard the current SAT solver, assign a new Solver object to
        self.solver, and replace the problem instance CNF in cnf_clauses
        with an empty list.

        '''

        self.solver = Solver()
        self.cnf_clauses = list()

    def add_assertion(self, predicate_string):
        '''

        Input a predicate as a string (e.g. "p (a, b)", "a != b", "r (a.f, a.g)") and
        add a CNF clause with a single positive literal to the solver CNF, updating
        self's map from predicates to DIMACS literals and DIMACS literals to predicates.
        
        '''

        assertion_clause = Clause(predicate_string, [])
        self.update_maps([assertion_clause])
        self.solver.add_clause(self.dimacs(assertion_clause))

    def una_equality(self):
        '''

        Embed equality as defined when making the unique-name assumption into
        the solver's CNF problem instance - i.e. if 'a' and 'b' are constants
        in the same sort, a != b iff a and b are different constants.

        '''

        for s in self.sorts:
            for c1 in self.sorts[s]:
                for c2 in self.sorts[s]:
                    equality = f"{c1} = {c2}"
                    inequality = f"{c1} != {c2}"
                    if c1 != c2:
                        self.add_assertion(inequality)
                    elif c1 == c2 and equality not in self.literal_map:
                        self.add_assertion(equality)

    def is_functional(self, term_string):
        '''

        Check if a term contains function applications (i.e. it is not
        a constant name, but has at least one function application, such
        as a.f.g or pair.first).

        '''

        return "." in term_string

    def dimacs(self, pure_clause):
        '''

        Return a list encoding the dimacs representation of a clause
        containing only constants terms (i.e. terms that are constant
        names / are not functional terms).

        The input clause must be a Horn clause.
        
        HornSolver.disjunction_dimacs() can be used for arbitrary
        disjunctions-

        '''

        dimacs_clause = []

        if pure_clause.head != "":
            dimacs_clause.append(self.literal_map[pure_clause.head])

        for atom in pure_clause.body:
            dimacs_clause.append(-self.literal_map[atom])

        return dimacs_clause

    def disjunction_dimacs(self, pure_clause):
        '''

        Return a list encoding the dimacs represention of a CNF clause
        containing only constant names as terms.

        '''

        return [self.literal_map[atom] for atom in pure_clause.body]

    def evaluate(self, term_string):
        '''

        Return the single constant name that results from evaluating all
        functions in the input term string.

        If the input term is already a single constant name, then it
        is returned unchanged.

        '''

        terms = term_string.split(TERM_SEPARATOR)
        evaluated_terms = []

        for term in terms:

            parts = [t.strip() for t in term.split(".")]

            domain = parts.pop(0)

            image = domain

            while parts:

                image = self.value_map[domain, parts.pop(0)]

                domain = image

            evaluated_terms.append(image)

        return " ".join(evaluated_terms)

    def evaluate_functions(self, clause):
        '''

        Evaluate all function applications that appear in the input clause
        and return an equivalent clause whose terms are exclusively constant
        names.

        '''

        function_free_clause = copy(clause)
        function_free_clause.head = self.evaluate(function_free_clause.head)
        function_free_clause.body = [
            self.evaluate(atom) for atom in function_free_clause.body
        ]

        return function_free_clause

    def update_maps(self, clauses):
        '''

        Update the dictionaries mapping atoms in string form to and form atoms
        represented as DIMACS literals (i.e. if any of the input clauses contains
        one or more atoms that have not yet been given a DIMACS representation,
        they are assigned a new integer).

        '''

        all_symbols = set()

        for c in clauses:
            all_symbols.add(c.head)
            all_symbols |= set(c.body)

        new_symbols = {s for s in all_symbols if s not in self.literal_map}

        for s in new_symbols:
            self.name_counter += 1
            self.literal_map[s] = self.name_counter
            self.reverse_literal_map[self.name_counter] = s

    def show_model(self, model, show_false=False):
        '''

        Given a model in DIMACS form, return a single string
        containing all true atoms in a human-readable string form.

        If show_false is set to True, false atoms are included as well.

        '''

        readable_model = ""
        counter = 1

        if not show_false:
            atoms = [self.reverse_literal_map[a] for a in model if a > 0]
            atoms = [a for a in atoms if "=" not in a]

        if show_false:
            atoms = []
            for a in model:
                if a > 0:
                    atoms.append(self.reverse_literal_map[a])
                else:
                    atoms.append(f"- {self.reverse_literal_map[abs(a)]}")

        for atom in atoms:
            readable_model = f"{readable_model}, {atom}"
            counter += 1
            counter = counter % 9
            if counter == 0:
                readable_model = readable_model + "\n"

        return readable_model

    def get_relations(self, model, target_relations):
        '''

        Return a set containing all atoms in the input model that
        are contained in target_relations.

        '''

        relations = set()

        for atom in model:
            if atom > 0:
                relation = tuple(self.reverse_literal_map[atom].split(" "))
                predicate = relation[0]
                if predicate in target_relations:
                    relations.add(relation)

        return relations

    def serialize(self):
        '''

        Return the string encoding of a JSON object whose fields are .clauses, .literals and .values.
        
        - The first field is an array of arrays encoding the CNF instance stored in self.solver.
        
        - The second field is an array of (key, value) pairs associating CNF literals to string atoms.

        - The third field serializes self.value_map as an array of triples (key1, key2, self.value_map[key1, key2]).

        Since the map in the second field is invertible, there is no need to serialize a map
        from string atoms to CNF literals.

        '''

        cnf_clauses = [c.tolist() for c in self.cnf_clauses]
        value_triples = [(a, f, self.value_map[a, f])
                         for (a, f) in self.value_map]

        return as_json({
            'clauses': cnf_clauses,
            'literals': self.literal_map,
            'values': value_triples
        })

def group_rules(rules):
    '''

    Input a list of rules and return a dictionary grouping
    rules by their 'predicate signature' (i.e. if two
    predicates range over two variables of the same sort,
    they are grouped together, same as four rules ranging
    over a single variable of the same sort).

    '''
    sorts_map = {}
    for r in rules:
        sorts_tuple = tuple(sorted(r.sorts))
        sorts_map[sorts_tuple].append(r)
    return sorts_map

def get_permutation(ordered_sorts, assorted_sorts):
    index_permutation = []
    last_index = dict([(s, 0) for s in ordered_sorts])
    for sort in assorted_sorts:
        low_index = last_index[sort]
        top_index = ordered_sorts.index(sort, low_index)
        last_index[sort] = top_index + 1
        index_permutation.append(top_index)
    return tuple(index_permutation)

def map_on(assignment, index_permutation):
    assignment_permutation = []
    for index in index_permutation:
        assignment_permutation.append(assignment[index])
    return tuple(assignment_permutation)

@dataclass
class Relation:
    parts: List[str]

    def get_string_encoding(self):
        return TERM_SEPARATOR.join([p.strip() for p in self.parts])


@dataclass
class Clause:
    head: str
    body: List[str]


@dataclass
class Rule:
    heads: List[Relation]
    body: List[Relation]
    sorts: List[str]
    variables: List[str]
    solver: HornSolver

    bindings: Dict[str, str]

    flags: Set[str]

    def get_clauses(self, assignment):

        has_any = True in [is_any(v) for v in self.variables]

        if not has_any:

            self.rebind(assignment)

            heads = [self.bind_variables(r) for r in self.heads]
            body = [self.bind_variables(r) for r in self.body]

        if has_any:

            self.guarded_rebind(assignment)

            nested_heads = [self.bind_any_variables(r) for r in self.heads]
            nested_body = [self.bind_any_variables(r) for r in self.body]

            heads = [r for h in nested_heads for r in h]
            body = [r for b in nested_body for r in b]

        string_heads = [r.get_string_encoding() for r in heads]
        string_body = [r.get_string_encoding() for r in body]

        if string_heads:
            return [Clause(h, string_body) for h in string_heads]

        else:
            return [Clause("", string_body)]

    def rebind(self, assignment):
        for variable, value in zip(self.variables, assignment):
            self.bindings[variable] = value

    def guarded_rebind(self, assignment):
        for variable, value in zip(self.variables, assignment):
            if not is_any(variable):
                self.bindings[variable] = value

    def bind_any_variables(self, relation):
        relations = []
        checked = set()

        pairs = [(n, s) for (n, s) in zip(self.variables, self.sorts)]

        any_pairs = [(n, s) for (n, s) in pairs if is_any(n)]
        any_names = product([n for (n, s) in any_pairs])
        any_sorts = product(*[self.solver.sorts[s] for (n, s) in any_pairs])

        any_bindings = product(any_names, any_sorts)

        for names, bindees in any_bindings:

            for n, b in zip(names, bindees):
                self.bindings[n] = b

            new_relation = Relation([self.replace(s) for s in relation.parts])
            hashable_new_relation = new_relation.get_string_encoding()

            if hashable_new_relation not in checked:
                relations.append(new_relation)
            checked.add(hashable_new_relation)

        return relations

    def bind_variables(self, relation):
        return Relation([self.replace(s) for s in relation.parts])

    def replace(self, symbol):

        if "." not in symbol:

            if symbol in self.bindings:
                return self.bindings[symbol]

            else:
                return symbol

        if "." in symbol:

            symbol_parts = [p.strip() for p in symbol.split(".")]
            return ".".join([self.replace(s) for s in symbol_parts])

    def rename_any(self):
        raise NotImplementedError
