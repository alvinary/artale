# for logic constant in tiles:
#    for category name in categories:
#        if (category, constant) in relations:
#            map[tile.x, tile.y] = atlas[cat.x, cat.y]
# podes tener eso listo en un diccionario

# so:
# Atlas[x, y] debería ser el sprite

from collections import defaultdict

import pyglet

# Define the side of a tile in pixels, as tiles are stored in a png, 
# jpeg or bitmap image, and define the factor by which tiles will
# be scaled when displayed
TILE_SIZE = 16
SCALING_FACTOR = 2

# Define the width and height of the window
WINDOW_WIDTH = 1420
WINDOW_HEIGHT = 810

# Define the (x, y) corner (x from the left of the window to the right,
# y from bottom to top) of the rectangular region of the window where 
# maps will be drawn
MAP_REGION_X = 10
MAP_REGION_Y = 10

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


sample_map = [
    (1, 1, "deep water"), (1, 2, "deep water"), (1, 3, "deep water"), 
    (2, 1, "deep water"), (2, 2, "deep water"), (2, 3, "deep water"), 
    (3, 1, "deep water"), (3, 2, "deep water"), (3, 3, "deep water")
]

tagger = MapTagger()
tagger.read_map(sample_map)
tagger.draw_map()

@window.event
def on_draw():
    window.clear()
    map_batch.draw()

pyglet.app.run()
