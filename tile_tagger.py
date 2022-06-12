from collections import defaultdict

import pyglet
import pyglet.window.key as keyboard
from pyglet.gl import glTexParameteri, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_NEAREST

from constants import PROMPT_TOKEN

SCROLL_SCALING = 40
TILE_SIDE = 48
HALFTILE = TILE_SIDE // 2
SCROLLABLE_PANEL_TOP = 400
TAG_SEPARATOR = 8
TAG_HEIGHT = 16
EMPTY_STRING = ""

letters = [
    l.upper()
    for l in "a b c d e f g h i j k l m n o p q r s t u v w x y z".split()
]


def as_ascii(s):
    return keyboard.symbol_string(s)


cool_purple = (58, 58, 165)
cool_coral = (192, 64, 64)
cool_white = (248, 231, 231)

window = pyglet.window.Window(1920, 1080)

background_batch = pyglet.graphics.Batch()
foreground_batch = pyglet.graphics.Batch()
hover_batch = pyglet.graphics.Batch()

color_batch = pyglet.graphics.Batch()

index = lambda: defaultdict(lambda: set())

tileset_resource = pyglet.image.load("./images/maps/lil_house.png")


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

        self.mouse_x = 0
        self.mouse_y = 0

        self.tile_x = 0
        self.tile_y = 0

        self.scroll_shift_y = 0
        self.scroll_shift_x = 0

        self.selected_tiles = set()
        self.selected_areas = {}
        self.tile_sequence = []

        self.tilemap.scale_x = 3
        self.tilemap.scale_y = 3

        self.virtual_nodes = []
        self.selected_virtual_nodes = []
        self.hovered_virtual_node = False

        self.drag = False

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):

        delta_y = int(scroll_y * SCROLL_SCALING)
    
        self.tilemap.y = self.tilemap.y - delta_y
        self.scroll_shift_y -= delta_y
        self.update_camera()

    def on_key_press(self, symbol, modifiers):

        modifiers = keyboard.modifiers_string(modifiers)

        if symbol == keyboard.LSHIFT:
            self.set_panel()

        if symbol == keyboard.TAB:
            self.dump_string()

        if symbol == keyboard.BACKSPACE and 'MOD_SHIFT' in modifiers:
            self.clear_label()

        if symbol == keyboard.LEFT:
            self.scroll_shift_x += 6 * TILE_SIDE
            self.tilemap.x += 6 * TILE_SIDE
            self.update_camera()

        if symbol == keyboard.RIGHT:
            self.scroll_shift_x -= 6 * TILE_SIDE
            self.tilemap.x -= 6 * TILE_SIDE
            self.update_camera()

        if symbol == keyboard.UP:
            self.scroll_shift_y -= 6 * TILE_SIDE
            self.tilemap.y -= 6 * TILE_SIDE
            self.update_camera()

        if symbol == keyboard.DOWN:
            self.scroll_shift_y += 6 * TILE_SIDE
            self.tilemap.y += 6 * TILE_SIDE
            self.update_camera()

    def on_mouse_press(self, x, y, button, modifiers):

        modifiers = keyboard.modifiers_string(modifiers)

        shift_modifier = 'MOD_SHIFT' in modifiers
        control_modifier = 'MOD_CTRL' in modifiers

        left_click = button == pyglet.window.mouse.LEFT
        right_click = button == pyglet.window.mouse.RIGHT

        simple = not shift_modifier and not control_modifier
        just_control = not shift_modifier and control_modifier
        just_shift = shift_modifier and not control_modifier
        
        tile_x = self.tile_x
        tile_y = self.tile_y

        tile_is_selected = (tile_x, tile_y) in self.selected_tiles

        if left_click and simple:
        
            # Drop current label at 'old' tile, if there is one
            self.drop_label()

            if tile_is_selected:
                self.unselect_tile(tile_x, tile_y)

            else: 
                self.select_tile(tile_x, tile_y)
                # Set new label at current tile
                self.set_label(tile_x * TILE_SIDE,
                               tile_y * TILE_SIDE)

        if left_click and just_shift and not tile_is_selected:

            self.drop_label()

            if len(self.tile_sequence) >= 1:
                self.area_select(tile_x, tile_y)
                
            self.set_label(tile_x * TILE_SIDE,
                           tile_y * TILE_SIDE)

        if left_click and just_shift and tile_is_selected:

            self.drop_label()

            if len(self.selected_tiles) >= 1:
                self.area_unselect(tile_x, tile_y)
                
        if right_click and not control_modifier:
            
            self.drag = not self.drag

        if left_click and just_control:

            self.make_node()
            self.clear_label()
            
    def update_camera(self):
    
        if self.panel:
            self.panel.adjust_to_scrolling()
        
        if self.label:
            self.label.adjust_to_scrolling()
    
        for _, rect in self.selected_areas.items():
            rect.adjust_to_scrolling()
            
        for node in self.virtual_nodes:
            node.adjust_to_scrolling()
        

    def on_mouse_motion(self, x, y, dx, dy):

        self.tile_x = self.get_tile_x(x)
        self.tile_y = self.get_tile_y(y)
        self.mouse_x = x
        self.mouse_y = y

        if self.drag:
            self.scroll_shift_y += dy
            self.scroll_shift_x += dx
            self.tilemap.x += dx
            self.tilemap.y += dy
            self.update_camera()

    def on_key_release(self, symbol, modifiers):
        if symbol == keyboard.LSHIFT and self.panel:
            self.drop_panel()
            
    def select_tile(self, x, y):
        self.tile_sequence.append((x, y))
        self.selected_tiles.add((x, y))
        self.selected_areas[x, y] = AreaRectangle(x,
                                                  y,
                                                  self)

        window.push_handlers(self.label)
            
    def unselect_tile(self, x, y):
        self.tile_sequence.remove((x, y))
        self.selected_tiles.discard((x, y))
        rect = self.selected_areas.pop((x, y))
        rect.discard()
        
    def clear_label(self):
        self.unlink_label()
        self.drop_label()

    def unlink_label(self):

        for node in self.selected_virtual_nodes:
            node.unselect()

        self.selected_virtual_nodes = []
        self.selected_tiles = set()

        while self.selected_areas:
            _, rect = self.selected_areas.popitem()
            rect.discard()
            
    def drop_label(self):
        if self.label:
            if self.label.label_item:
                self.label.label_item.delete()
            self.label = None
            
    def set_label(self, x, y):
        self.label = ShortTextInput(self, PROMPT_TOKEN, x, y)
        self.label.adjust_to_scrolling()
        window.push_handlers(self.label)
            
    def make_node(self):
        
        selected_nodes = [n for n in self.selected_virtual_nodes]
        selected_tiles = list(self.selected_tiles)
        
        new_node = VirtualNode(self,
                               self.tile_x * TILE_SIDE + HALFTILE,
                               self.tile_y * TILE_SIDE + HALFTILE,
                               list(selected_nodes),
                               list(selected_tiles))
            
        new_node.update_edges()
        window.push_handlers(new_node)
        
        self.virtual_nodes.append(new_node)

    def get_tile_x(self, x):
        return (x - self.scroll_shift_x) // TILE_SIDE

    def get_tile_y(self, y):
        return (y - self.scroll_shift_y) // TILE_SIDE

    def drop_panel(self):
        if self.panel:
            for l in self.panel.label_panel:
                l.delete()
            if self.panel.panel_background:
                self.panel.panel_background.delete()
                self.panel.panel_background = None
            self.panel.tags = []
            self.panel = None

            if self.hovered_virtual_node:
                self.hovered_virtual_node.is_hovered = False
            self.hovered_virtual_node = False

    def set_panel(self):
        if not self.panel:
            self.panel = TagPanel(self, self.tile_x, self.tile_y)
            self.panel.update_labels()

    def dump_string(self):

        blank = lambda: print(EMPTY_STRING)

        for k in self.property_index:
            tile_x = k[0]
            tile_y = k[1]
            tile_properties = ', '.join(self.property_index[k])
            print(f"{tile_x}.{tile_y}: {tile_properties}")
            blank()

        for node in self.virtual_nodes:

            node_properties = ', '.join(list(node.tags))
            node_x = node.x // TILE_SIDE
            node_y = node.y // TILE_SIDE

            print(f"node at {node_x}.{node_y}: {node_properties}")

            for tile_x, tile_y in node.tile_children:
                node_name = f"{node_x}.{node_y}"
                tile_name = f"{tile_x}.{tile_y}"
                print(f"has child: node at {node_name}, tile {tile_name}")

            for child_node in node.node_children:
                child_x = child_node.x // TILE_SIDE
                child_y = child_node.y // TILE_SIDE
                child_name = f"{child_x}.{child_y}"
                print(f"has child: node at {node_name}, node at {child_name}")

            blank()
        
        blank()

    def load_string(self, text):
        #TODO: now we have nodes, and nodes should be loaded properly!
        for line in text.split("\n"):
            coordinates = tuple(line.split(":")[0].strip().split(", "))
            properties = {p.strip() for p in line.split(":")[1].split(",")}
            self.property_index[coordinates] |= properties
            
    def area_select(self, new_x, new_y):
        last_x, last_y = self.tile_sequence[-1]
        start_x, end_x = min(last_x, new_x), max(last_x, new_x)
        start_y, end_y = min(last_y, new_y), max(last_y, new_y)
        for i in range(start_x, end_x + 1):
            for j in range(start_y, end_y + 1):
                if (i, j) not in self.selected_tiles:
                    print(i, j)
                    self.select_tile(i, j)

    def area_unselect(self, new_x, new_y):
        last_x, last_y = self.tile_sequence[-1]
        start_x, end_x = min(last_x, new_x), max(last_x, new_x)
        start_y, end_y = min(last_y, new_y), max(last_y, new_y)
        for i in range(start_x, end_x + 1):
            for j in range(start_y, end_y + 1):
                print(i, j)
                if (i, j) in self.selected_tiles:
                    self.unselect_tile(i, j)
            
    def arrange_nodes(self):
    
        heights = defaultdict(lambda : [])
        
        for node in self.virtual_nodes:
        
            depth = node.depth
            heights[depth].append(node)
        
        depths = sorted(list([k for k in heights.keys()]))
        print(depths)
        
        for d in depths:
        
            for node in heights[d]:

                nodes_xs = [child.start_x for child in node.node_children]
                tiles_xs = [x * TILE_SIDE for x, y in node.tile_children]
                nodes_ys = [child.start_y for child in node.node_children]
                tiles_ys = [y * TILE_SIDE for x, y in node.tile_children]
                
                min_xs = []
                max_xs = []
                max_ys = []

                if not node.tile_children and not node.node_children:   
                    pass

                else:
            
                    if node.node_children and node.tile_children:
                        
                        min_xs.append(min(nodes_xs))
                        min_xs.append(min(tiles_xs))
                        max_xs.append(max(nodes_xs))
                        max_xs.append(max(tiles_xs))
                        max_ys.append(max(nodes_ys))
                        max_ys.append(max(tiles_ys))

                    if node.tile_children and not node.node_children:
                        
                        min_xs.append(min(tiles_xs))
                        max_xs.append(max(tiles_xs))
                        max_ys.append(max(tiles_ys))
                        
                    if node.node_children and not node.tile_children:

                        min_xs.append(min(nodes_xs))
                        max_xs.append(max(nodes_xs))
                        max_ys.append(max(nodes_ys))

                    leftmost_x = min(min_xs)
                    rightmost_x = max(max_xs)
                    
                    upmost_y = max(max_ys)
                    upmost_y += TILE_SIDE + HALFTILE
                        
                    center_x = leftmost_x
                    center_x += (rightmost_x - leftmost_x) // 2
                    
                    node.set_position(center_x, upmost_y)


class AreaRectangle:

    def __init__(self, tile_x, tile_y, tagger):
        
        self.x = tile_x
        self.y = tile_y

        self.tagger = tagger

        abs_x = tile_x * TILE_SIDE + self.tagger.scroll_shift_x
        abs_y = tile_y * TILE_SIDE + self.tagger.scroll_shift_y

        self.shape = pyglet.shapes.Rectangle(x=abs_x, y=abs_y,
                                             width=TILE_SIDE,
                                             height=TILE_SIDE,
                                             color=(0, 255, 0),
                                             batch=hover_batch)

        self.shape.opacity = 100
        self.panel = False

    def adjust_to_scrolling(self):
    
        self.shape.x = self.x * TILE_SIDE + self.tagger.scroll_shift_x
        self.shape.y = self.y * TILE_SIDE + self.tagger.scroll_shift_y
        
        if self.panel:

            self.panel.x = self.x * TILE_SIDE + self.tagger.scroll_shift_x
            self.panel.y = self.y * TILE_SIDE + self.tagger.scroll_shift_y

    def discard(self):
        self.shape.delete()
        self.shape = None

    def show_panel(self):
        self.panel = TagPanel(self.tagger,
                              self.x,
                              self.y)
        self.panel.update_labels()

    def hide_panel(self):
        if self.panel:
            for l in self.panel.label_panel:
                l.delete()
            if self.panel.panel_background:
                self.panel.panel_background.delete()
                self.panel.panel_background = None
            self.panel.tags = []
            self.panel = None


class VirtualNode:
    def __init__(self, tagger, x, y, node_children, tile_children):
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.node_children = node_children
        self.tile_children = tile_children
        self.shape = pyglet.shapes.Rectangle(x=self.x, y=self.y,
                                             width=TILE_SIDE,
                                             height=TILE_SIDE,
                                             color=(0, 125, 255),
                                             batch=hover_batch)
        self.shape.opacity = 128
        self.edges = []
        self.selected = False
        self.show_edges = False
        self.tags = set()
        self.tagger = tagger
        self.is_hovered = False
        self.panel = False
        
        self.tagger.virtual_nodes.append(self)
        
        self.depth = 0
        
        if self.node_children:
            depths = [child.depth for child in self.node_children]
            self.depth = max(depths) + 1
            
        self.tagger.arrange_nodes()


    def update_edges(self):

        while self.edges:
            current_edge = self.edges.pop()
            current_edge.delete()
            current_edge = None

        self.edges = []

        self_center_x = self.x + HALFTILE
        self_center_y = self.y + HALFTILE

        if self.show_edges:

            for child in self.node_children:
                child_center_x = child.x + HALFTILE
                child_center_y = child.y + HALFTILE
                new_edge = pyglet.shapes.Line(self_center_x, self_center_y,
                                            child_center_x, child_center_y,
                                            batch=hover_batch,
                                            width=2, color=(255, 0, 0))
                new_edge.opacity = 100
                self.edges.append(new_edge)

            for (child_x, child_y) in self.tile_children:

                child_center_x = child_x * TILE_SIDE + HALFTILE
                child_center_x += self.tagger.scroll_shift_x

                child_center_y = child_y * TILE_SIDE + HALFTILE
                child_center_y += self.tagger.scroll_shift_y


                new_edge = pyglet.shapes.Line(self_center_x, self_center_y,
                                            child_center_x, child_center_y,
                                            batch=hover_batch,
                                            width=2, color=(255, 0, 0))
                new_edge.opacity = 100

                self.edges.append(new_edge)

    def on_mouse_press(self, x, y, button, modifiers):

        modifiers_string = keyboard.modifiers_string(modifiers)

        right_click = button == pyglet.window.mouse.RIGHT
        control_mod = 'MOD_CTRL' in modifiers_string
        selection_combo = right_click and control_mod

        within_x = x >= self.x and self.x + TILE_SIDE >= x
        within_y = y >= self.y and self.y + TILE_SIDE >= y
        tile_is_hovered = within_x and within_y

        if selection_combo and tile_is_hovered and not self.selected:
            
            self.select()
            self.tagger.drop_label()
            self.tagger.set_label(self.start_x, self.start_y)
            self.tagger.selected_virtual_nodes.append(self)

        elif selection_combo and tile_is_hovered and self.selected:
            self.unselect()
            self.tagger.selected_virtual_nodes.remove(self)
            self.tagger.clear_label() # drop or clear?

    def on_mouse_motion(self, x, y, dx, dy):

        within_x = x >= self.x and self.x + TILE_SIDE >= x
        within_y = y >= self.y and self.y + TILE_SIDE >= y
        tile_is_hovered = within_x and within_y

        if tile_is_hovered and not self.is_hovered:
            self.is_hovered = True
            if self.tagger.hovered_virtual_node:
                self.tagger.hovered_virtual_node.is_hovered = False
            self.tagger.hovered_virtual_node = self
        
        if not tile_is_hovered and self.is_hovered:
            self.is_hovered = False
            self.tagger.hovered_virtual_node = False

    def on_key_press(self, symbol, modifiers):

        if self.selected and symbol == keyboard.DELETE:
            self.discard()

    def adjust_to_scrolling(self):
        
        self.x = self.start_x + self.tagger.scroll_shift_x
        self.y = self.start_y + self.tagger.scroll_shift_y
        self.shape.x = self.x
        self.shape.y = self.y
        self.update_edges()
        
        if self.panel:
            self.panel.adjust_to_scrolling()

    def select(self):
        self.selected = True
        self.shape.color = (0, 0, 255)
        self.show_tree()

    def unselect(self):
        self.selected = False
        self.shape.color = (0, 125, 255)
        self.hide_tree()

    def show_tree(self):

        self.show_edges = True
        self.show_panel()
        self.update_edges()

        for node in self.node_children:
            node.show_tree()

        for tile_x, tile_y in self.tile_children:

            if (tile_x, tile_y) not in self.tagger.selected_areas:

                new_rectangle = AreaRectangle(tile_x,
                                              tile_y,
                                              self.tagger)

                new_rectangle.shape.color = (255, 125, 0)

                self.tagger.selected_areas[tile_x, tile_y] = new_rectangle

            self.tagger.selected_areas[tile_x, tile_y].show_panel()

    def hide_tree(self):

        self.show_edges = False
        self.hide_panel()
        self.update_edges()

        for node in self.node_children:
            if not node.selected:
                node.hide_tree()

        for tile_x, tile_y in self.tile_children:

            if (tile_x, tile_y) in self.tagger.selected_areas:
            
                self.tagger.selected_areas[tile_x, tile_y].hide_panel()

                if (tile_x, tile_y) not in self.tagger.selected_tiles:
                    chomeur_tile = self.tagger.selected_areas.pop((tile_x, tile_y))
                    chomeur_tile.discard()

    def show_panel(self):

        self.panel = TagPanel(self.tagger,
                              self.start_x,
                              self.start_y,
                              virtual_node=self)

        self.panel.update_labels()

    def hide_panel(self):
        if self.panel:
            for l in self.panel.label_panel:
                l.delete()
            if self.panel.panel_background:
                self.panel.panel_background.delete()
                self.panel.panel_background = None
            self.panel.tags = []
            self.panel = False

    def discard(self):
        self.unselect()
        self.hide_tree()
        self.hide_panel()
        self.shape.delete()
        self.shape = None
        for node in self.tagger.virtual_nodes:
            if self in node.node_children:
                node.node_children.remove(self)
        self.tagger.virtual_nodes.remove(self)
        self.tagger.selected_virtual_nodes.remove(self)
        
    def set_position(self, x, y):
        self.start_x = x
        self.start_y = y
        self.adjust_to_scrolling()

class ShortTextInput:

    def __init__(self, tagger, text, input_x, input_y):
        
        self.tagger = tagger
        self.text = text
        self.x = input_x
        self.y = input_y
        self.start_x = input_x
        self.start_y = input_y
        
        self.label_item = pyglet.text.Label(text=self.text,
                                            font_name="Go Mono",
                                            x=self.x,
                                            y=self.y,
                                            font_size=14,
                                            align="left",
                                            color=(255, 255, 255, 255),
                                            batch=hover_batch)

    def update_label(self):
    
        if self.label_item:
            self.label_item.delete()
            self.label_item = None
            
        self.label_item = pyglet.text.Label(text=self.text,
                                            font_name="Go Mono",
                                            x=self.x,
                                            y=self.y,
                                            font_size=14,
                                            align="left",
                                            color=(255, 255, 255, 255),
                                            batch=hover_batch)

    def on_key_press(self, symbol, modifiers):

        modifiers = keyboard.modifiers_string(modifiers)

        if symbol == keyboard.ENTER:
        
            new_tags = set([s.strip() for s in self.text.split(",")])

            selected_tiles = list(self.tagger.selected_tiles)

            for (tile_x, tile_y) in selected_tiles:
                self.tagger.property_index[tile_x, tile_y] |= new_tags

            for node in self.tagger.selected_virtual_nodes:
                node.tags |= new_tags

            self.tagger.clear_label()

        elif as_ascii(symbol) in letters and "MOD_SHIFT" in modifiers:

            key_string = keyboard.symbol_string(symbol)

            if self.text == PROMPT_TOKEN:
                self.text = key_string

            else:
                self.text = self.text + key_string
                self.update_label()

        elif as_ascii(symbol) in letters:

            key_string = keyboard.symbol_string(symbol)

            if self.text == PROMPT_TOKEN:
                self.text = key_string.lower()
                self.update_label()
            
            else:
                self.text = self.text + key_string.lower()
                self.update_label()

        elif symbol == keyboard.BACKSPACE and len(self.text) > 0:
            self.text = self.text[:-1]
            self.update_label()

        elif symbol == keyboard.SPACE:
            self.text = self.text + ' '
            self.update_label()

        elif symbol == keyboard.PARENLEFT:
            self.text = self.text + '('
            self.update_label()

        elif symbol == keyboard.PARENRIGHT:
            self.text = self.text + ')'
            self.update_label()

        elif symbol == keyboard.COLON:
            self.text = self.text + ":"
            self.update_label()

        elif symbol == keyboard.COMMA:
            self.text = self.text + ","
            self.update_label()

        else:
            pass
            
    def adjust_to_scrolling(self):
        self.x = self.start_x + self.tagger.scroll_shift_x
        self.y = self.start_y + self.tagger.scroll_shift_y
        self.update_label()


class TagPanel:

    def __init__(self, tagger, tile_x, tile_y, virtual_node=False):

        self.tagger = tagger
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.tags = []
        self.label_panel = []
        self.x = tile_x * TILE_SIDE
        self.y = tile_y * TILE_SIDE
        self.panel_background = None
        self.virtual_node = virtual_node

        if self.virtual_node:
            self.x = self.virtual_node.x
            self.y = self.virtual_node.y

        if not self.virtual_node and self.tagger.hovered_virtual_node:
            self.virtual_node = self.tagger.hovered_virtual_node
            
        self.adjust_to_scrolling()

    def update_tags(self):
        self.tags = []

        if not self.virtual_node:
            for t in self.tagger.property_index[self.tile_x, self.tile_y]:
                self.tags.append(t)
        
        if self.virtual_node:
            for t in self.virtual_node.tags:
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
            y=self.y-int(bottom_y)+15,
            width=bottom_x,
            height=bottom_y,
            color=(60, 40, 40),
            batch=foreground_batch)
                
    def adjust_to_scrolling(self):
        
        self.x = self.tile_x * TILE_SIDE + self.tagger.scroll_shift_x
        self.y = self.tile_y * TILE_SIDE + self.tagger.scroll_shift_y
            
        self.update_labels()


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
