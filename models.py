from collections import defaultdict
from typing import List, Dict, Set
from itertools import product
from dataclasses import dataclass
from copy import copy
from json import dumps as as_json
from array import array
from functools import reduce, lru_cache, cache

from pysat.solvers import Solver

TERM_SEPARATOR = "--"
IS_DISJUNCTION = "vee"
ANY = "any"

@cache
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
        self.verbose = False

    def fill_sort(self, sort, n):
        '''

        Add n constants named '{sort} 1', '{sort} 2', '{sort} 3', ... ,
        '{sort} n' to the sort provided as argument.
        
        '''
        
        for i in range(n):
            self.sorts[sort].append(f"{sort}{i + 1}")

    def add_element(self, sort, name):
        '''
        
        Add a constant named 'name' to the sort provided as argument
        
        '''
        
        self.sorts[sort].append(name)
        
    def assign(self, f, x, v):
        '''
        
        Assign value 'v' to 'f(x)' (i.e. x.f will evaluate to v)
        
        '''
        self.value_map[f, x] = v

    def reset_maps(self):
        '''

        Assign empty dictionaries to self.literal_map, 
        self.reverse_literal_map and self.value_map.

        '''

        self.literal_map = {}
        self.reverse_literal_map = {}
        self.value_map = {}

    def unfold_rule(self, rule, sort_restrictions={}):
        '''

        Obtain a list of clauses encoding a propositional embedding of the
        first-order input rule and add them to the CNF formula stored by the
        SAT solver in self.solver.

        As a side effect, new clauses are appended to self.cnf_clauses.

        '''
        
        if sort_restrictions:
            old_sorts = {}
            for sort in sort_restrictions.keys():
                all_members = self.sorts[sort]
                restricted_members = sort_restrictions[sort]
                self.sorts[sort] = restricted_members
        
        if self.verbose:
            mult = lambda x, y: x * y
            prod = lambda x: reduce(mult, x, 1)
            no_assignments = prod([len(self.sorts[s]) for s in rule.sorts])
            print(f"There are {no_assignments} to unfold left!")
            print(" * ".join(rule.sorts))
            chunks = no_assignments // 100000
            count = 0
            print("*" * chunks)

        for assignment in product(*[self.sorts[s] for s in rule.sorts]):

            clauses = rule.get_clauses(assignment)

            pure_clauses = [self.evaluate_functions(c) for c in clauses]

            self.update_maps(pure_clauses)

            if IS_DISJUNCTION in rule.flags:
                cnf_clauses = [
                    self.disjunction_dimacs(c) for c in pure_clauses
                ]

            else:
                cnf_clauses = [self.dimacs(c) for c in pure_clauses]

            cnf_clauses = [c for c in cnf_clauses if len(c) > 0]

            for cnf_clause in cnf_clauses:
                self.solver.add_clause(cnf_clause)
                self.cnf_clauses.append(array("l", cnf_clause))
            
            if self.verbose:
                count += 1
                if count > 100000:
                    count = 0
                    chunks -= 1
                    print("*" * chunks)
                    
        if sort_restrictions:
            for sort in old_sorts.keys():
                self.sorts[sort] = old_sorts[sort]
            
                

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
        dimacs_clause = self.dimacs(assertion_clause)
        self.solver.add_clause(dimacs_clause)
        self.cnf_clauses.append(dimacs_clause)

    def unfold_una(self):
        '''

        Embed equality as defined when making the unique-name assumption into
        the solver's CNF problem instance - i.e. if 'a' and 'b' are constants
        in the same sort, a != b iff a and b are different constants.

        '''

        for s in self.sorts:
        
            checked_assertions = set()
        
            for c1, c2 in product(self.sorts[s], self.sorts[s]):
            
                equality = f"{c1} = {c2}"
                inequality = f"{c1} != {c2}"
                
                if c1 != c2 and inequality not in checked_assertions:
                    self.add_assertion(inequality)
                    checked_assertions.add(inequality)
                    
                if c1 == c2 and equality not in checked_assertions:
                    self.add_assertion(equality)
                    checked_assertions.add(equality)

    @lru_cache(maxsize=512)
    def is_functional(self, term_string):
        '''

        Check if a term contains function applications (i.e. it has
        at least one function application, like a.f.g or pair.first).

        '''

        return "." in term_string

    def dimacs(self, pure_clause):
        '''

        Return a list encoding the dimacs representation of a clause
        containing only constant terms (i.e. terms without function
        application).

        The input clause must be a Horn clause, but
        HornSolver.disjunction_dimacs() can be used for unrestricted
        disjunctions.

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

    @lru_cache(maxsize=512)
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

            x = parts.pop(0)

            a = x

            while parts:

                f = parts.pop(0)

                a = self.value_map[f, x]

                x = a

            evaluated_terms.append(a)

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
            
    def get_model(self):
        '''
        
        If the problem instance is satisfiable, return
        (True, model), where model is a list of integer
        literals.
        
        Else, return (False, [])
        
        '''
        solvable = self.solver.solve()
        if solvable:
            model = self.solver.get_model()
            return (True, model)
        else:
            return (False, [])
            
    def model_with(self, statements):
        '''
        
        Check if there is a model satisfying the current
        problem instance, adding the statements in 'statements'
        as additional assumptions (which are not added permanently
        to the solver's problem instance).
        
        The statements must be provided as strings, since
        they are 'translated' to DIMACS using a map from
        string to integer literals stored in HornSolver.literal_map
        
        If the problem instance is satisfiable, return
        (True, model), where model is a list of integer
        literals.
        
        Else, return (False, [])
        
        '''
        literals = [self.literal_map[s] for s in statements]
        solvable = self.solver.solve(literals)
        if solvable:
            model = self.solver.get_model()
            return (True, model)
        else:
            return (False, [])

    def show_model(self, model, show_false=False):
        '''

        Given a model in DIMACS form, return a single string
        containing all true atoms in a human-readable string form.

        If show_false is set to True, false atoms are included as well.

        '''

        readable_model = ""

        if not show_false:
            atoms = [self.reverse_literal_map[a] for a in model if a > 0]
            atoms = [a for a in atoms if "=" not in a]
            atoms = [a for a in atoms if "not " != a[:4]]

        if show_false:
            atoms = []
            for a in model:
                if a > 0:
                    atoms.append(self.reverse_literal_map[a])
                else:
                    atoms.append(f"- {self.reverse_literal_map[abs(a)]}")

        readable_model = ""
        line = ""
        
        for atom in atoms:
        
            line = f"{line}{atom}, "
            line_length = len(line)
            
            if line_length > 60:
                readable_model = readable_model + line + "\n"
                line = ""

        return readable_model
        
    def show_clauses(self):
        '''
        
        Return a list containing all clauses stored in the solver's
        problem instance, encoded as tuples of strings (the first
        component is the dimacs representation of the clause, the
        second component is a human-readable representation of the clause)
        
        '''
        clauses = []
        for c in self.cnf_clauses:
            head = [self.reverse_literal_map[a] for a in c if a > 0]
            body = [self.reverse_literal_map[abs(a)] for a in c if a < 0]
            body = [f"- {b}" for b in body]
            literals = [str(a) for a in c]
            clauses.append((", ".join(literals), ", ".join(body + head)))
        return clauses

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
        value_triples = [(f, x, self.value_map[f, x])
                         for (f, x) in self.value_map]

        return as_json({
            'clauses': cnf_clauses,
            'literals': self.literal_map,
            'values': value_triples
        })

    def rule_from_parts(self, body, head, variable_sort_pairs, flags):

        head_atoms = [Relation([term for term in atom]) for atom in head]
        body_atoms = [Relation([term for term in atom]) for atom in body]
        sorts = [s for _, s in variable_sort_pairs]
        variables = [v for v, _ in variable_sort_pairs]

        new_rule = Rule(head_atoms,
                        body_atoms,
                        sorts, variables,
                        self, {}, flags)

        self.rules.append(new_rule)

def group_rules(rules):
    '''

    Input a list of rules and return a dictionary grouping
    rules by their 'predicate signature' (i.e. if two
    predicates range over two variables of the same sort,
    they are grouped together, same as four rules ranging
    over a single variable of the same sort).

    '''
    sorts_map = index()
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

    def as_string(self):
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

        string_heads = [r.as_string() for r in heads]
        string_body = [r.as_string() for r in body]

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
            hashable_new_relation = new_relation.as_string()

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

    def as_string(self):

        body_atoms = [b.as_string() for b in self.body]
        rule_body = ", ".join(body_atoms)

        head_atoms = [h.as_string() for h in self.heads]
        rule_head = ", ".join(head_atoms)

        if not head_atoms:
            rule_head = "False"

        rule_string = f"{rule_body} => {rule_head}"
        rule_string = rule_string.replace(TERM_SEPARATOR, " ")

        return rule_string
