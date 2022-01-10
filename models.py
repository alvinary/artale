from collections import defaultdict
from typing import List, Dict, Set
from itertools import product
from dataclasses import dataclass
from copy import copy

from pysat.solvers import Glucose3

def index():
    return defaultdict(lambda: [])

@dataclass
class Relation:
    parts: List[str]

    def get_string_encoding(self):
        return " ".join([p.strip() for p in self.parts])


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
    sorts: List[str]

    bindings: Dict[str, str]

    flags: Set[str]

    def get_clauses(self, assignment):
        
        self.rebind(assignment)

        heads = [self.bind_variables(r) for r in self.heads]
        body = [self.bind_variables(r) for r in self.body]

        string_heads = [r.get_string_encoding() for r in heads]
        string_body = [r.get_string_encoding() for r in body]
        if string_heads:
            return [Clause(h, string_body) for h in string_heads]

        else:
            return [Clause("", string_body)]

    def rebind(self, assignment):
        for variable, value in zip(self.variables, assignment):
            self.bindings[variable] = value

    def bind_variables(self, relation):
        return Relation([self.replace(s) for s in relation.parts])

    def replace(self, symbol):
        if symbol in self.bindings:
            return self.bindings[symbol]
        else:
            return symbol


class HornSolver:

    def __init__(self):

        self.sorts = index()
        self.rules = []
        self.literals = set()
        self.clauses = []
        self.value_map = {}
        self.literal_map = {}
        self.reverse_literal_map = {}
        self.solver = Glucose3()
        self.name_counter = 0

    def reset_maps(self):

        self.literal_map = {}
        self.reverse_literal_map = {}
        self.value_map = {}

    def unfold_instance(self):
        
        for rule in self.rules:
            
            for assignment in product(*[self.sorts[s] for s in rule.sorts]):
                
                clauses = rule.get_clauses(assignment)
                
                pure_clauses = [self.evaluate_functions(c) for c in clauses]
                
                self.update_maps(pure_clauses)

                cnf_clauses = self.clausify(pure_clauses)

                for cnf_clause in cnf_clauses:
                    self.solver.add_clause(cnf_clause)

    def is_functional(self, term_string):
        return "." in term_string
        
    def evaluate(self, term_string):
        
        parts = term_string.split(".")
        domain = parts.pop(0)
        image = domain

        while parts:
            image = self.value_map[domain, parts.pop(0)]
            domain = image

        return image

    def evaluate_functions(self, clause):

        function_free_clause = copy(clause)
        function_free_clause.head = self.evaluate(new_clause.head)
        function_free_clause.body = [self.evaluate(atom) for atom in new_clause.body]
            
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

