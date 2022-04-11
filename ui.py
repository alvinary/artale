import pyglet

from constants import *
import ttag

window = pyglet.window.Window(1200, 900)

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

def make_node_edge(x_pos, y_pos, _x_pos, _y_pos):
    return pyglet.shapes.Line(x_pos, y_pos, _x_pos, _y_pos, width=1, batch=edge_batch, color=(255,255,255))


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

        self.edge = None

        if not (self.parent is None):
            self.edge = make_node_edge(self.x, self.y, self.parent.x, self.parent.y)


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
                min_node_x = min([c.count_left() for c in n.children]) * NODE_WIDTH
                max_node_x = max([c.count_left() for c in n.children]) * NODE_WIDTH
                n.x = min_node_x + (max_node_x - min_node_x) // 2
                n.y = n.depth() * NODE_HEIGHT

    def update_edges(self):
        for n in self.collect():
            if not (n.parent is None) and n.edge is None:
                n.edge = make_node_edge(n.x, n.y, n.parent.x, n.parent.y)

    def update_graphics(self):
        self.update_node_positions()
        self.update_edge_positions()

    def update_node_positions(self):
        self.vertex_box.x = self.x * 5
        self.vertex_box.y = TREE_BOX_Y - self.y * 5
        self.label.x = self.x * 5
        self.label.y = TREE_BOX_Y - self.y * 5
    
    def update_edge_positions(self):
        for n in self.collect():
            if not (n.edge is None):
                n.edge.x = n.x * 5 + n.vertex_box.width // 2
                n.edge.y = TREE_BOX_Y - n.y * 5 + n.vertex_box.height // 2
                n.edge.x2 = n.parent.x * 5 + n.vertex_box.width // 2
                n.edge.y2 = TREE_BOX_Y - n.parent.y * 5 + n.vertex_box.height // 2

    def draw(self):
        self.arrange()
        all_nodes = self.root().collect()
        for n in all_nodes:
            n.update_graphics()

    def destroy(self):
        if self.edge:
            del self.edge
        del self.label
        del self.vertex_box
        del self

@window.event()
def on_draw():
    window.clear()
    edge_batch.draw()
    node_box_batch.draw()
    node_batch.draw()

def read_tree(tree_predicates, prefix):

    names = {}
    nodes = set()
    relations = set()

    counter = 0

    for _tree_predicate in tree_predicates:
        if len(_tree_predicate) > 4:
            predicate, term = _tree_predicate.split(" ")
            if "blank" not in predicate:
                nodes.add(term)

    for n in nodes:
        counter += 1
        names[n] = prefix + str(counter)

    for node in nodes:
        chunked_node = node.split(".")
        if len(chunked_node) > 1:
            chunk = chunked_node.pop(-1)
            chunked_node = ".".join(chunked_node)
            relations.add((chunk, names[chunked_node], names[node]))

    node_names = [names[k] for k in names]

    return node_names, relations

def read_relations(relation):
    
    nodes = set()

    print("before:")
    for i in relation:
        print(i)

    print("after:")

    relation = {t for t in relation if len(t) == 3}

    for r in relation:
        print(r)
    
    for r in relation:
        for l in r[1:]:
            nodes.add(l)

    return nodes, relation


class TreeViewer:

    def __init__(self):

        self.index = 900
        self.nodes_map = {}
        self.tree = []

        self.right_facts = ttag.right_facts

        self.tree_nodes, self.tree_relations = [], {}
        
        self.update_tree_view()

        self.model_length = len(self.right_facts)

    def on_key_press(self, symbol, modifiers):

        satisfiability_check = False

        if symbol == pyglet.window.key.RIGHT:
            index_shift = 1
            self.index += 1
            self.index = self.index % self.model_length + 1
                
        if symbol == pyglet.window.key.LEFT:
            index_shift = -1
            self.index -= 1
            self.index = self.index % self.model_length + 1

        for k in list(self.nodes_map.keys()):
            self.nodes_map[k].destroy()

        print(self.index)

        fact_literal = ttag.solver.literal_map[self.right_facts[self.index]]
        satisfiability_check = ttag.solver.solver.solve([fact_literal])

        while not satisfiability_check:
            self.index = (self.index + index_shift) % self.model_length + 1
            fact_literal = ttag.solver.literal_map[self.right_facts[self.index]]
            satisfiability_check = ttag.solver.solver.solve([fact_literal])
            print(f"index: {self.index}")

        model = ttag.solver.solver.get_model()

        if self.model_length == 1:
            self.model_length = max([abs(atlit) for atlit in model])
            print(f"Updated model length: {self.model_length}")

        model_as_set = ttag.solver.get_relations(model, ["left", "right"])

        print("\n".join([" ".join(t) for t in model_as_set]), "\n")

        self.tree_nodes, self.tree_relations = read_relations(model_as_set)
        self.nodes_map = {}

        self.update_tree_view()

    def update_tree_view(self):
    
        global node_batch
    
        node_batch = pyglet.graphics.Batch()

        for n in self.tree_nodes:
            self.nodes_map[n] = Node(n)

        self.tree = {self.nodes_map[k].root().text for k in self.nodes_map}
        self.tree = [self.nodes_map[k] for k in self.tree]

        for triple in self.tree_relations:
            r, a, b = triple
            self.nodes_map[b].parent = self.nodes_map[a]
            self.nodes_map[b].tags = {r}
            self.nodes_map[a].children.append(self.nodes_map[b])

        self.tree = {self.nodes_map[k].root().text for k in self.nodes_map}
        self.tree = [self.nodes_map[k] for k in self.tree]

        for t in self.tree:
            t.update_edges()
            t.draw()
            window.clear()
            edge_batch.draw()
            node_box_batch.draw()
            node_batch.draw()

viewer = TreeViewer()
window.push_handlers(viewer)

pyglet.app.run()
