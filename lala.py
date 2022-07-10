from sparse import *
from models import HornSolver

def meep(jeje):

    solvery = HornSolver()
    
    rulytexto = read_rule(normalize(jeje))
    rulo = make_rule(rulytexto, solvery)

    print(rulo)
    
    
meep("p (a : sort a, b : sort b), q (b) => r (a)")
meep("pepa (char : character), pig (char) => pepa pig (char)") # This time just once
meep("holy (t : thing) v neutral (t) v unholy (t)")
meep("unholy (brad the unholy)")
