import parser
import models
from test_parser import sorted_program as program

parts = parser.Parser().parse(program)[1]
rules = []

for p in parts:
    body, head, variables, sorts = p
    rules.append(models.Rule([models.Relation(b) for b in body],
                             [models.Relation(h) for h in head],
                             sorts,
                             [v[0] for v in variables],
                             {},
                             []))

solver = models.HornSolver()
solver.rules = rules
