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

tileset_resource = pyglet.image.load("./images/maps/route_118.png")


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

        self.tilemap.scale_x = 3
        self.tilemap.scale_y = 3

        self.virtual_nodes = []
        self.selected_virtual_nodes = []
        self.hovered_virtual_node = False

        self.drag = False

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.tilemap.y = self.tilemap.y - int(scroll_y * SCROLL_SCALING)
        self.scroll_shift_y -= int(scroll_y * SCROLL_SCALING)
        for _, rect in self.selected_areas.items():
            rect.adjust_to_scrolling()
        for node in self.virtual_nodes:
            node.adjust_to_scrolling()

    def on_key_press(self, symbol, modifiers):

        modifiers = pyglet.window.key.modifiers_string(modifiers)

        if symbol == pyglet.window.key.LSHIFT:
            self.set_panel()

        if symbol == pyglet.window.key.TAB:
            self.dump_string()

        if symbol == pyglet.window.key.BACKSPACE and 'MOD_SHIFT' in modifiers:
            self.clear_label()

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

        for node in self.selected_virtual_nodes:
            node.drag = False

        modifiers = pyglet.window.key.modifiers_string(modifiers)

        shift_modifier = 'MOD_SHIFT' in modifiers
        control_modifier = 'MOD_CTRL' in modifiers

        simple = not shift_modifier and not control_modifier
        just_control = not shift_modifier and control_modifier

        tile_x = self.tile_x
        tile_y = self.tile_y

        if button == pyglet.window.mouse.LEFT and simple:

            if self.label:
                if self.label.label_item:
                    self.label.label_item.delete()
                self.label = None

            self.label = ShortTextInput(self, ">", x, y)

            if (tile_x, tile_y) in self.selected_tiles:
                self.selected_tiles.discard((tile_x, tile_y))
                rect = self.selected_areas.pop((tile_x, tile_y))
                rect.discard()

            else: 
            
                self.selected_tiles.add((tile_x, tile_y))

                self.selected_areas[tile_x, tile_y] = AreaRectangle(self.tile_x,
                                                                    self.tile_y,
                                                                    self)

                window.push_handlers(self.label)

        if button == pyglet.window.mouse.RIGHT and not control_modifier:
            self.drag = not self.drag

        if button == pyglet.window.mouse.LEFT and just_control:

            selected_nodes = [n for n in self.selected_virtual_nodes]
            selected_tiles = list(self.selected_tiles)
            
            new_node = VirtualNode(self, x, y, list(selected_nodes),
                                   list(selected_tiles))
            
            new_node.update_edges()
            window.push_handlers(new_node)
            
            self.clear_label()


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
            for _, rect in self.selected_areas.items():
                rect.adjust_to_scrolling()
            for node in self.virtual_nodes:
                node.adjust_to_scrolling()

    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.LSHIFT and self.panel:
            self.drop_panel()

    def clear_label(self):

        for node in self.selected_virtual_nodes:
            node.unselect()

        self.selected_virtual_nodes = []
        self.selected_tiles = set()

        while self.selected_areas:
            _, rect = self.selected_areas.popitem()
            rect.discard()
        
        if self.label:
            if self.label.label_item:
                self.label.label_item.delete()
            self.label = None

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
        for k in self.property_index:
            print(f"{k[0]}.{k[1]}: {', '.join(self.property_index[k])}")
        print("")
        for node in self.virtual_nodes:
            node_properties = ', '.join(list(node.tags))
            print(f"node at {node.x // TILE_SIDE}.{node.y // TILE_SIDE}: {node_properties}")
            for tile_x, tile_y in node.tile_children:
                print(f"has child: node at {node.x}.{node.y}, tile {tile_x}.{tile_y}")
            for child_node in node.node_children:
                child_x = child_node.x // TILE_SIDE
                child_y = child_node.y // TILE_SIDE
                print(f"has child: node at {node.x}.{node.y}, node at {child_x}.{child_y}")
            print("")
        print("")

    def load_string(self, text):
        for line in text.split("\n"):
            coordinates = tuple(line.split(":")[0].strip().split(", "))
            properties = {p.strip() for p in line.split(":")[1].split(",")}
            self.property_index[coordinates] |= properties
            
    def arrange_nodes(self):
    
        heights = defaultdict(lambda : [])
        
        for node in self.virtual_nodes:
        
            depth = node.depth
            heights[depth].append(node)
        
        new_positions = {}
        
        depths = sorted(list([k for k in heights.keys()]))
        print(depths)
        
        for d in depths:
        
            for node in heights[d]:
            
                if node.node_children and node.tile_children:
                
                    minimum_child_x = min([child.x for child in node.node_children])
                    minimum_tile_x = min([x * TILE_SIDE for x, y in node.tile_children])
                
                    leftmost_x = min(minimum_child_x, minimum_tile_x)
                
                    maximum_child_x = max([child.x for child in node.node_children])
                    maximum_tile_x = max([x * TILE_SIDE for x, y in node.tile_children])
                
                    rightmost_x = max(minimum_child_x, minimum_tile_x)
                    
                    upmost_tile_y = max([y * TILE_SIDE for x, y in node.tile_children])
                    upmost_node_y = max([child.y for child in node.node_children])
                
                    upmost_y = max(upmost_tile_y, upmost_node_y) + TILE_SIDE + TILE_SIDE // 2
                
                    node.set_position(leftmost_x + (rightmost_x - leftmost_x) // 2, upmost_y)

                if node.tile_children and not node.node_children:
                
                    leftmost_x = min([x * TILE_SIDE for x, y in node.tile_children])
                
                    rightmost_x = max([x * TILE_SIDE for x, y in node.tile_children])
                    
                    upmost_y = max([y * TILE_SIDE for x, y in node.tile_children]) + TILE_SIDE + TILE_SIDE // 2

                    node.set_position(leftmost_x + (rightmost_x - leftmost_x) // 2, upmost_y)
                    
                if node.node_children and not node.tile_children:
                     
                    leftmost_x = min([child.x for child in node.node_children])
                
                    rightmost_x = max([child.x for child in node.node_children])
                
                    upmost_y = max([child.y for child in node.node_children]) + TILE_SIDE + TILE_SIDE // 2
                
                    node.set_position(leftmost_x + (rightmost_x - leftmost_x) // 2, upmost_y)
                
                if not node.tile_children and not node.node_children:
                
                    pass
                    
                    

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
            self.depth = max([child.depth + 1 for child in self.node_children])
            
        print("Depth: ", self.depth)
            
        self.tagger.arrange_nodes()


    def update_edges(self):

        while self.edges:
            current_edge = self.edges.pop()
            current_edge.delete()
            current_edge = None

        self.edges = []

        self_center_x = self.x + TILE_SIDE // 2
        self_center_y = self.y + TILE_SIDE // 2

        if self.show_edges:

            for child in self.node_children:
                child_center_x = child.x + TILE_SIDE // 2
                child_center_y = child.y + TILE_SIDE // 2
                new_edge = pyglet.shapes.Line(self_center_x, self_center_y,
                                            child_center_x, child_center_y,
                                            batch=hover_batch,
                                            width=2, color=(255, 0, 0))
                new_edge.opacity = 100
                self.edges.append(new_edge)

            for (child_x, child_y) in self.tile_children:
                child_center_x = child_x * TILE_SIDE + TILE_SIDE // 2 + self.tagger.scroll_shift_x
                child_center_y = child_y * TILE_SIDE + TILE_SIDE // 2 + self.tagger.scroll_shift_y
                new_edge = pyglet.shapes.Line(self_center_x, self_center_y,
                                            child_center_x, child_center_y,
                                            batch=hover_batch,
                                            width=2, color=(255, 0, 0))
                new_edge.opacity = 100
                self.edges.append(new_edge)

    def on_mouse_press(self, x, y, button, modifiers):

        modifiers_string = pyglet.window.key.modifiers_string(modifiers)

        right_click = button == pyglet.window.mouse.RIGHT
        control_mod = 'MOD_CTRL' in modifiers_string
        within_x = x >= self.x and self.x + TILE_SIDE >= x
        within_y = y >= self.y and self.y + TILE_SIDE >= y

        if right_click and control_mod and within_x and within_y and not self.selected:
            
            self.select()
            
            self.tagger.selected_virtual_nodes.append(self)

            if self.tagger.label:
                if self.tagger.label.label_item:
                    self.tagger.label.label_item.delete()
                self.tagger.label = None

            self.tagger.label = ShortTextInput(self.tagger, ">", x, y)
            window.push_handlers(self.tagger.label)

        elif right_click and control_mod and within_x and within_y and self.selected:
            self.unselect()
            self.tagger.selected_virtual_nodes.remove(self)

    def on_mouse_motion(self, x, y, dx, dy):

        within_x = x >= self.x and self.x + TILE_SIDE >= x
        within_y = y >= self.y and self.y + TILE_SIDE >= y

        if within_x and within_y and not self.is_hovered:
            self.is_hovered = True
            if self.tagger.hovered_virtual_node:
                self.tagger.hovered_virtual_node.is_hovered = False
            self.tagger.hovered_virtual_node = self
        
        if not (within_x and within_y) and self.is_hovered:
            self.is_hovered = False
            self.tagger.hovered_virtual_node = False

    def on_key_press(self, symbol, modifiers):

        if self.selected and symbol == pyglet.window.key.Q:
            self.discard()

    def adjust_to_scrolling(self):
        self.x = self.start_x + self.tagger.scroll_shift_x
        self.y = self.start_y + self.tagger.scroll_shift_y
        self.shape.x = self.x
        self.shape.y = self.y
        self.update_edges()

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

                self.tagger.selected_areas[tile_x, tile_y] = AreaRectangle(tile_x,
                                                                           tile_y,
                                                                           self.tagger)

                self.tagger.selected_areas[tile_x, tile_y].shape.color = (255, 125, 0)

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
                              0,
                              0,
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
        self.drag_shift_x = 0
        self.drag_shift_x = 0
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.adjust_to_scrolling()

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

        modifiers = pyglet.window.key.modifiers_string(modifiers)

        if symbol == pyglet.window.key.ENTER:
        
            new_tags = set([s.strip() for s in self.text.split(",")])

            selected_tiles = list(self.tagger.selected_tiles)

            for (tile_x, tile_y) in selected_tiles:
                self.tagger.property_index[tile_x, tile_y] |= new_tags

            for node in self.tagger.selected_virtual_nodes:
                node.tags |= new_tags

            self.tagger.clear_label()

        elif as_ascii(symbol) in letters and "MOD_SHIFT" in modifiers:

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

        elif symbol == pyglet.window.key.COMMA:
            self.text = self.text + ","
            self.label_item.delete()
            self.update_label()

        else:
            pass


class TagPanel:

    def __init__(self, tagger, tile_x, tile_y, virtual_node=False):

        self.tagger = tagger
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.tags = []
        self.label_panel = []
        self.x = tagger.mouse_x
        self.y = tagger.mouse_y
        self.panel_background = None
        self.virtual_node = virtual_node

        if self.virtual_node:
            self.x = self.virtual_node.x
            self.y = self.virtual_node.y

        if not self.virtual_node and self.tagger.hovered_virtual_node:
            self.virtual_node = self.tagger.hovered_virtual_node

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
