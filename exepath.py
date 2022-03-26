
from __future__ import annotations

import typing as T
from functools import partial
from enum import Enum

from treegraph.node import GraphNode

if T.TYPE_CHECKING:
	from treegraph.attr import NodeAttr
	from treegraph.edge import GraphEdge
	from treegraph.group import NodeSet
	from treegraph.graph import Graph



class ExecutionPath(object):
	"""class describing a sequential path through the graph"""
	def __init__(self, graph=None):
		self.sequence = []
		self.graph = graph
		self.seedNodes = set() # nodes with no history
		self.passedNodes = set() # nodes passed by query
		self.boundaryNodes = set()
		self.allNodes = set() # safety

		self.currentIndex = 1 # never less than 1

	"""this could also store execution indices, but only if we need
	things like 'build all plan stages, then all run stages' etc"""


	@property
	def nodeSet(self):
		"""returns set of nodes in sequence"""
		return set(self.sequence)

	def getSeedNodes(self, starters):
		"""returns the seed nodes for a set of nodes"""
		allHistory = self.graph.getCombinedHistory(starters)
		for i in [n for n in starters if not n.history]:
			allHistory = allHistory.union({i}) # add nodes
		seedNodes = self.graph.getSeedNodes()
		ourSeeds = seedNodes.intersection(allHistory)
		return ourSeeds

	def resetIndices(self):
		for i in self.allNodes:
			i.index = None

	def setNodes(self, targets):
		"""initialise path with various known values"""
		self.passedNodes = set(targets)
		self.seedNodes = self.getSeedNodes(targets)

		# safety
		self.boundaryNodes = self.passedNodes.union(self.seedNodes)
		self.allNodes = self.boundaryNodes.union(self.graph.getNodesBetween(
			nodes=self.boundaryNodes))

	def buildToNodes(self):
		"""get order only containing targets' critical paths"""
		self.resetIndices()

		self.currentIndex = 1
		for i in self.seedNodes:
			self.setIndex(i)
			testSet = self.passedNodes.union({i})
			between = self.graph.getNodesBetween(testSet, include=True)
			for n in between:
				self.setIndexBranchSafe(n)
		# donezo????????????

	def setIndexBranchSafe(self, node:GraphNode):
		"""sets index of target, or looks back til it finds a node with an index"""
		if node.index:
			return
		for i in node.directHistory:
			if not i.index:
				self.setIndexBranchSafe(i)
		self.setIndex(node)

	def setIndex(self, node):
		"""sets node index to current index and increments"""
		if node.index: # super duper sketched out about this
			return
		node.index = self.currentIndex
		self.currentIndex += 1
		self.sequence.append(node) # sure why not

	@staticmethod
	def getExecPathToNodes(graph:"Graph"=None,
	                       targets:T.Set[GraphNode]=None)->ExecutionPath:
		"""gets execution path to nodes"""
		path = ExecutionPath(graph)
		path.setNodes(targets)
		path.resetIndices()
		path.buildToNodes()
		return path

	@staticmethod
	def getExecPathToAll(graph=None):
		"""execute everything"""
		path = ExecutionPath(graph)
		path.setNodes(graph.nodes)
		path.resetIndices()
		path.buildToNodes() #?
		return path
