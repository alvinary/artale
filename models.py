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

        self.literal_map = {}
        self.reverse_literal_map = {}
        self.value_map = {}

    def unfold_rule(self, rule):
        
        for assignment in product(*[self.sorts[s] for s in rule.sorts]):
  
            clauses = rule.get_clauses(assignment)

            pure_clauses = [self.evaluate_functions(c) for c in clauses]
  
            self.update_maps(pure_clauses)
  
            if IS_DISJUNCTION in rule.flags:
                cnf_clauses = [self.disjunction_dimacs(c) for c in pure_clauses]
  
            else:
                cnf_clauses = [self.dimacs(c) for c in pure_clauses]
  
            for cnf_clause in cnf_clauses:
                self.solver.add_clause(cnf_clause)
                self.cnf_clauses.append(array("l", cnf_clause))

    def unfold_instance(self):
        for rule in self.rules:
            self.unfold_rule(rule)

    def una_equality(self):
        for s in self.sorts:
            for c1 in self.sorts[s]:
                for c2 in self.sorts[s]:
                    equality = f"{c1} = {c2}"
                    if c1 != c2:
                        pure_clause = Clause(f"{c1} != {c2}", [])
                        pure_clauses = [pure_clause]
                        self.update_maps(pure_clauses)
                        self.solver.add_clause(self.dimacs(pure_clause))
                    elif c1 == c2 and equality not in self.literal_map:
                        pure_clause = Clause(equality, [])
                        pure_clauses = [pure_clause]
                        self.update_maps(pure_clauses)
                        self.solver.add_clause(self.dimacs(pure_clause))

    def is_functional(self, term_string):
        return "." in term_string

    def dimacs(self, pure_clause):

        dimacs_clause = []

        if pure_clause.head != "":
            dimacs_clause.append(self.literal_map[pure_clause.head])

        for atom in pure_clause.body:
            dimacs_clause.append(-self.literal_map[atom])

        return dimacs_clause

    def disjunction_dimacs(self, pure_clause):
        return [self.literal_map[atom] for atom in pure_clause.body]

    def evaluate(self, term_string):

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

        function_free_clause = copy(clause)
        function_free_clause.head = self.evaluate(function_free_clause.head)
        function_free_clause.body = [
            self.evaluate(atom) for atom in function_free_clause.body
        ]

        return function_free_clause

    def update_maps(self, clauses):

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

        Return a JSON object whose fields are .clauses, .literals
        
        - The first field is an array of arrays encoding the CNF instance stored in self.solver.
        
        - The second field is an array of (key, value) pairs associating CNF literals to string atoms.

        Since the map in the second field is invertible, there is no need to serialize a map
        from string atoms to CNF literals.

        '''

        cnf_clauses = [c.tolist() for c in self.cnf_clauses]

        return as_json( { clauses : cnf_clauses , literals : self.literal_map } )
        

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


