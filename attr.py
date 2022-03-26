
from __future__ import annotations

import copy
from enum import Enum, auto
import typing as T

from tree import Tree, Signal, TreeReference

from treegraph.base import GraphNodeBase
from treegraph.edge import GraphEdge
if T.TYPE_CHECKING:
	from treegraph.node import GraphNode
	from treegraph.graph import Graph


baseColour = (100, 100, 200)


"""TODO
work out proper system for array attributes,
generating new complex entries based on a schema
"""

class NodeAttr(Tree):
	""" trees to function as attributes for graph nodes
	"""

	sep = "."

	# available plug types
	class DataTypes(Enum):
		"""Redefine your own enums in inheriting
		programs"""
		Null = auto()
		Int = auto()
		Float = auto()
		String = auto()
		Dict = auto()

	# override in subclasses
	attrTypes = DataTypes #type: Enum

	# available hierarchy types
	class NodeAttrHTypes(Enum):
		Leaf = auto()
		Compound = auto()
		Array = auto()
		Root = auto()

	class Roles(Enum):
		Input = auto()
		Output = auto()


	branchesInheritType = False

	# property keys
	dataTypePKey = "dataType"
	isArrayPKey = "isArray"

	def __init__(self, name="blankName", dataType=DataTypes.Int,
	             isArray=False, desc="", default=None,
	             *args, **kwargs):
		super(NodeAttr, self).__init__(name=name, default=default)
		self.properties[self.dataTypePKey] = dataType
		self.properties[self.isArrayPKey] = isArray


		self._ui = None # link to ui representation if needed

		self.extras["desc"] = desc

		# colour for representation
		self.extras["colour"] = baseColour

		self.connectionChanged = Signal()

	@property
	def desc(self):
		return self.extras["desc"]

	@property
	def node(self)->"GraphNode":
		""" points to node which owns this attr
		:rtype GraphNode"""
		return next(filter(lambda x: isinstance(x, GraphNodeBase), self.trunk()))

	@property
	def attrRoot(self) ->NodeAttr:
		"""return root-level attribute"""
		return list(filter(lambda x: isinstance(x, GraphNodeBase), self.trunk(includeSelf=True)))[-1]

	def attrAddress(self)->T.List[str]:
		return self.relAddress(fromBranch=self.node)

	@property
	def role(self)->Roles:
		if "input" in self.attrAddress():
			result = self.Roles.Input
		if "output" in self.attrAddress():
			result = self.Roles.Output
		return result


	@property
	def graph(self)->"Graph":
		return self.node.graph

	@property
	def connections(self)->T.Set[GraphEdge]:
		"""edge register is maintained by Graph - this
		only indexes into it """
		return self.graph.attrEdgeMap[self]


	@property
	def dataType(self):
		return self.getProperty(self.dataTypePKey)

	# plug properties
	@property
	def plug(self):
		if self._plug is None:
			return None
		return self._plug()
	@plug.setter
	def plug(self, val):
		self._plug = val
		# not robust AT ALL, but enough for what we need


	@property
	def ui(self):
		return self._ui


	# ---- main methods ---

	@property
	def isArray(self):
		return self.getProperty(self.isArrayPKey)

	def isConnectable(self):
		#return self.hType == "leaf" or self.hType == "compound"
		return True

	def getConnections(self):
		return self.connections

	def isSimple(self):
		"""can attr be set simply by user in ui?"""
		simpleTypes = ["int", "float", "string", "enum", "colour", "boolean"]
		if any(self.dataType == i for i in simpleTypes):
			return True
		return False


	def connectedBranches(self):
		return [i for i in self.branches if i.getConnections()]

	def getAllLeaves(self):
		level = self.allBranches()
		return [i for i in level if i.isLeaf()]

	def getAllConnectable(self):
		level = self.allBranches() + [self]
		levelList = [i for i in level if i.isConnectable()]
		return levelList

	def getAllInteractible(self):
		level = self.allBranches() + [self]
		levelList = [i for i in level if i.isInteractible()]
		return levelList

	def addConnection(self, edge):
		"""ensures that input attributes will only ever have one incoming
		connection"""
		if edge in self.connections:
			#self.log("skipping duplicate edge on attr {}".format(self.name))
			print(( "skipping duplicate edge on attr {}".format(self.name) ))
			return
		if self.role == "output":
			self.connections.add(edge)
		else:
			self.connections.clear()
			self.connections.add(edge)

	def delete(self):
		""" removes this attribute and all children
		from other attrs' connections
		might be better to use signal system"""
		for edge in self.getConnections():
			other = edge.oppositeAttr(self)
			other.connections.remove(edge)
		for i in self.connectedBranches():
			i.delete()


	def getConnectedAttrs(self):
		"""returns only connected AbstractAttrs, not abstractEdges -
		this should be the limit of what's called in normal api"""
		if self.role == "input":
			return [i.sourceAttr for i in self.getConnections()]
		elif self.role == "output":
			return [i.destAttr for i in self.getConnections()]

	def attrFromName(self, name):
		#print "attrFromName looking for {}".format(name)
		results = self.search(name)
		if results: return results[0]
		else: return

	### user facing methods
	def addAttr(self, name:str, dataType=DataTypes.Int,
				default=None, desc="", *args, **kwargs):
		# check if attr of same name already exists
		newAttr = self.__class__(name=name, dataType=dataType,
							 default=default, role=self.role, desc=desc,
							 *args, **kwargs)
		self.addChild(newAttr)
		return newAttr

	def removeAttr(self, name):
		# first remove target from any attributes connected to it
		target = self.attrFromName(name)
		if not target:
			warn = "attr {} not found and cannot be removed, skipping".format(name)

			print(warn)
			return
		# what if target has children?
		for i in target.getChildren():
			target.removeAttr(i.name)
		for i in target.getConnections():
			conAttr = i["attr"]
			conAttr.connections = [i for i in conAttr.connections if i["attr"] != self]
		# remove attribute
		target.remove()

	# def remove(self, address=None):
	# 	""" also take care of removing """


	def copyAttr(self, name="new"):
		"""used by array attrs - make sure connections are clean
		AND NAMES ARE UNIQUE"""
		newAttr = copy.deepcopy(self)
		newAttr.name = name
		for i in newAttr.allBranches():
			i.connections = []
		return newAttr


	# ---- ARRAY BEHAVIOUR ----
	def setChildKwargs(self, name=None, desc="", dataType="0D", default=None,
					   extras=None):
		newKwargs = {}
		# this is disgusting i know
		newKwargs["name"] = name or self.childKwargs["name"]
		newKwargs["desc"] = desc or self.childKwargs["desc"]
		newKwargs["dataType"] = dataType or self.childKwargs["dataType"]
		self.childKwargs.update(newKwargs)


	def addFreeArrayIndex(self, arrayAttr):
		"""looks at array attr and ensures there is always at least one free index"""

	def matchArrayToSpec(self, spec=None):
		"""supplied with a desired array of names, will add, remove or
		rearrange child attributes
		this is because we can't just delete and regenerate the objects -
		edge references will be lost
		:param spec list of dicts:
		[ { name : "woo", hType : "leaf"}, ]
		etc
			"""

		# set operations first
		nameList = [i["name"] for i in spec]
		nameSet = set(nameList)
		childSet = {i.name for i in self.children}
		excessChildren = childSet - nameSet
		newNames = nameSet - childSet
		#print(( "newNames {}".format(newNames)))

		for i in excessChildren:
			self.remove(i)

		for i in newNames:
			#print(( "newName i {}".format(i)))
			nameSpec = [n for n in spec if n["name"] == i][0]
			kwargs = {}
			# override defaults with only what is defined in spec
			for k, v in self.childKwargs.items():
				kwargs[k] = nameSpec.get(k) or v
				# safer than update

			newAttr = NodeAttr(**kwargs)
			#self.children.append(newAttr)
			self.addChild(newAttr)