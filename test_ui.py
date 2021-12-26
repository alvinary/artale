import pytest
from ui import Node

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
