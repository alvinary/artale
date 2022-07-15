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

trees = '''sort node 13

sort type 13

left (n : node, m : node) v not left (n, m)

left (n : node, m : node), not left (n, m) => False

right (n : node, m : node) v not right (n : node, m : node)

right (n : node, m : node), not right (n, m) => False

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

-- A node's left child is always its successor (I)  --

phrase (n : node), next (n : node, m : node) => left (n, m)

-- Before --

left (n : node, m : node), before (m, n) => False

right (n : node, m : node), before (m, n) => False

-- A node's left child is always its successor (II)  --

left (n : node, m : node) => next (n, m)

-- If a left child is a leaf, the right child is its successor --

left (a : node, b : node), leaf (b), right (a, c : node) => next(b, c)

-- Nodes left of another are always "smaller" --

left of (a : node, b : node), before (b, a) => False

-- Left childs are left of right childs --

left (a : node, b : node), right (a, c : node) => left of (b, c)

-- "left of" is transitive --

left of (a : node, b : node), left of (b : node, c : node) => left of (a, c)

-- "left of" is antisymmetric --

left of (a : node, b : node), left of (b, a) => False

-- Descendent is the transitive closure of has child --

has child (n : node, m : node) => descendent (n, m)

phrase (n: node) => descendent (n, n)

descendent (n : node, m : node), descendent (m, o : node) => descendent (n, o)

descendent (n : node, m : node) v not descendent (n, m)

descendent (n : node, m : node), not descendent (n, m) => False

-- Every phrase node is a descendent of root --

phrase (n), not descendent (node1, n) => False

'''

cfg = '''

sort S 600

sort S.next in S

sort rule 30

sort T 30

sort T add start

sort C

sort C add a, b, c, d, e, f, g, h, i, j, k, l, m,

sort C add n, o, p, q, r, s, t, u, v, x, y, z

parses segment (A : T, s1 : S, s2 : S), empty (s2) => parses (A, s)

parses segment (B : T, s1 : S, s2 : S),
parses segment (C : T, s2, s3 : S),
left in (r : rule, A : T, B),
right in (r, A, C) =>
parses segment (A, s1, s3)

parses symbol (p : T, s : S) =>
parses segment (p, s, s.next)

is (s : S, char : C),
parses terminal (r : rule, A : T, char) =>
parses symbol (A, s)

is (s : S, c1 : C), is (s, c2 : C), c1 a != c2 => False

empty (s : S) => empty (s.next)

'''
