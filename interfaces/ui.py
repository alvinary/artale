import pyglet

from artale.taggers.trees import solver
from artale.constants import *


facts = [f for f in solver.literal_map.keys()]
for f in facts:
    print(f)

right_facts = [f for f in solver.literal_map.keys() if "right" in f]

window = pyglet.window.Window(1200, 900)

edge_batch = pyglet.graphics.Batch()
node_box_batch = pyglet.graphics.Batch()
node_batch = pyglet.graphics.Batch()

def read_type(constant_name, model):

    hash_model = set(model)

    # Obtain all parts of the type

    type_members = set()
    type_members.add(constant_name)
    
    remaining_elements = True

    while remaining_elements:

        new = set()

        for t in type_members:
            if (t, "input") in solver.value_map:
                new.add(solver.value_map[t, "input"])
            if (t, "output") in solver.value_map:
                new.add(solver.value_map[t, "output"])

        if not (new - type_members):
            remaining_elements = False

        type_members |= new

    type_members.discard("blanktype")

    # Put in a map the category of each leaf (N or S),
    # and put in another map the input and output child
    # of the 'node' parts
    # (Blank parts are left out properly, since nor
    #  the leaf predicate nor the nodetype predicate should
    # hold for them)
            
    leaf_categories = {}
    node_children = {}

    for t in type_members:

        leaf_fact = f"leaftype {t}"
        sent_fact = f"sentential {t}"
        nomi_fact = f"nominal {t}"
        node_fact = f"nodetype {t}"

        l_atom = solver.literal_map[leaf_fact]
        n_atom = solver.literal_map[node_fact]
        is_leaf = l_atom in hash_model
        is_node = n_atom in hash_model

        if is_leaf:
            s_atom = solver.literal_map[sent_fact]
            n_atom = solver.literal_map[nomi_fact]
            if s_atom in hash_model:
                leaf_categories[t] = "s"
            if n_atom in hash_model:
                leaf_categories[t] = "n"

        elif is_node:
            node_children[t, "input"] = f"{t}.input"
            node_children[t, "output"] = f"{t}.output"
        
    return get_type(constant_name, leaf_categories, node_children)

def get_type(root_name, leaf_map, node_map):

    if root_name in leaf_map:

        return leaf_map[root_name].upper()

    if (root_name, "input") in node_map:
        left = f"{root_name}.input"
        right = f"{root_name}.output"

        input_type = get_type(left, leaf_map, node_map)
        output_type = get_type(right, leaf_map, node_map)

        return f"({input_type} -> {output_type})"

    else:
        print("Node: ", root_name)
        print(f"Leaf properties of {root_name}:", leaf_map)
        print("Node data: ", node_map)
        return TYPE_WARNING

def read_word(constant_name, lexicon, model):
    '''
    
    Return the word w if w's predicate holds for the input constant.
    If there is no such word, return NO_WORD.
    
    '''
    
    hash_model = set(model)
    
    for item in lexicon:
    
        word_fact = f"{item} {constant_name}"
    
        if word_fact in solver.literal_map:
    
            atom = solver.literal_map[word_fact]
    
            if atom in hash_model:
                print("Word:", item)
                return item
    
    return NO_WORD

def tree_from_relations(predicates, relation_order):
    '''
    
    Given a set of unary and binary predicates, and an ordering
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

    '''
    
    Given a 'text' string and two integers (x_pos and y_pos), return
    a pyglet text label whose text is 'text', placed at (x_pos, y_pos) 2d
    coordinates.
    
    '''

    return pyglet.text.Label(text,
                             font_name="Arial",
                             font_size=14,
                             x=x_pos,
                             y=y_pos,
                             batch=node_batch)


def make_node_box(text, x_pos, y_pos):

    return pyglet.shapes.Rectangle(x_pos, y_pos, 20,
                            20, color=(230, 55, 48),
                            batch=node_box_batch)

def make_node_edge(x_pos, y_pos, _x_pos, _y_pos):

    return pyglet.shapes.Line(x_pos, y_pos,
                              _x_pos, _y_pos,
                              width=1, batch=edge_batch,
                              color=(255,255,255))


class Node:
    
    def __init__(self, text, type_description,
                 word="", children=[], tags=set(),
                 show_order=True, show_type=True,
                 show_word=True, parent=None,
                 x=0, y=0):
        
        self.text = text
        self.type_description = type_description
        self.word = word
        print(f"Node word for {self.text}: {self.word}")
        
        self.children = list(children) # these children are not labeled!
        self.parent = parent
        self.tags = set(tags)
        
        self.x = int(x)
        self.y = int(y)

        label_text = ""

        if self.word != "":
            self.show_word = True

        if show_order:
            label_text = self.text + ' '
        if show_word:
            label_text = label_text + self.word + '\n'
        if show_type:
            label_text = label_text + self.type_description

        self.label = make_node_label(label_text, self.x, self.y)
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
        
        '''
        
        Count the number of leaves, split a bounding box evenly,
        place each leaf at its depth, and width "count left"
        
        '''
        
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
    
    check = lambda x: x[1] != "of" and x[1] != "headed"
    # TODO: properly extend this function so that relations are taken
    # from a set of target relations (for instance, "left" and "right")
    # and excluded from a set of other relations ("left of", "right headed")

    relation = {t for t in relation if len(t) == 3}
    
    for r in relation:
        for l in r[1:]:
            nodes.add(l)

    return nodes, relation


class TreeViewer:

    def __init__(self):

        self.lexicon = []

        self.index = 0
        self.nodes_map = {}
        self.tree = []

        self.right_literals = [solver.literal_map[fact] for fact in right_facts]
        self.model_length = len(self.right_literals)

        self.tree_nodes, self.tree_relations = [], {}
        
        self.update_tree_view([])

    def on_key_press(self, symbol, modifiers):

        satisfiability_check = False

        if symbol == pyglet.window.key.RIGHT:
            index_shift = 1
            self.index += 1
            self.index = self.index % self.model_length
                
        if symbol == pyglet.window.key.LEFT:
            index_shift = -1
            self.index -= 1
            self.index = self.index % self.model_length

        for k in list(self.nodes_map.keys()):
            self.nodes_map[k].destroy()

        print("Current model index: ", self.index)

        fact_literal = self.right_literals[self.index]
        satisfiability_check = solver.solver.solve([fact_literal])
        found_a_model = False

        while not satisfiability_check:

            absolute_index = self.index + index_shift

            self.index = (self.index + index_shift) % self.model_length
            fact_literal = self.right_literals[self.index]

            print(f"Skipping to index {self.index}...")

            satisfiability_check = solver.solver.solve([fact_literal])
            found_a_model = found_a_model or satisfiability_check

            looped_all_the_way = absolute_index >= self.model_length

            if not found_a_model and looped_all_the_way:
                print("The specification in this program is unsatisfiable!")
                break

        if satisfiability_check:

            model = solver.solver.get_model()

            model_as_set = solver.get_relations(model, ["left", "right"])

            self.tree_nodes, self.tree_relations = read_relations(model_as_set)
            self.nodes_map = {}

            self.update_tree_view(model)

    def update_tree_view(self, model):
    
        global node_batch
    
        node_batch = pyglet.graphics.Batch()

        for node in self.tree_nodes:

            type_node = f"{node}.type"
            type_description = read_type(type_node, model)
            node_word = read_word(node, self.lexicon, model)

            solver.show_model(model)
            
            if node_word == NO_WORD:
                ui_node = Node(node, type_description)
            if node_word != NO_WORD:
                ui_node = Node(node, type_description, word=node_word)

            self.nodes_map[node] = ui_node

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
viewer.lexicon = LEXICON
window.push_handlers(viewer)

pyglet.app.run()
