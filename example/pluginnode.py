
"""basic node classes registered by default in graph object
IntNode is prototypical example of user-defined node
plugin registration functions are then called to add these
nodes into the graph
"""
from treegraph.node import GraphNode
from treegraph.plugin import registerNode



class IntNode(GraphNode):
	"""node with single int spinbox,
	outputs that value to its attribute
	"""

	def defineSettings(self):
		pass

	def defineAttrs(self):
		self.addOutput(name="value")


defaultNodes = [
	IntNode,
]

for i in defaultNodes:
	registerNode(i)

dynamicCls = type("GenNode", (IntNode, GraphNode), {})

