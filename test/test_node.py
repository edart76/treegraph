import unittest

from tree import Tree
from treegraph import Graph, GraphEdge, GraphNode, NodeAttr

class TestNode(unittest.TestCase):
	""" test for node methods """


	def test_nodeTyping(self):
		node = GraphNode()
		self.assertIsInstance(node, Tree)

	def test_nodeAttrs(self):
		node = GraphNode()

		result = node.addInput("testInput")
		self.assertIs(node.getInput("testInput"), result)
		self.assertIs(node.getInput("testInput").node, node)








