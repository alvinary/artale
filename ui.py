import pyglet

NODE_WIDTH = 30
NODE_HEIGHT = 20
TREE_BOX_X = 300
TREE_BOX_Y = 600
CHAR_WIDTH = 10
CHAR_HEIGHT = 14
NODE_MARGIN = 5

window = pyglet.window.Window(700, 700)

edge_batch = pyglet.graphics.Batch()
node_box_batch = pyglet.graphics.Batch()
node_batch = pyglet.graphics.Batch()

def tree_from_relations(predicates, relation_order):
    '''Given a set of unary and binary predicates, and an ordering
    between relations, return a tree representation of that relation,
    or norify the relation supplied is not a tree.

    For instance, the set {(p, a), (r, a, b), (l, a, c), (q, b), (q', c)} should
    map to the tree shown below.

     a[p]
     /  \
  b[q]  c[q']

    '''
    nodes = []
    node_names = {t[1] for t in predicates}
    node_names = node_names | {t[2] for t in predicates if 2 <= len(t)}
    node_index = {}
    return nodes

def make_node_label(text, x_pos, y_pos):
    '''Given a 'text' string and two integers (x_pos and y_pos), return
    a pyglet text label whose text is 'text', placed at (x_pos, y_pos) 2d
    coordinates.'''
    return pyglet.text.Label(text,
                             font_name="Arial",
                             font_size=14,
                             x=x_pos,
                             y=y_pos,
                             batch=node_batch)


def make_node_box(text, x_pos, y_pos):
    return pyglet.shapes.Rectangle(x_pos, y_pos, 20,
                            20, 
                            color=(230, 55, 48), batch=node_box_batch)


class Node:
    
    def __init__(self, text, children=[], tags=set(), parent=None, x=0, y=0):
        
        self.text = text
        
        self.children = list(children) # these children are not labeled!
        self.parent = parent
        self.tags = set(tags)
        
        self.x = int(x)
        self.y = int(y)

        self.label = make_node_label(self.text, self.x, self.y)
        self.vertex_box = make_node_box(self.text, self.x, self.y)
        self.edge_lines = []

    def depth(self):
        '''Return the distance from self to the root of the tree'''
        if self.parent is None:
            return 0
        else:
            return 1 + self.parent.depth()

    def spawn_child(self, text):
        spawn = Node(text)
        self.add_child(spawn)

    def add_child(self, node):
        self.children.append(node)
        node.parent = self

    def root(self):
        candidate, roof = self, self.parent
        while not (roof is None):
            candidate, roof = self.parent, roof.parent
        return candidate

    def count_leaves(self):
        if self.children:
            return sum([c.count_leaves() for c in self.children])
        else:
            return 1

    def count_left(self):
        # While parent is not None... (collect left of parent)
        if self.parent is None:
            return 0
        else:
            upper = self.parent
            block = self
            on_left = []
            while not (upper is None):
                for i in upper.children:
                    if i == block:
                        break
                    on_left.append(i)
                block = upper
                upper = block.parent

            return sum([l.count_leaves() for l in on_left])

    def is_leaf(self):
        return not self.children

    def collect(self):
        if not self.children:
            return [self]
        
        child_leaves = [c.collect() for c in self.children]
        return [self] + [leaf for leaves in child_leaves for leaf in leaves]

    def arrange(self):
        '''Count the number of leaves, split a bounding box evenly,
        place each leaf at its depth, and width "count left" '''
        all_nodes = self.root().collect()
        for n in all_nodes:
            if n.is_leaf():
                n.x = n.count_left() * NODE_WIDTH
                n.y = n.depth() * NODE_HEIGHT
            else:
                #AHHHH AMOOO
                min_node_x = min([c.count_left() for c in n.children]) * NODE_WIDTH
                max_node_x = max([c.count_left() for c in n.children]) * NODE_WIDTH
                n.x = min_node_x + (max_node_x - min_node_x) // 2
                n.y = n.depth() * NODE_HEIGHT

    def update_graphics(self):
        self.vertex_box.x = self.x * 5
        self.vertex_box.y = TREE_BOX_Y - self.y * 5
        self.label.x = self.x * 5
        self.label.y = TREE_BOX_Y - self.y * 5

    def draw(self):
        self.arrange()
        all_nodes = self.root().collect()
        for n in all_nodes:
            n.update_graphics()

@window.event()
def on_draw():
    window.clear()
    node_box_batch.draw()
    node_batch.draw()

filberto = Node("F")
gerberto = Node("G")
delberto = Node("D")
bilberto = Node("B")
omengo = Node("O")

filberto.add_child(gerberto)
filberto.add_child(delberto)
delberto.add_child(bilberto)
delberto.add_child(omengo)

filberto.draw()

pyglet.app.run()
