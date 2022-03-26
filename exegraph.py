from __future__ import annotations

import typing as T
from functools import partial
from enum import Enum

from tree import Signal

from treegraph.node import GraphNode
from treegraph.attr import NodeAttr
from treegraph.edge import GraphEdge
from treegraph.group import NodeSet
from treegraph.graph import Graph

# should probably have its functions moved to a lib
from treegraph.exepath import ExecutionPath


class GraphExecutionManager(object):
	"""manages context for entire execution process"""
	def __init__(self, graph:ExeGraph):
		# super(GraphExecutionManager, self).__init__(graph)
		self.graph = graph

	def __enter__(self):
		"""set graph state"""
		self.graph.setState("executing")
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		"""reset graph state"""
		if exc_type:
			self.graph.setState("neutral")
		self.graph.setState("neutral")


class ExeGraph(Graph):
	"""Graph with extra fuunctions to handle
	node execution"""

	class GraphState(Enum):  # graph states
		neutral = "neutral"
		executing = "executing",
		complete = "complete",
		failed = "failed",
		approved = "approved"

	states = GraphState._member_names_[:]

	def __init__(self, name="main"):
		super(ExeGraph, self).__init__(name)
		self.state = self.GraphState.neutral
		"""used to check if execution is in progress; prevents any change to topology
		if it is. states are neutral, executing, (routing, for massive graphs?)"""
		self.stateChanged = Signal()




	### region node execution ###
	def getExecPath(self, nodes):
		"""creates execution path from unordered nodes"""
		if nodes:
			newPath = ExecutionPath.getExecPathToNodes(self, nodes)
		else:
			newPath = ExecutionPath.getExecPathToAll(self)
		self.log("exec path is {}".format(i.name for i in newPath.sequence))
		return newPath

	def executeNodes(self, nodes=None, index=-1):
		"""executes nodes in given sequence to given index"""

		execPath = self.getExecPath(nodes=nodes)
		#self.setState("executing")
		# enter graph-level execution state here
		with GraphExecutionManager(self):
			for i in execPath.sequence:
				nodeIndex = index
				if index == -1: # all steps
					nodeIndex = len(i.executionStages()) # returns ["plan", "build"] etc
				# for n in range(nodeIndex):
				# 	kSuccess = i.execute(index=n)
				"""currently no support for executing all nodes to stage n before
				all to n+1"""
				try:
					kSuccess = i.execToStage(index)
					# enter and exit node-level execution state
					self.log("all according to kSuccess")
				except RuntimeError("NOT ACCORDING TO KSUCCESS"):
					pass

		# exit graph-level execution
		#self.setState("neutral")
		self.log("execution complete")

	def resetNodes(self, nodes=None):
		"""resets nodes to pre-executed state"""
		if not nodes:
			nodes = self.nodes
		for i in nodes:
			i.reset()
		"""currently no support for specific order during reset, as in maya there
		is no need. however, it could be done"""
		self.sync()

	def reset(self):
		self.resetNodes(self.nodes)
		self.setState(self.State.neutral)

	def getExecActions(self, nodes=None):
		"""returns available execution actions for target nodes, or all"""
		return {"execute nodes" : partial(
			self.executeNodes, kwargs={"nodes" : nodes},
			name="execute nodes"),
			"reset nodes": partial(
				self.resetNodes, kwargs={"nodes" : nodes},
				name="reset nodes"),
			"rig it like you dig it" : partial(
				self.executeNodes, name="rig it like you dig it"),
			"reset all": partial(
				self.reset, name="reset all")
		}

	def setState(self, state:GraphState):
		"""didn't know this was also a magic method but whatevs"""
		self.state = state
		self.stateChanged()

	#endregion


