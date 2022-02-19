# Artale

I use these scripts to embed logic programs limited to the Horn fragment of
many-sorted first order logic into propositional logic (using CNFs), and add
hard-coded auxiliary clauses to manage constraints that are beyond either
first order logic or make limited use of functions relying on the unique
name assumption, so I can use a SAT solver to find models of the theory
described in the program.

- The class in charge of finding models satisfying the specification given in a program is in `models.py` 
- The class in charge of parsing programs is in `parser.py`

### Dependencies
The scripts in this repository depend on [Pyglet](http://pyglet.org) and [PySAT](https://pysathq.github.io/).
Pyglet is fairly portable and should be easy to install on Linux distributions, Windows and MacOS by using pip:

```
pip install pyglet
```

Pyglet is written in pure Python and has no additional dependencies.

PySAT relies on external SAT solvers, and can be installed directly on Ubuntu, but I'm not sure about other operating systems.
Use pip to install it, or check the PySat's homepage to look for additional installation instructions if something fails.

```
pip install python-sat[pblib,aiger]
```
