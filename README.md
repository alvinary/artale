# Artale

I use these scripts to embed logic programs limited to the Horn fragment of
many-sorted first order logic into propositional logic, and add
hard-coded auxiliary clauses to manage constraints that are either beyond
first order logic or make limited use of functions (relying on the unique
name assumption), so I can use a SAT solver for model checking.

- The class in charge of finding models satisfying the specification given in a program is in `models.py` 
- The class in charge of parsing programs is in `parser.py`
- A class for displaying relations as trees can be found in `ui.py`
- The `./specs` folder contains some example programs
- The `grammar` file specifies the grammar of the input language

### Dependencies
The scripts in this repository depend on [Pyglet](http://pyglet.org), [Lark](https://github.com/lark-parser/lark)
and [PySAT](https://pysathq.github.io/). 

Pyglet and Lark are fairly portable and should be easy to install on most Linux distributions, Windows and MacOS by using pip.

```
pip install pyglet
pip install lark
```

PySAT relies on external SAT solvers, and can be installed directly on Ubuntu, but I'm not sure about other distributions
and operating systems.

Use pip to install it, or check the PySat's homepage to look for additional installation instructions if something fails.

```
pip install python-sat[pblib,aiger]
```

### Language

These scripts implement something similar to the embedding of Horn DL-Lite described in [this paper](https://arxiv.org/abs/1401.3487).

You can specify theories and constraints with:

- Horn rules (not limited to single-argument predicates, as in the paper linked above).
- Statements involving equality and inequality (relying on the unique name assumption, i.e. assuming syntactic equality
between constants is semantic equality). Note "full fledged" equality can be emulated (incurring in a polynomial
increase in time and space complexity) simply by defining a suitable equivalence relation, and
stating every property that holds for a member of an equivalence class holds for the rest.
- Single-argument functions (these rely on the unique name assumption as well, but it is possible to
define functions with several arguments by placing suitable restrictions on a relation using equality as
defined above).
- Disjunctions (which may increase the time required to find a model above polynomial bounds, but
very likely will not affect the time required to solve a problem instance, as model finding relies
on a SAT solver for general propositional formulae, and modern solvers are know to perform well on
"industrial" instances -i.e. SAT instances taken from 'natural' domains in which some underlying
structure makes instances easy, sometimes even despite high values in common complexity
parameters such as treewidth, as surveyed, for instance, in ).

In order to reduce the size of the embeddings, you can distribute constants into several sorts (sets of separate constants, which in
this setting are entirely equivalent to using monadic predicates as guards limiting quantification), so predicate embeddings only
range over constants of a relevant sort.

