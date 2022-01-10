import models
from lark import Lark

grammar = ""

with open("grammar") as grammar_file:
    for line in grammar_file:
        grammar = grammar + line

class Parser:

    def __init__(self):

        self.parser = Lark(grammar)

    def preprocess(self, program):

        program = program.replace("=>", " => ")
        program = program.replace(",", ", ")

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

    def get_solver(self, program):

        return "Je"
        
