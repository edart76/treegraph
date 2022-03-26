# edge object in node graph
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Tuple
if TYPE_CHECKING:
	from treegraph.node import GraphNode
	from treegraph.attr import NodeAttr
	from treegraph.graph import Graph

from tree import Signal

class GraphEdge(object):
	"""connects two abstractNode/abstractAttr objects"""


	def __init__(self, source:"NodeAttr"=None,
	             dest:"NodeAttr"=None,
	             graph:"Graph"=None):
		"""source and dest to be abstractAttrItems"""
		self.graph = graph
		if source:
			self.sourceAttr = source
			self.sourceNode = source.node
		if dest:
			self.destAttr = dest
			self.destNode = dest.node
		self.dataType = self.sourceAttr.dataType

		# signal on edge garbage collected / destroyed
		# self.edgeDestroyed = Signal()


	def __str__(self):
		""" dirty solution to remove edge objects from serialisation process """
		return str( self.serialise() )

	# def __del__(self):
	# 	"""fires edge death signal"""
	# 	print("edge __del__")
	# 	self.edgeDestroyed(self)

	# for anything dealing with nodes and attributes, return node first
	@property
	def source(self)->Tuple["GraphNode", "NodeAttr"]:
		return self.sourceNode, self.sourceAttr

	@property
	def dest(self)->Tuple["GraphNode", "NodeAttr"]:
		return self.destNode, self.destAttr

	def oppositeAttr(self, attr)->"NodeAttr":
		""" given one attr, return its opposite,
		or None if attr is not recognised """
		if attr == self.sourceAttr:
			return self.destAttr
		elif attr == self.destAttr:
			return self.sourceAttr
		else:
			return None

	def propagate(self):
		"""transfers value of source attr to dest attr"""
		self.destAttr.value = self.sourceAttr.value

	def serialise(self):
		"""store uids of nodes, and names of attributes - edges regenerated last"""
		serial = {
			"source" : {
				"node" : self.sourceNode.uid,
				"attr" : self.sourceAttr.name,
				"name" : self.sourceNode.name #readability
			},
			"dest" : {
				"node" : self.destNode.uid,
				"attr" : self.destAttr.name,
				"name" : self.destNode.name #matters
			}
		}
		return serial

	@staticmethod
	def fromDict(serial, graph=None):
		sourceNode = graph.nodeFromUID(serial["source"]["node"])
		sourceAttr = sourceNode.getOutput(serial["source"]["attr"])

		destNode = graph.nodeFromUID(serial["dest"]["node"])
		destAttr = destNode.getInput(serial["dest"]["attr"])

		return GraphEdge(source=sourceAttr, dest=destAttr, graph=graph)
