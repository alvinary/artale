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

NO_WORD = "(...)"
TYPE_WARNING = "NO TYPE"

TEMPLATE = '''
sort component 40
sort tile 60

leaf(c : component), node(c : component) => False

leaf(c : component) v node(c : component)

node(c: component), assign(t: tile, c) => False

assign(t: tile, c: component), matches(s: tile, c), t != s => False

assign(t: tile, c: component), assign(t, d: component), d != c => False

leaf(c: component), virtual(c) => False

virtual(c : component) v actual(c : component)

actual(c : component), virtual(c.left) => regent(c, c.left)

actual(c : component), virtual(c.right) => regent(c, c.right)

virtual(c : component), virtual(c.left), regent(d: component, c) => regent(d, c.left)

virtual(c : component), virtual(c.right), regent(d: component, c) => regent(d, c.right)

rel: relation (c.left : component, d : component), virtual(c.left) => rel(c, d)

rel: relation (c.right : component, d : component), virtual(c.right) => rel(c, d)
'''
