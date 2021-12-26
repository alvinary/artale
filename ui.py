import pyglet

NODE_WIDTH = 30
NODE_HEIGHT = 20

window = pyglet.window.Window(700, 700)

edge_batch = pyglet.graphics.Batch()
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

def make_node_label(node):
    return pyglet.text.Label(node.text,
                             font_name="Arial",
                             font_size=14,
                             x=node.x,
                             y=node.y)

class Node:
    
    def __init__(self, text, children=[], parent=None):
        
        self.text = text
        
        self.children = children # these children are not labeled!
        self.parent = parent
        
        self.x = 0
        self.y = 0

        self.label = make_node_label(self)
        self.vertex_sprite = None
        self.edge_sprites = []

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
        if self.parent is None:
            return 0
        else:
            on_left = []
            for i in self.parent.children:
                if i == self:
                    break
                on_left.append(i)

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

    def draw(self):
        all_nodes = self.root().collect()
        for n in all_nodes:
            if not n.is_leaf():
                end_x, end_y
                tip_x, tip_y


