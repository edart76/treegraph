
import unittest

from tree import Tree
from treegraph import Graph, GraphEdge, GraphNode

class TestGraph(unittest.TestCase):
	""" test for graph methods """

	def setUp(self):
		self.graph = Graph(name="testGraph")

	def test_graphTyping(self):
		self.assertIsInstance(self.graph, Graph)

	def test_graphAddNode(self):
		node = GraphNode("testNode")

		result = node.addInput("testInput")
		self.assertIs(node.getInput("testInput"), result)
		self.assertIs(node.getInput("testInput").node, node)

		self.graph.addNode(node)

		self.assertIs(self.graph("testNode"), node)
		self.assertIs(self.graph, node.graph)



