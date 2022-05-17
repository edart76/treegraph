
"""base setup for a topological graph, with nodes based on trees
"""

# manages connectivity and execution order of a dag graph
from __future__ import annotations
from typing import List, Set, Dict, Callable, Tuple, Sequence, Union, TYPE_CHECKING
import typing as T
import typing as Ty

from functools import partial

import pprint, inspect, itertools
from weakref import WeakSet, WeakValueDictionary
from collections import defaultdict
from functools import partial
from enum import Enum

from tree import Tree, Signal

from treegraph.node import GraphNode
from treegraph.attr import NodeAttr
from treegraph.edge import GraphEdge
from treegraph.group import NodeSet

from treegraph.exepath import ExecutionPath


#from treegraph.plugin import defaultNodes

from treegraph.catalogue import ClassCatalogue

from treegraph.functionset import GraphFunctionSet

class Graph(
	#Tree
	GraphNode # maybe a bad idea
            ):
	"""setting out the inheritance from Tree
	abstractNodes and child graphs are BRANCHES.

	taking inspiration from houdini -
	Graph indexing up to nodes done using "/"
	Node indexing within attributes done with "."

	node groups might be value of branch 'groups'
	"""

	sep = "/"

	# register of all active graphs to async lookup and interaction
	globalTree = Tree("globalRoots")

	branchesInheritType = False


	class EdgeEvents(Enum):
		added = "added"
		removed = "removed"

	class SetEvents(Enum):
		added = "added"
		removed = "removed"

	class SaveMode(Enum):
		"""options between saving entire graph to single file,
		or each graph and node to a separate file in a folder hierarchy"""
		singleFile = "singleFile"
		separateFiles = "separateFiles"

	# reserved names for graph components,
	# not to be used for node names
	reservedKeys = ["nodeGroups", "nodeMemory", "edges"]

	# default node classesToReload to register
	#nodeClasses = []

	#registeredNodeClasses = {} # type: T.Dict[str, T.Type[GraphNode]]

	# ONE NODE CATALOGUE PER GRAPH CLASS
	# could do it per-instance, but we will not
	classCatalogue = ClassCatalogue(classPackagePaths=[],
	                                  baseClasses={GraphNode})

	#functionset = GraphFunctionSet()

	functionSetCls = GraphFunctionSet
	functionSet: GraphFunctionSet = Tree.TreePropertyDescriptor(
		key="functionSet", default=None, inherited=True)

	def __init__(self,
	             name="main",
	             uid=None,
	             ):
		super(Graph, self).__init__(name=name, uid=uid)
		#self.edges = set() # single source of truth on edges

		def _edgeItemFactory():
			return WeakSet()
		self.attrEdgeMap = defaultdict(_edgeItemFactory) #type: Dict[NodeAttr, Set[GraphEdge]]

		#self.selectedNodes = []
		self.setProperty("nodeSets", {})
		self.setProperty("edges", set())

		self.transforms = {} # map of node


		# signals
		# edgesChanged signature : edge object, event type
		self.edgesChanged = Signal()
		self.nodeChanged = self.structureChanged
		# nodeSetsChanged signature : node set, event type
		self.nodeSetsChanged = Signal()
		self.wireSignals()

		self._isAcyclic = True

	@classmethod
	def newRootGraph(cls, name:str)->Graph:
		"""add a new global top-level graph"""
		newGraph = cls(name=name)
		namespace = ("graph", )
		cls.addGlobalRoot(newGraph, namespace)
		return newGraph

	def allSubGraphs(self, includeSelf=True)->Ty.List[Graph]:
		"""return only branches that are graphs in their own right"""
		if not self.branches:
			return []
		subgraphs = [self] if includeSelf else []
		for i in self.branches:
			if not isinstance(i, Graph):
				continue
			subgraphs.append(i)
			subgraphs.extend(i.allSubGraphs())
		return subgraphs

	# graph attributes
	@property
	def nodeMemory(self):
		return self("nodeMemory")

	@property
	def isAcyclic(self)->bool:
		return self._isAcyclic
	def setAcyclic(self, state:bool):
		self._isAcyclic = state

	@property
	def edges(self)->Set[GraphEdge]:
		return self.getProperty("edges")

	@property
	def nodeSets(self)->Dict[str, NodeSet]:
		return self.getProperty("nodeSets")

	@property
	def nodes(self)->List[GraphNode]:
		"""DOES NOT exclude child graphs"""
		return [i for i in self.branches if isinstance(i, GraphNode)
		        ]

	@property
	def subGraphs(self)->List[Graph]:
		"""return all direct branches that are graphs in their own right"""
		return [i for i in self.branches is isinstance(i, Graph)]

	@property
	def nonGraphNodes(self)->Set[GraphNode]:
		return set(self.nodes) - set(self.subGraphs)

	@property
	def nodeMap(self)->Dict[str, GraphNode]:
		"""returns map of {node name : node }"""
		return {i.name : i for i in self.branches if isinstance(i, GraphNode)
		        }

	def log(self, message):
		print(message)

	def setAsset(self, assetItem):
		self._asset = assetItem

	def clearSession(self):
		#self.nodeGraph.clear()
		self.edges.clear()
		for i in self.branches:
			if i.name in self.reservedKeys:
				continue
			# clear all nodes
			self.remove(i.name)

	# signals
	def onNodeAttrsChanged(self, node):
		"""checks if any connections to node are now invalid"""
		legal = self.checkNodeConnections(node)
		if not legal:
			self.edgesChanged()
		self.nodeChanged(node)

	def wireSignals(self):
		"""in case signal hierarchy is needed -
		avoid this if possible"""


	#region node class processing
	@property
	def registeredNodeClasses(self)->Dict[str, type]:
		"""dict of { class name, class object } for nodes"""
		return {i.__name__ : i for i in  self.classCatalogue.classes}

	@classmethod
	def registerNodeClasses(cls,
	                        toRegister:T.List[T.Type[GraphNode]]):
		"""updates class catalogue with given classes"""
		cls.classCatalogue.registerClasses(toRegister)

	@property
	def registeredClassNames(self):
		return list(self.registeredNodeClasses.keys())

	# endregion

	@property
	def knownUIDs(self):
		return [i.uid for i in self.nodes]

	@property
	def knownNames(self):
		# return [i["node"].name for i in list(self.nodeGraph.values())]
		return [i.name for i in self.nodes]

	### region node creation and deletion

	def createNode(self, nodeType="", name="", add=True)->GraphNode:
		"""accepts string of node class name to create
		does not directly add node to graph
		"""

		if not nodeType in self.registeredClassNames:
			raise RuntimeError("nodeType "+nodeType+" not registered in graph")
		nodeClass = self.registeredNodeClasses[nodeType]
		newInstance = nodeClass(name=name or nodeClass.__name__,
		                          )
		if add:
			self.addNode(newInstance)
		return newInstance


	def addNode(self, node:GraphNode)->T.Union[None, GraphNode]:
		"""adds a node to the active graph"""
		# add node as branch
		self.addChild(node)
		return node

	def deleteNode(self, node:GraphNode):
		if self.state != self.State.neutral:
			return False
		for i in node.edges:
			self.deleteEdge(i)
		for i in self.nodeSets.keys():
			self.removeNodeFromSet(node, i)

		self.remove(node,
		            #delete=True
		            )
		# node.delete()
		# del node

	#endregion

	### region node querying
	def nodesFromName(self, name):
		"""may by its nature return multiple nodes"""
		return [i for i in self.nodes if i.name == name]

	def nodeFromUID(self, uid):
		# return self.nodeGraph[uid]["node"]
		return [i for i in self.nodes ]

	def getNode(self, node)->Union[GraphNode, Dict]:
		"""returns an GraphNode object from
		an GraphNode, node name, node UID, or NodeAttr(?)
		:returns GraphNode"""
		if isinstance(node, GraphNode):
			node = node
		elif isinstance(node, str):
			node = self.nodesFromName(node)[0] # don't do this
		elif isinstance(node, int):
			node = self.nodeFromUID(node)
		elif isinstance(node, NodeAttr):
			node = node.node
		elif isinstance(node, dict) and "node" in list(node.keys()): # node entry
			node = node["node"]
		# node is now absolutely definitely a node
		return node


	#endregion

	### region adding edges
	def addEdge(self, sourceAttr:NodeAttr, destAttr:NodeAttr, newEdge=None):
		"""adds edge between two attributes
		DOES NOT CHECK LEGALITY
		edges in future should not use bidirectional references -
		only inputs know their own drivers - outputs know nothing
		"""
		if self.state != self.State.neutral:
			print("graph state is ", self.state, "skipping")

			return False

		self.log( "")
		self.log( " ADDING EDGE")
		newEdge = newEdge or GraphEdge(
			source=sourceAttr, dest=destAttr, graph=self)

		# add edge to master edge set
		self.edges.add(newEdge)
		self.attrEdgeMap[sourceAttr].add(newEdge)

		# remove existing dest connections
		self.attrEdgeMap[destAttr].clear()
		self.attrEdgeMap[destAttr].add(newEdge)
		self.edgesChanged(newEdge, self.EdgeEvents.added)
		return newEdge


	def deleteEdge(self, edge):
		if self.state != self.State.neutral:
			print("graph state is not neutral, skipping")
			return False
		# in theory this should be it
		self.edges.remove(edge)
		self.edgesChanged(edge, self.EdgeEvents.removed)
		print("graph deleteEdge complete")
		return


	def nodeEdges(self, node:GraphNode, outputs=False,
	              all=False)->Set[GraphEdge]:
		"""return either edges for either inputs or outputs
		could have done this directly on node object
		but seems easier to follow this way """
		if all:
			return self.nodeEdges(node, outputs=True).union(
				self.nodeEdges(node, outputs=False)	)
		# edges = WeakSet()
		edges = set()
		tree = node.outputRoot if outputs else node.inputRoot
		for i in tree.allBranches():
			edges.update(self.attrEdgeMap[i])
		return edges

	def adjacentNodes(self, node, future=True, history=True)->Set[GraphNode]:
		"""return direct neighbours of node"""
		# nodes = WeakSet()
		nodes = set()
		if future:
			for i in self.nodeEdges(node, outputs=True):
				nodes.add(i.destAttr.node)
		if history:
			for i in self.nodeEdges(node, outputs=False):
				nodes.add(i.sourceAttr.node)
		return nodes

	# endregion



	### region CONNECTIVITY AND TOPOLOGY ###
	def getNodesInHistory(self, node):
		"""returns all preceding nodes"""
		return self.getInlineNodes(node, history=True,
		                           future=False)

	def getNodesInFuture(self, node):
		"""returns all proceeding nodes"""
		return self.getInlineNodes(node, history=False,
		                           future=True)

	def getCombinedHistory(self, nodes):
		"""returns common history between a set of nodes"""
		history = set()
		for i in nodes:
			# history = history.union(i.history)
			history.update(self.getNodesInHistory(i))
		return history

	def getCombinedFuture(self, nodes):
		"""returns common future between a set of nodes"""
		future = set()
		for i in nodes:
			future.update(self.getNodesInFuture(i))
		return future

	def getInlineNodes(self, node:GraphNode, history=True, future=True,
	                   )->Set[GraphNode]:
		"""gets all nodes directly in the path of selected node
		forwards and backwards is handy way of working out islands
		can't work out how to factor out the copying"""
		inline = set()
		if future:
			for n in self.adjacentNodes(node, history=False, future=True):
				inline.add(n)
				inline.update(self.getInlineNodes(
						n, history=False, future=True))
		if history:
			for n in self.adjacentNodes(node, history=True, future=False):
				inline.add(n)
				inline.update(self.getInlineNodes(
						n, history=True, future=False))
		return inline

	def getContainedEdges(self, nodes=None):
		"""get edges entirely contained in a set of nodes"""
		nodes = self.getNodesBetween(nodes, include=False)
		edges = set()
		for i in nodes:
			nodeEdges = self.nodeEdges(i, outputs=True).union(
				self.nodeEdges(i, outputs=False))
			edges = edges.union(nodeEdges)
			# imperfect - contained nodes may have escaping connections
		return edges

	def getSeedNodes(self):
		"""get nodes with no history
		do not trust them"""
		seeds = set()
		for i in self.nodes:
			# if not i.history:
			if not self.nodeEdges(i, outputs=False):
				seeds.add(i)
		return seeds

	def getEndNodes(self):
		"""get nodes with no future
		pity them"""
		lost = set()
		for i in self.nodes:
			if not i.future: # i know the feeling
				lost.add(i) # don't cry, it doesn't help
		return lost # things might not get better
		# but they can't get worse


	def checkLegalConnection(self, source, dest):
		"""checks that a connection wouldn't undermine DAG-ness"""
		# if self.state != self.State.neutral: # graph is executing
		# 	return False
		if source.node is dest.node: # same node
			self.log("put some effort into it for god's sake")
			return False
		if self.isAcyclic:
			if source in source.node.inputs or dest in dest.node.outputs:
				self.log("attempted connection in wrong order")
				return False
			elif source.node in dest.node.future:
				self.log("source node in destination's future")
				return False
			elif dest.node in source.node.history:
				self.log("dest node in source's past")
				return False
		return True

	def checkNodeConnections(self, node):
		"""called whenever attributes change, to check there aren't any
		dangling edges"""
		removeList = []
		for i in node.edges:
			if not any([n in node.outputs + node.inputs for
						n in [i.sourceAttr, i.destAttr]]):
				removeList.append(i)

		if removeList:
			for i in removeList:
				self.deleteEdge(i)
				#self.edgesChanged()
			return False # going for semantics here
		return True



	def getNodesBetween(self, nodes:List=None, include=True):
		"""get nodes only entirely contained by selection
		include sets whether to return passed nodes or not
		return node items"""
		starters = set(self.getNode(i) for i in nodes)
		for i in starters:
			#""" do fancy topology shit """
			"""get all inline nodes for all search nodes
			if any node appears only in search history or only in search
			future,	cannot be contained. """

		allHistory = self.getCombinedHistory(starters)
		allFuture = self.getCombinedFuture(starters)

		betweenSet = allHistory.intersection(allFuture) # gg easy ????

		if include:
			betweenSet = betweenSet.union(nodes)
		else:
			betweenSet = betweenSet.difference(nodes)

		return betweenSet

	def orderNodes(self, nodes:Set[GraphNode], dfs=True)\
			->List[GraphNode]:
		""" sort nodes in order - assumes all nodes are connected
		if dfs, do depth-first, else b r e a d-first """
		path = ExecutionPath.getExecPathToNodes(self, nodes)
		return sorted(list(nodes), key=lambda x: x.index)

	def getLongestPath(self, seeds=List[GraphNode],
	                   ends=List[GraphNode]):
		"""Return the longest continuous path of nodes
		between ends given
		SUPER inefficient but we're not going to start caring now
		"""
		maxPath = set()
		for pair in itertools.product(seeds, ends):
			path = self.getNodesBetween(pair) or set()
			if len(path) > len(maxPath):
				maxPath = path
		return self.orderNodes(maxPath)


	def getIslands(self, nodes:Sequence[GraphNode]=None)\
			->Dict[int, Set[GraphNode]]:
		""" Return sets of totally disjoint nodes
		"""
		toTest = set(nodes or self.nodes)
		regions = defaultdict(set)
		index = 0
		while toTest:
			seed = toTest.pop()
			island = {seed}
			found = 0
			for node in self.getInlineNodes(seed):
				# has node already been found
				if node not in toTest:
					for n in island:
						regions[node.index].add(n)
					found = 1
					break
				toTest.remove(node)
				island.add(node)
			if found:
				continue

			regions[index].update(island)
			index += 1
		return regions

	#endregion




	### region node sets
	@property
	def nodeSetNames(self):
		return list(self.nodeSets.keys())

	def addNodeSet(self, name):
		self.nodeSets[name] = NodeSet(name)
		self.nodeSetsChanged()

	def getNodeSet(self, name):
		if not name in self.nodeSets:
			nodeSet = self.addNodeSet(name)
		return self.nodeSets[name]

	def addNodeToSet(self, node, setName):
		"""adds node to set - creates set if it doesn't exist
		:param node : GraphNode
		:param setName : str"""
		origSet = self.nodeSets.get(setName)
		if not origSet:
			self.nodeSets[setName] = NodeSet(name=setName)
		self.nodeSets[setName].add(node)

	def removeNodeFromSet(self, node, setName):
		""":param node : GraphNode
		:param setName : str"""
		targetSet = self.nodeSets.get(setName)
		if not targetSet:
			# i aint even mad
			self.log("target set {} not found".format(setName))
			return
		if not node in targetSet:
			# you aint even mad
			self.log("target node {} not in set {}".format(node.name, setName))
			return
		targetSet.remove(node)


	def getNodesInSet(self, setName):
		nodes = set()
		targetSet = self.nodeSets.get(setName)
		if targetSet:
			nodes = {i for i in targetSet}
		return nodes

	def getSetsFromNode(self, node):
		node = self.getNode(node)
		sets = set()
		for i in self.nodeSets.items():
			if node in i[1]:
				sets.add(i)
	# endregion

	### region node memory
	def getNodeMemoryCell(self, node):
		""" retrieves or creates key in memory dict of
		uid : {
			name : node name,
			data : node memory """

		uid = self.getNode(node).uid
		return self.nodeMemory.get(uid) or self.makeMemoryCell(node)

	def makeMemoryCell(self, node):
		node = self.getNode(node)
		cell = self.nodeMemory(node.uid)
		cell["name"] = node.name
		cell("data")

		return cell
	# endregion

	#region ui integration
	def selectedNodes(self)->T.List[GraphNode]:
		return [i for i in self.nodes if i.selected]

	#endregion

	# region serialisation and regeneration
	def serialise(self):
		"""oof ouchie"""
		graph = {"nodes" : {},
		         "edges" : [],
		         "name" : self.name,
		         "memory" : self.nodeMemory.serialise(),
		         }
		for uid, entry in self.nodeGraph.items():
			graph["nodes"][uid] = entry["node"].serialise()
			# don't worry about directHistory and directFuture - these will be reconstructed
			# from edges
		graph["edges"] = [i.serialise() for i in self.edges]
		graph["nodeSets"] = {k : [i.name for i in v] for k, v in self.nodeSets.items()}
		# add another section for groupings when necessary

		return graph

	@staticmethod
	def fromDict(regen:dict):
		"""my bones"""

		newGraph = Graph(name=regen["name"]) # parent will be tricky
		# regen memory
		memory = Tree.fromDict(regen["memory"])
		newGraph.addChild(memory, force=True)

		for uid, nodeInfo in regen["nodes"].items():
			newNode = GraphNode.fromDict(nodeInfo, newGraph)
			newNode.uid = uid
			newGraph.addNode(newNode)
		for i in regen["edges"]:
			newEdge = GraphEdge.fromDict(i, newGraph)
			newGraph.addEdge(sourceAttr=newEdge.sourceAttr,
			                 destAttr=newEdge.destAttr, newEdge=newEdge)
		for k, v in regen["nodeSets"]:
			newGraph.nodeSets[k] = set([newGraph.getNode(n) for n in v])
		return newGraph

	# endregion

	### initial startup when tesserae is run for the first time
	@classmethod
	def startup(cls, name="main")->Graph:
		"""returns a fresh graph object"""
		# do other stuff if necessary
		graph = cls(name=name)

		# initialise function set
		graph.functionSet = graph.functionSetCls(rootGraph=graph)

		return graph


