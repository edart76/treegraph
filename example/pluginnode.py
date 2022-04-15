
"""basic node classesToReload registered by default in graph object
IntNode is prototypical example of user-defined node
plugin registration functions are then called to add these
nodes into the graph
"""
from treegraph.node import GraphNode
from treegraph.plugin import registerNodes



class IntNode(GraphNode):
	"""node with single int spinbox,
	outputs that value to its attribute
	"""

	def defineSettings(self):
		pass

	def defineAttrs(self):
		self.addOutput(name="value")



dynamicCls = type("GenNode", (IntNode, GraphNode), {})

defaultNodes = [
	IntNode, dynamicCls
]

#for i in defaultNodes:
registerNodes(defaultNodes)


