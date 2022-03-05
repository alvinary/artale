SCROLL_SCALING = 40
TILE_SIDE = 48
SCROLLABLE_PANEL_TOP = 400
TAG_SEPARATOR = 8
TAG_HEIGHT = 16

TILE_SIZE = 16
SCALING_FACTOR = 2

WINDOW_WIDTH = 1520
WINDOW_HEIGHT = 980

MAP_REGION_X = 10
MAP_REGION_Y = 10

EDITOR_X = 900
EDITOR_Y = 900

EDITOR_WIDTH = 540
EDITOR_HEIGHT = 900

PADDING = 80

NODE_WIDTH = 15
NODE_HEIGHT = 10
TREE_BOX_X = 300
TREE_BOX_Y = 800
CHAR_WIDTH = 10
CHAR_HEIGHT = 14
NODE_MARGIN = 5

TEMPLATE = '''
-- Press click anywhere to switch to and from the program editor to the map tagger --

-- All map components are either leaves or nodes (preterminals) --

leaf(c : component) v node(c : component),
leaf(c : component), node(c : component) => 
False

-- No tile is assigned to a preterminal --

node(c: component), assign(t: tile, c) => False

-- No map component (in particular, no leaf) is assigned two different tiles --

assign(t: tile, c: component), matches(s: tile, c), t != s => False

-- No tile is assigned to two different map components --

assign(t: tile, c: component), assign(t, d: component), d != c => False

-- Map components are either 'virtual' components (used to keep trees binary),
   or 'actual' components. All leaves are 'actual' components --

leaf(c: component), virtual(c) => False

virtual(c : component) v actual(c : component)

-- Virtual components are 'reigned' by the first actual node 'above' them
   ('the first node above' being 'the first actual node found by following
   branches/edges upwards') -- 

actual(c : component), virtual(c.left) => regent(c, c.left)

actual(c : component), virtual(c.right) => regent(c, c.right)

virtual(c : component), virtual(c.left), regent(d: component, c) => regent(d, c.left)

virtual(c : component), virtual(c.right), regent(d: component, c) => regent(d, c.right)

-- Virtual components inherit all their relations to
   their parent components, so that the first actual
   node dominating n virtual nodes gets all their
   relations and 'receives' the properties it should --

rel : relation (c.left : component, d : component), virtual(c.left) => rel(c, d)

rel : relation (c.right : component, d : component), virtual(c.right) => rel(c, d)

-- Constraints apply to real nodes only! --
-- (Or should there be actual and real relations? neh, actual and real nodes) --

-- The way there rules were stated, nothing prevents a map
   from having a property without meeting any of its requirements --
'''
