cfg = '''

sort string 600
sort string add emptyString
sort string.next in string

sort rule 30
sort preterminal 30

sort character 128

parses segment (A, s, emptyString) =>
parses (A, s)

parses segment (B, s1, s2),
parses segment (C, s2, s3),
left in (r, A, B),
right in (r, A, C) =>
parses segment (A, s1, s3)

parses symbol (p, s) =>
parses segment (p, s, s.next)

is (s, char),
parses terminal (r, A, char) =>
parses symbol (A, s)

is (s, char a), is (s, char b), char a != char b => False

'''

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

-- A node's left child is always successor (I)  --

phrase (n : node), next (n : node, m : node) => left (n, m)

-- No node is left or right of itself --

left (n : node, n) => False

right (n : node, n) => False

-- No node is either a left or right of another, not both --

left (a : node, b : node), right (a, b) => False

-- Before --

left (n : node, m : node), before (m, n) => False

right (n : node, m : node), before (m, n) => False

-- A node's left child is always successor (II)  --

left (n : node, m : node) => next (n, m)

-- If left child is a leaf, the right child is its successor --

left (a : node, b : node), leaf (b), right (a, c : node) => next(b, c)

-- Nodes left of another are always "smaller" --

left of (a : node, b : node), before (b, a) => False

-- Left childs are left of right childs --

left (a : node, b : node), right (a, c : node) => left of (b, c)

-- "left of" is transitive --

left of (a : node, b : node), left of (b : node, c : node) => left of (a, c)

-- "left of" is antisymmetric --

left of (a : node, b : node), left of (b, a) => False

-- Two different nodes cannot parent the same child -- 

right (a : node, b : node), right (c : node, b), a != c => False

right (a : node, b : node), left (c : node, b), a != c => False

left (a : node, b : node), left (c : node, b), a != c => False

-- The same node cannot parent different childs in the same direction --

right (a : node, b : node), right (a, c : node), b != c => False

left (a : node, b : node), left (a, c : node), b != c => False
'''

'''
phrase (a : node), not left (a, any : node) => False

phrase (a : node), not right (a, any : node) => False
'''
