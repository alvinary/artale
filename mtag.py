from collections import defaultdict
from math import log

from models import HornSolver, Rule, Relation
from parser import Parser
from scaffoldings import tree
from constants import *

import pyglet
from pyglet.gl import glTexParameteri, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_NEAREST
from pyglet.window.key import PARENLEFT, PARENRIGHT, COLON, LESS, EQUAL, GREATER, PERIOD, COMMA

special_keys = {
    PARENLEFT : "(",
    PARENRIGHT : ")",
    COLON : ":",
    LESS : "<",
    EQUAL : "=",
    GREATER : ">",
    PERIOD : ".",
    COMMA : ","
}

sample = '''
sort component 40
sort tile 60

-- Map components are either leaves or nodes --

leaf(c : component), node(c : component) => False

leaf(c : component) v node(c : component)

-- Only leaves can be assigned tiles --

node(c: component), assign(t: tile, c) => False

-- Leaves cannot be virtual components --

leaf(c: component), virtual(c) => False

-- Map components are either virtual or actual --

virtual(c : component) v actual(c : component)

-- Virtual nodes inherit all their properties to their
   parents (so that the first actual node above any number
   of virtual nodes gets all their properties) --

prop : property (c.l : component), virtual(c.l) => prop(c)

prop : property (c.r : component), virtual(c.r) => prop(c)

-- Same goes for relations --

rel: relation (c.l : component, d : component), virtual(c.l) => rel(c, d)

rel: relation (c.r : component, d : component), virtual(c.r) => rel(c, d)

-- Components obey the following rules -- 

'''

letters = [
    l.upper()
    for l in "a b c d e f g h i j k l m n o p q r s t u v w x y z = > < ( ) . : ,".split()
]


def as_ascii(s):
    if s in special_keys.keys():
        return special_keys[s]
    return pyglet.window.key.symbol_string(s)

# Define two separate batches (one for the map region, one 
# for the rest of UI elements)
ui_batch = pyglet.graphics.Batch()
map_batch = pyglet.graphics.Batch()

window = pyglet.window.Window(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)

class MapTagger:

    def __init__(self, tileset="./images/tileset.png", tilespec="./specs/atlas_reference"):

        # tags[tag] should hold all elements tagged as 'tag'

        self.tags = defaultdict(lambda: set())

        # Self.atlas[x, y] should yield a

        self.atlas = pyglet.image.load(tileset)

        # Self.tile_map[tile_name] should yield the tile's (x, y) position in a grid
        # with cells of side TILE_SIZE

        self.tile_map = {}

        # Tile names for each (x, y) coordinate

        self.current_map = {}

        # Self.map_sprites

        self.map_sprites = {}
        
        self.tile_sprites = {}

        # Variables for storing map grid data

        self.map_width = 0
        self.map_height = 0

        self.update_atlas_reference(tilespec)
        self.set_up()
        
        self.theory = ""
        
        self.solver = HornSolver()
        
        self.program = sample

        self.editor = ProgramEditor(self, sample)
        
        self.on_editor = False
        
        self.models = []
        
        self.model_index = 0
        
        window.push_handlers(self.editor)
        window.push_handlers(self)

    def on_key_press(self, symbol, modifiers):
        
        if symbol == pyglet.window.key.LEFT and not self.on_editor:
            self.model_index -= 1
            self.model_index = max(0, self.model_index)
            if self.models:
                self.solver.show_model(self.models[self.model_index])
                
        elif symbol == pyglet.window.key.RIGHT and not self.on_editor:
            self.model_index += 1
            self.model_index = min(len(self.models), self.model_index)
            print(self.model_index)
            self.solver.show_model(self.models[self.model_index])

        elif symbol == pyglet.window.key.ENTER and self.on_editor:
            if self.models == []:
                self.update_models()
    
    def update_atlas_reference(self, specs_path):
        '''Open the text file at specs_path (each line should consist of
           two integers separated by exactly one space, and a space followed
           by an arbitrary string, i.e. "{x} {y} {name}", as in "12 15 grass"
           or "0 0 default blank tile 1"), and set the atlas coordinates of
           tile <name> to be <(x, y)> using the dictionary in self.tile_map.'''
        
        with open(specs_path, "r") as specs:

            for line in specs:

                line_parts = line.split(" ")

                x, y = line_parts[:2]
                name = " ".join(line_parts[2:]).strip()

                print(f"{x}, {y}, {name}")

                self.tile_map[name] = (int(x), int(y))

    def set_up(self):

        self.map_width = self.atlas.width // TILE_SIZE
        self.map_height = self.atlas.height // TILE_SIZE

        for x in range(self.map_width):

            for y in range(self.map_height):

                sprite_x = x * TILE_SIZE + MAP_REGION_X
                sprite_y = y * TILE_SIZE + MAP_REGION_Y

                self.tile_sprites[x, y] = pyglet.sprite.Sprite(self.blank_tile(), sprite_x, sprite_y, batch=map_batch)

    def blank_tile(self):
        return self.atlas.get_region(0, 0, TILE_SIZE, TILE_SIZE)

    def tile_at(self, x, y, flipped=True):
        ''' Return the tile in the cell at <x, y> as a pyglet.image.ImageGrid texture region.'''
        # maybe do height - x, if y indexing is from the bottom to the top
        
        if flipped:
            y = self.map_height - y
        
        # Convert one-based indexing to zero-based indexing
        x = x - 1
        
        return self.atlas.get_region(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def draw_map(self, flipped=True):

        for x in range(self.map_width):

            for y in range(self.map_height):

                if (x, y) in self.current_map:

                    tile_name = self.current_map[x, y]
                    atlas_x, atlas_y = self.tile_map[tile_name]

                    self.tile_sprites[x, y].image = self.tile_at(atlas_x, atlas_y)

    def read_map(self, map_description):
        # TODO: filter non-map relations and predicates
        for r in map_description:
            x, y, cat = r
            self.current_map[x, y] = cat
            
    def update_models(self):

        self.program = self.program.replace("", "\n")
    
        self.models = []
        
        rules = []
        
        sorts_part, rules_part = Parser().parse(self.program)

        for rule in rules_part:

            body, head, variables, sorts, flags = rule

            models_module_rule = Rule([Relation([term for term in atom]) for atom in head],
                                      [Relation([term for term in atom]) for atom in body],
                                      [s for v, s in variables], [v for v, s in variables], {}, flags)

            rules.append(models_module_rule)

        self.solver = HornSolver()
        self.solver.rules = rules
        
        self.unfold_trees(10, 10)
        self.solver.unfold_instance()

        distinct_atoms = {atom for atom in self.solver.literal_map.keys()}

        self.solver.una_equality()

        for m in range(1, 101):
            res = self.solver.solver.solve([m])
            if res:
                self.models.append(self.solver.solver.get_model())
                
        print(len(self.models))

    def unfold_trees(self, width, height):

        tree_depth = int(log(width * height, 2)) + 1

        tree_constants, tree_relation = tree("component", ["l", "r"], tree_depth)

        for c in tree_constants:
            self.solver.sorts["component"].append(c)

        checked = set()

        for r in tree_relation:
            f, a, b = r
            self.solver.value_map[a, f] = b
            checked.add(a)

        for e in tree_constants - checked:
            self.solver.value_map[e, "l"] = "null"
            self.solver.value_map[e, "r"] = "null"

        self.solver.value_map["null", "l"] = "null"
        self.solver.value_map["null", "r"] = "null"

        self.solver.sorts["component"].append("null")

        self.solver.sorts["tile"] = [f"tile<{i},{j}>)" for i in range(width) for j in range(height)]

    def model_atoms():
        atoms = set()
        if self.models:
            for a in self.models[self.model_index]:
                if a > 0 and a in self.solver.reverse_literal_map:
                    atoms.add(self.solver.reverse_literal_map[a])
        return atoms
        
    def on_mouse_press(self, x, y, button, modifiers):

        if button == pyglet.window.mouse.LEFT and x >= self.editor.layout.x: # TODO: declunkify
            self.on_editor = not self.on_editor # TODO: change to something better


class ProgramEditor:

    def __init__(self, tagger, text):
        self.tagger = tagger
        self.text = text
        self.x = EDITOR_X
        self.y = EDITOR_Y
        self.index = max(0, len(self.text))
        
        self.document = pyglet.text.document.UnformattedDocument(self.text)
        self.document.set_style(0, len(self.document.text),
            dict(color=(255, 255, 255, 255), font_name="Go Mono", font_size=14)
        )
        
        self.layout = pyglet.text.layout.ScrollableTextLayout(
            self.document, EDITOR_WIDTH, EDITOR_HEIGHT, multiline=True, batch=ui_batch
        )
        
        self.layout.x = WINDOW_WIDTH - (EDITOR_WIDTH + PADDING)
        self.layout.y = WINDOW_HEIGHT - (EDITOR_HEIGHT + PADDING // 2)
                                            
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.tagger.on_editor:
            self.layout.view_y += int(scroll_y * SCROLL_SCALING)

    def on_key_press(self, symbol, modifiers):
    
        if self.tagger.on_editor:
    
            current_symbol = ""
            index_update = 0

            if symbol == pyglet.window.key.ENTER:
                current_symbol = "\u2028"
                index_update = 1

            elif as_ascii(
                    symbol
            ) in letters and "MOD_SHIFT" in pyglet.window.key.modifiers_string(
                    modifiers):
                current_symbol = as_ascii(symbol).upper()
                index_update = 1

            elif as_ascii(symbol) in letters:
                current_symbol = as_ascii(symbol).lower()
                index_update = 1

            elif symbol == pyglet.window.key.BACKSPACE and len(self.text) > 0:
                cut_index = max(0, self.index - 1)
                self.text = self.text[:cut_index] + self.text[cut_index+1:]
                index_update = 0

            elif symbol == pyglet.window.key.SPACE:
                current_symbol = ' '
                index_update = 1
                
            elif symbol == pyglet.window.key.LEFT:
                current_symbol = ""
                index_update = -1
                
            elif symbol == pyglet.window.key.RIGHT:
                current_symbol = ""
                index_update = 1
                
            self.text = self.text[:self.index] + current_symbol + self.text[self.index:]
            self.index += index_update
            self.index = max(0, self.index)
            self.index = min(len(self.text), self.index)

            self.tagger.program = self.text
            self.document.text = self.text


sample_map = [
    (1, 1, "deep water"), (1, 2, "deep water"), (1, 3, "deep water"), 
    (2, 1, "deep water"), (2, 2, "deep water"), (2, 3, "deep water"), 
    (3, 1, "deep water"), (3, 2, "deep water"), (3, 3, "deep water")
]

tagger = MapTagger()
tagger.read_map(sample_map)
tagger.draw_map()
tagger.update_models()

@window.event
def on_draw():
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    window.clear()
    map_batch.draw()
    ui_batch.draw()

pyglet.app.run()
