from collections import defaultdict

import pyglet
from pyglet.gl import glTexParameteri, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_NEAREST

SCROLL_SCALING = 40
TILE_SIDE = 48
SCROLLABLE_PANEL_TOP = 400
TAG_SEPARATOR = 8
TAG_HEIGHT = 16

letters = [
    l.upper()
    for l in "a b c d e f g h i j k l m n o p q r s t u v w x y z".split()
]


def as_ascii(s):
    return pyglet.window.key.symbol_string(s)


cool_purple = (58, 58, 165)
cool_coral = (192, 64, 64)
cool_white = (248, 231, 231)

window = pyglet.window.Window(1920, 1080)

background_batch = pyglet.graphics.Batch()
foreground_batch = pyglet.graphics.Batch()
hover_batch = pyglet.graphics.Batch()

color_batch = pyglet.graphics.Batch()

index = lambda: defaultdict(lambda: set())

tileset_resource = pyglet.image.load("./images/61816.png")


class TileTagger:

    def __init__(self):
        self.properties = set()
        self.tile_index = index()  # tile_index[a, b] = tile_name
        self.property_index = index()
        self.tilemap = pyglet.sprite.Sprite(tileset_resource,
                                            x=0,
                                            y=0,
                                            batch=background_batch)
        self.panel = None
        self.label = None
        self.tile_x = 0
        self.tile_y = 0
        self.scroll_shift_y = 0
        self.scroll_shift_x = 0

        self.tilemap.scale_x = 3
        self.tilemap.scale_y = 3

        self.drag = False

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.tilemap.y = self.tilemap.y - int(scroll_y * SCROLL_SCALING)
        self.scroll_shift_y -= int(scroll_y * SCROLL_SCALING)

    def on_key_press(self, symbol, modifiers):

        if symbol == pyglet.window.key.LSHIFT:
            if self.property_index[self.tile_x, self.tile_y]:
                self.set_panel(self.mouse_x, self.mouse_y)

        if symbol == pyglet.window.key.TAB:
            self.dump_string()

        if symbol == pyglet.window.key.LEFT:
            self.scroll_shift_x += 6 * TILE_SIDE
            self.tilemap.x += 6 * TILE_SIDE

        if symbol == pyglet.window.key.RIGHT:
            self.scroll_shift_x -= 6 * TILE_SIDE
            self.tilemap.x -= 6 * TILE_SIDE

        if symbol == pyglet.window.key.UP:
            self.scroll_shift_y -= 6 * TILE_SIDE
            self.tilemap.y -= 6 * TILE_SIDE

        if symbol == pyglet.window.key.DOWN:
            self.scroll_shift_y += 6 * TILE_SIDE
            self.tilemap.y += 6 * TILE_SIDE

    def on_mouse_press(self, x, y, button, modifiers):

        if button == pyglet.window.mouse.LEFT:

            if self.label:
                if self.label.label_item:
                    self.label.label_item.delete()
                self.label = None

            self.label = ShortTextInput(self, ">", x, y)
            window.push_handlers(self.label)

        if button == pyglet.window.mouse.RIGHT:
            self.drag = not self.drag

    def on_mouse_motion(self, x, y, dx, dy):
        self.tile_x = (x - self.scroll_shift_x) // TILE_SIDE
        self.tile_y = (y - self.scroll_shift_y) // TILE_SIDE
        self.mouse_x = x
        self.mouse_y = y

        if self.drag:
            self.scroll_shift_y += dy
            self.scroll_shift_x += dx
            self.tilemap.x += dx
            self.tilemap.y += dy

    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.LSHIFT and self.panel:
            self.drop_panel()

    def drop_panel(self):
        if self.panel:
            for l in self.panel.label_panel:
                l.delete()
            if self.panel.panel_background:
                self.panel.panel_background.delete()
                self.panel.panel_background = None
            self.panel.tags = []
            self.panel = None

    def set_panel(self, x, y):
        if not self.panel:
            self.panel = TagPanel(self, x, y)
            self.panel.update_labels()

    def dump_string(self):
        for k in self.property_index:
            print(f"{k[0]}, {k[1]}: {', '.join(self.property_index[k])}")
        print("")

    def load_string(self, text):
        for line in text.split("\n"):
            coordinates = tuple(line.split(":")[0].strip().split(", "))
            properties = {p.strip() for p in line.split(":")[1].split(",")}
            self.property_index[coordinates] |= properties


class ShortTextInput:

    def __init__(self, tagger, text, input_x, input_y):
        self.tagger = tagger
        self.text = text
        self.x = input_x
        self.y = input_y
        self.tile_x = self.tagger.tile_x
        self.tile_y = self.tagger.tile_y
        self.label_item = pyglet.text.Label(text=self.text,
                                            font_name="Go Mono",
                                            x=self.x,
                                            y=self.y,
                                            font_size=14,
                                            align="left",
                                            color=(255, 255, 255, 255),
                                            batch=hover_batch)

    def update_label(self):
        self.label_item = pyglet.text.Label(text=self.text,
                                            font_name="Go Mono",
                                            x=self.x,
                                            y=self.y,
                                            font_size=14,
                                            align="left",
                                            color=(255, 255, 255, 255),
                                            batch=hover_batch)

    def on_key_press(self, symbol, modifiers):

        if symbol == pyglet.window.key.ENTER:
            self.tagger.property_index[self.tile_x,
                                       self.tile_y].add(self.label_item.text)
            self.label_item.delete()
            self.label_item = None

        elif as_ascii(
                symbol
        ) in letters and "MOD_SHIFT" in pyglet.window.key.modifiers_string(
                modifiers):
            if self.text == ">":
                self.text = pyglet.window.key.symbol_string(symbol)
            else:
                self.text = self.text + pyglet.window.key.symbol_string(symbol)
                self.label_item.delete()
                self.update_label()

        elif as_ascii(symbol) in letters:
            if self.text == ">":
                self.text = pyglet.window.key.symbol_string(symbol).lower()
            else:
                self.text = self.text + pyglet.window.key.symbol_string(
                    symbol).lower()
                self.label_item.delete()
                self.update_label()

        elif symbol == pyglet.window.key.BACKSPACE and len(self.text) > 0:
            self.text = self.text[:-1]
            self.label_item.delete()
            self.update_label()

        elif symbol == pyglet.window.key.SPACE:
            self.text = self.text + ' '
            self.label_item.delete()
            self.update_label()

        elif symbol == pyglet.window.key.PARENLEFT:
            self.text = self.text + '('
            self.label_item.delete()
            self.update_label()

        elif symbol == pyglet.window.key.PARENRIGHT:
            self.text = self.text + ')'
            self.label_item.delete()
            self.update_label()

        elif symbol == pyglet.window.key.COLON:
            self.text = self.text + ":"
            self.label_item.delete()
            self.update_label()

        else:
            pass


class TagPanel:

    def __init__(self, tagger, x, y):
        self.tagger = tagger
        self.tile_x = self.tagger.tile_x
        self.tile_y = self.tagger.tile_y
        self.tags = []
        self.label_panel = []
        self.x = x
        self.y = y
        self.panel_background = None

    def update_tags(self):
        self.tags = []
        for t in self.tagger.property_index[self.tile_x, self.tile_y]:
            self.tags.append(t)

    def update_labels(self):
        self.update_tags()

        bottom_y = 0
        label = None

        for t in self.tags:

            label = pyglet.text.Label(text=t,
                                      font_name="Go Mono",
                                      x=self.x,
                                      y=self.y - int(bottom_y),
                                      font_size=11,
                                      align="left",
                                      color=(255, 255, 255, 220),
                                      batch=hover_batch)

            bottom_y += TAG_HEIGHT + TAG_SEPARATOR
            self.label_panel.append(label)

            bottom_x = 400

            self.panel_background = pyglet.shapes.Rectangle(
                x=self.x,
                y=self.y - int(bottom_y) + 15,
                width=bottom_x,
                height=bottom_y,
                color=(60, 40, 40),
                batch=foreground_batch)


@window.event
def on_draw():
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    window.clear()
    background_batch.draw()
    foreground_batch.draw()
    hover_batch.draw()
    color_batch.draw()


tagger = TileTagger()
window.push_handlers(tagger)

pyglet.app.run()
