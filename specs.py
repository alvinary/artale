boulders = '''

-- Boulders test
   Propositional version (there are no entity/object abstractions) --

sort character 4
sort tile 144
sort object 72

sort direction 0
sort direction add up, down, left, right

sort tile.left in tile
sort tile.up in tile
sort tile.right in tile
sort tile.down in tile

-- Characters can move to a free tile --

at (c, t), direction (c.action),
free (t.direction) => at (c.next, t.next)

-- A character that moves in the direction
   of a blocked tile bonks --

at (c, t), direction (c.action),
blocked (t.direction) => at (c.next, t.next), bonk (c.next)

-- Walls and boulders block the way --

wall (t) => blocked (t)
boulder (t) => blocked (t)

-- Tiles cannot be free and blocked --

blocked (t), free (t) => False

-- Walls remain walls --

wall (t) => wall (t.next)

-- Characters can kick boulders in any
   direction, provided the tile behind
   the boulder is not blocked -- 

at (c, t), boulder (t.direction),
direction (c.action), free (t.direction.direction) =>
kicked (t.direction, direction),
free (t.direction.next),
boulder (t.direction.direction.next),
acted on (t.direction),
acted on (t.direction.direction)

-- There is only one exit --

exit (t), t != s => not exit (s)

-- Naive inertia: boulders stay where they are unless kicked --

free (t), not acted on (t) => free (t.next)
boulder (t), not acted on (t) => boulder (t.next)

not kicked (tile, direction),
acted on (tile) => False

not kicked (tile, direction),
acted on (tile.direction) => False

-- A character's action can only be a single
   key press, or none at all --
   
direction a (c.action),
direction b (c.action),
direction a != direction b
=> False

-- You can only kick something in one direction --

kicked (t, direction a),
kicked (t, direction b),
direction a != direction b
=> False

'''

trees = '''

sort node 13

sort type 13

left (n : node, m : node) v not left (n, m)

left (n : node, m : node), not left (n, m) => False

right (n : node, m : node) v not right (n : node, m : node)

right (n : node, m : node), not right (n, m) => False

-- Negation --

next (a : node, b : node) v not next (a : node, b : node)

next (a : node, b : node), not next (a : node, b : node) => False

before (a : node, b : node) v not before (a : node, b : node)

before (a : node, b : node), not before (a : node, b : node) => False

left of (a : node, b : node) v not left of (a : node, b : node)

left of (a : node, b : node), not left of (a : node, b : node) => False

-- Nodes are either leaves or phrases --

leaf (n : node) v phrase (n)

leaf (n : node), phrase (n) => False

-- Leaves do not have children --

leaf (n : node), left (n, m : node) => False

leaf (n : node), right (n, m : node) => False

-- No node is its own child --

left (n : node, n) => False

right (n : node, n) => False

-- A node cannot be a child of two other differet nodes -- 

left (n : node, m : node) => has child (n, m)

right (n : node, m : node) => has child (n, m)

has child (n : node, m : node), has child (o : node, m), n != o => False

-- No node can have two different nodes as left children (or right children)  --

left (n : node, m : node), left (n : node, o : node), m != o => False

right (n : node, m : node), right (n : node, o : node), m != o => False

-- No node can be both a left and right child --

left (n : node, m : node), right (n : node, m : node) => False

phrase (a : node), not left (a, any : node) => False

phrase (a : node), not right (a, any : node) => False

-- Before --

left (n : node, m : node), before (m, n) => False

right (n : node, m : node), before (m, n) => False

-- A node's left child is always its successor (I)  --

phrase (n : node), next (n : node, m : node) => left (n, m)

-- A node's left child is always its successor (II)  --

phrase (n), left (n : node, m : node) => next (n, m)

-- If a left child is a leaf, the right child is its successor --

left (a : node, b : node), leaf (b), right (a, c : node) => next(b, c)

left (a : node, b : node), leaf (b), right (a, c : node), not next(b, c) => False

-- Nodes left of another are always "smaller" --

left of (a : node, b : node) => before (a, b)

left of (a : node, b : node), before (b, a) => False

-- Left childs are left of right childs --

left (a : node, b : node), right (a, c : node) => left of (b, c)

-- "left of" is transitive --

left of (a : node, b : node), left of (b : node, c : node) => left of (a, c)

-- "left of" is antisymmetric --

left of (a : node, b : node), left of (b, a) => False

'''

cfg = '''

sort S 1

sort S.next in S

sort S add void

sort T 10

sort T add start

sort C 26

var s, s1, s2, s3 : S

var A, B, C : T

var char : C

-- Negation --

before (s1, s2) v not before (s1, s2)

before (s1, s2), not before (s1, s2) => False

parses segment (A, s1, s2) v not parses segment (A, s1, s2)

parses segment (A, s1, s2), not parses segment (A, s1, s2) => False

parses terminal (A, c) v not parses terminal (A, c)

parses terminal (A, c), not parses terminal (A, c) => False

productions (A, B, C) v not productions (A, B, C)

productions (A, B, C), not productions (A, B, C) => False

substitute (A, B) v not substitute (A, B)

substitute (A, B), not substitute (A, B) => False

parses (A, s) v not parses (A, s)

parses (A, s), not parses (A, s) => False

-- Two preterminals parse together a string segment if
   they parse contiguous parts --

parses segment (B, s1, s2),
parses segment (C, s2, s3) =>
parse together (B, C, s1, s2)

-- If there is a rule A -> B C, and B and C parse together a segment,
   A parses that segment --

productions (A, B, C), 
parse together (B, C, s1, s2) =>
parses segment (A, s1, s2),
parses on (A, B, C, s1, s2),
parses by prod (A, s1, s2)

-- Parses must make sense --

parses on (A, B, C, s1, s2), not parse together (B, C, s1, s2) => False

parses on (A, B, C, s1, s2), not productions (A, B, C) => False

parses with (A, B, s1, s2), not substitutions (A, B) => False

-- If A -> B, and B parses a string, then A parses it too (This rule is not monotonic) --

substitute (A, B),
parses segment (B, s1, s2) =>
parses segment (A, s1, s2),
parses with (A, B, s1, s2)

-- If a preterminal parses a character, it parses all symbols with that character --

is (s, char), parses terminal (A, char) => parses segment (A, s, s.next)

-- A preterminal cannot parse a string segment consisting of a single character if it does not parse that character --

is (s, char), parses segment (A, s, s.next), not parses terminal (A, char) => False

-- No string symbol "is" two different characters
   (without this condition, you parse more general sequences) --

is (s, c1), is (s, c2), c1 a != c2 => False

-- If a symbol is empty, so is the next (by induction, from there
   on the string is empty) --

empty (s) => empty (s.next)

-- The void string is empty --

empty (void)

-- Strings are ordered sequences --

parses segment (A, s1, s2), before (s2, s1) => False

-- parses --

parses segment (A, s, void) => parses (A, s)

-- ILP --

not parses (start, p : pos) => False

parses (start, n : neg) => False

'''

cfg_induction = '''

sort pos 10

sort neg 10

-- The start symbol must parse all positive examples, and no negative examples --

not parses segment (start, p : pos, void) => False

parses segment (start, n : neg, void) => False

'''

# Exclusions:

'''

left (a, b), terminal (a, A), terminal (b, B) => left terminal (a, B)

right (a, c), terminal (a, A), terminal (c, C) => right terminal (a, C)

terminal (a, A),
left terminal (a, B),
right terminal (a, C),
not productions (A, B, C) => False

parses segment (A, s1, s2),
not parses by sub (A, s1, s2),
not parses by prod (A, s1, s2) => False

parses segment (B, s1, s2), not substitutions (A, B, s1, s2) => not parses by (A, B, s1, s2)
 
parses by sub (A, s1, s2), not parses by (A, any : B, s1, s2) => False


-- parses left on, parses right on, etc --

-- A preterminal A cannot possibly have parsed a string segment
   if it hasn't parsed it by substitution (By some rule A -> B)
   or by productions (by some rule A -> B C)
   
   These rules are awkward, but equivalence is harder to express
   than implication without <=>: TODO, embed <=>
   
   P v Q <=> R v S is
   
   <P,Q> => <R,S>
   <R,S> => <P,Q>
   not P and not Q and <P,Q> => False
   not S and not R and <R,S> => False --

'''
