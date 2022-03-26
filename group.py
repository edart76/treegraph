


class AbstractRelation(object):
	"""base class for things like group boxes, vertex networks etc"""

	def __init__(self, graph=None, name=""):
		self.graph = graph
		self.nodes = []

class NodeSet(AbstractRelation):
	"""defines a basic group of nodes"""
	def __init__(self, graph=None, name=""):
		super(NodeSet, self).__init__(graph)


