# Artale

I use these scripts to embed logic programs limited to the Horn fragment of
many-sorted first order logic into propositional logic, and add
hard-coded auxiliary clauses to manage constraints that are either beyond
first order logic or make limited use of functions (relying on the unique
name assumption), so I can use a SAT solver to find models that meet the constraints
specified on a program or perform bounded model checking.

- The class in charge of finding models satisfying a specification is in `models.py` 
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

Use pip to install it, or check the PySat homepage to look for additional installation instructions if something fails.

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
define functions without the UNA and/or with several arguments by placing suitable restrictions on a relation using equality as
defined above).
- Disjunctions (which may increase the time required to find a model above polynomial bounds, but
very likely will not affect the time required to solve a problem instance, as model finding relies
on a SAT solver for general propositional formulae, and modern solvers are know to perform well on
"industrial" instances -i.e. SAT instances taken from 'natural' domains in which some underlying
structure makes instances easy, sometimes even despite high values in common complexity
parameters such as treewidth, as surveyed, for instance, in [this other article](https://www.microsoft.com/en-us/research/publication/treewidth-in-industrial-sat-benchmarks/)).

In order to reduce the size of the embeddings, you can distribute constants into several sorts (sets of separate constants, which in
this setting are entirely equivalent to using monadic predicates as guards limiting quantification), so predicate embeddings only
range over constants of a relevant sort.

### Example

This simple program illustrates how modeling a domain of interest works with these scripts:

```
-- There are ten ponies and ten islands --

sort pony 10
sort island 10

-- No pony can be nowhere, and no pony can be somehwere and nowhere simultaneously --

somewhere(p : pony) v nowhere (p)

somewhere(p : pony), nowhere(p) => False

at(p : pony, i : island) => somewhere(p)

nowhere(p : pony), at(p, i: island) => False

nowhere(p : pony) => False

-- No pony can be at two places at the same time --

at(p: pony, i : island), at(p, j : island), i != j => False

-- Ponies who hate each other can't be at the same island --

loathes (p : pony, q : pony),
loathes(q, p), at(p, i : island),
at(q, i) => False

-- Hatred is symmetrical for ponnies --

loathes (p : pony, q : pony) => loathes (q : pony, p : pony)
```

Comments are written between double dashes, and can span as many lines as you like.

They support an embarrasignly small set of characters (just some ASCII
punctuation and ASCII characters - not even ASCII digits!)

Sort declarations have the form `sort <sort name> <number of constants>`, and they
ensure there is a sort with the given name, populated by `number of constants` uniform constans (i.e. mere
names of constants).

You can also define distinguished constants using `sort <sort name> add <some name>, <some other name>, <as many names as you want>`.

All sort declarations must precede all rules.

Rules cannot mix disjunctions and conjunction (they are either Horn rules or disjunctions).
You can use negation and mix literals any way you want, but using Horn rules is more cognitively
ergonomic.

Disjunctions are written as in `somewhere(p : pony) v nowhere (p)`. In order for 
the scripts to interpret a symbol as a variable symbol, it must be given a sort at
least once. You can ommit it elsewhere for brevity (ugly, I know, but less typing).

You assign a sort to a variable using `:`.

Rules can have the habitual Prolog rule shape we all know and love (`p(a: A, b: B), q(a) => r(b)`),
but rules like `p(a: s, b: s) => q(b: s, a: s), r(a)` are allowed as well.

Those are simply shorthand for `p(a: s, b: s) => q(b: s, a: s)` and `p(a: s, b: s) => r(a)`.

Functions are written like fields of a struct / properties of an object: `f(a)` is `a.f` and
`h(g(f(a)))` is `a.f.g.h`. I know, this is ugly too.

Terms using functions must be assigned the sort of their domain. This is because variables
work like really simple macros (just replacing variable names with constants from their sorts).

In order to avoid `somePredicate1` and `isA`, predicates and constants can include spaces.
It is assumed that one can tell a predicate is a predicate because it precedes parentheses,
and arguments are separated by commas. Unnecesary and childishly idiosyncratic but more readable!

So you can perfectly write `building (b: part), has part (b, t : part), on fire (t) => risk of fire (b)`.

### Useful idioms

#### Negation

Negation can be embedded for specific predicates by writing

```
small (a : s) v not small (a : s)
small (a : s), not small (a : s) => False
```

#### Existence

You can simulate some simple kinds of assertions of existence using this cheap trick:

```
has part (b : part, e : part), entrance (e) => has entrance (b)
building (b : part), has entrance . not (b) => False
```

As long as you can turn your condition into an unary predicate, you just have to
rule out models in which constants for which some predicate holds also meet that unary predicate.
