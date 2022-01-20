from collections import defaultdict
from typing import List, Dict, Set
from itertools import product
from dataclasses import dataclass
from copy import copy

from pysat.solvers import Glucose3

TERM_SEPARATOR = "--"

def index():
    return defaultdict(lambda: [])

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

    bindings: Dict[str, str]

    flags: Set[str]

    def get_clauses(self, assignment):
        
        self.rebind(assignment)

        heads = [self.bind_variables(r) for r in self.heads]
        body = [self.bind_variables(r) for r in self.body]

        print(heads)
        print(body)

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
        if "." not in symbol:
            if symbol in self.bindings:
                return self.bindings[symbol]
            else:
                print(f"symbol {symbol} not in {self.bindings.keys()}")
                return symbol
        if "." in symbol:
            symbol_parts = [p.strip() for p in symbol.split(".")]
            return ".".join([self.replace(s) for s in symbol_parts])


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

            print(rule.body)
            print(rule.sorts)
            
            for assignment in product(*[self.sorts[s] for s in rule.sorts]):
                
                print(assignment)

                clauses = rule.get_clauses(assignment)
                
                for c in clauses:
                    print("clause:")
                    print(f"   head: {c.head}")
                    print(f"   body: {', '.join([b for b in c.body])}")

                pure_clauses = [self.evaluate_functions(c) for c in clauses]
                
                self.update_maps(pure_clauses)

                cnf_clauses = [self.dimacs(c) for c in pure_clauses]

                for cnf_clause in cnf_clauses:
                    self.solver.add_clause(cnf_clause)

    def is_functional(self, term_string):
        return "." in term_string

    def dimacs(self, pure_clause):

        dimacs_clause = []

        if pure_clause.head != "":
            dimacs_clause.append(self.literal_map[pure_clause.head])

        for atom in pure_clause.body:
            dimacs_clause.append(-self.literal_map[atom])

        return dimacs_clause
        
        
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
        function_free_clause.body = [self.evaluate(atom) for atom in function_free_clause.body]
            
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

