from __future__ import annotations

import typing as T
from functools import partial
from enum import Enum

from tree import Signal, Tree
from tree.lib.object import ObjectComponent

from treegraph.node import GraphNode
from treegraph.attr import NodeAttr
from treegraph.edge import GraphEdge
from treegraph.group import NodeSet

from treegraph.constant import NodeState


# should probably have its functions moved to a lib
from treegraph.exepath import ExecutionPath

if T.TYPE_CHECKING:
	from treegraph.graph import Graph

"""Component object and context manager to manage node execution state
this must be attached by caller if a graph has to execute, instead
of remaining static"""

class GraphExecutionManager(object):
	"""manages context for entire execution process"""
	def __init__(self, graph:Graph):
		# super(GraphExecutionManager, self).__init__(graph)
		self.graph = graph

	def __enter__(self):
		"""set graph state"""
		self.graph.setState(Graph.State.executing)
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		"""reset graph state"""
		if exc_type:
			self.graph.setState(Graph.State.failed)
		self.graph.setState(Graph.State.neutral)


class GraphStateComponent(ObjectComponent):
	"""Graph with extra fuunctions to handle
	node execution"""
	parentType : Graph

	### region node execution ###
	def getExecPath(self, nodes):
		"""creates execution path from unordered nodes"""
		if nodes:
			newPath = ExecutionPath.getExecPathToNodes(self.parentObject, nodes)
		else:
			newPath = ExecutionPath.getExecPathToAll(self.parentObject)
		self.parentObject.log("exec path is {}".format(i.name for i in newPath.sequence))
		return newPath

	def executeNodes(self, nodes=None, index=-1):
		"""executes nodes in given sequence to given index"""

		execPath = self.getExecPath(nodes=nodes)
		self.parentObject.setState("executing")
		# enter graph-level execution state here
		with GraphExecutionManager(self.parentObject):
			for i in execPath.sequence:

				try:
					kSuccess = i.execStage(0)
					# enter and exit node-level execution state
					self.parentObject.log("all according to kSuccess")
				except RuntimeError("NOT ACCORDING TO KSUCCESS"):
					pass

		# exit graph-level execution
		self.parentObject.setState("neutral")
		self.parentObject.log("execution complete")

	def resetNodes(self, nodes=None):
		"""resets nodes to pre-executed state"""
		if not nodes:
			nodes = self.parentObject.nodes
		for i in nodes:
			i.reset()
		"""currently no support for specific order during reset, as in maya there
		is no need. however, it could be done"""

	def reset(self):
		self.resetNodes(self.parentObject.nodes)
		self.parentObject.setState(self.parentObject.State.neutral)

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

	def getActions(self) ->Tree:
		"""gather selected nodes and have option to execute them"""
		selNodes = self.parentObject.selectedNodes()
		execBranch = self.parentObject.baseActionTree("execute")
		execBranch("Selected nodes").value = partial(
			self.executeNodes, nodes=selNodes
		)
		execBranch("All nodes").value = partial(
			self.executeNodes
		)
		execBranch("All nodes").description = "rig it like you dig it"

		return self.parentObject.baseActionTree



	#endregion


