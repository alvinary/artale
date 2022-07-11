import pytest

from artale.interfaces.ui import Node, NODE_HEIGHT, NODE_WIDTH

def make_test_tree_a():
    root = Node("a")
    root.spawn_child("b")
    c_node = Node("c")
    c_node.spawn_child("d")
    c_node.spawn_child("e")
    root.add_child(c_node)
    return root

def make_test_tree_b():
    a = Node("a")
    b = Node("b")
    c = Node("c")
    d = Node("d")
    a.add_child(b)
    a.add_child(c)
    c.add_child(d)
    return a

def test_leaf_count_a():
    test_tree = make_test_tree_a()
    assert test_tree.count_leaves() == 3

def test_leaf_count_b():
    test_tree = make_test_tree_b()
    assert test_tree.count_leaves() == 2 

def shallow_inspect():
    a = make_test_tree_b()
    print(len(a.children))
    for c in a.children:
        print(c.text)
        print(len(c.children))

def test_count_left_and_depth():
    test_tree = make_test_tree_a()
    e = test_tree.children[1].children[1]
    print("Expected number of leaves to the left of node e: 2")
    print(f"Found... {e.count_left()} leaves!")
    assert e.count_left() == 2 and e.depth() == 2

def test_collect():
    assert len(make_test_tree_a().collect()) == 5

def test_arrange():
    test_tree = make_test_tree_a()
    test_tree.arrange()
    for n in test_tree.collect():
        print(f"label: {n.text}, depth: {n.depth()}, x: {n.x}, y: {n.y}")
        assert n.depth() * NODE_HEIGHT == n.y
        assert n.count_left() * NODE_WIDTH <= n.x
        assert (n.count_left() + 1) * NODE_WIDTH >= n.x

test_arrange()
