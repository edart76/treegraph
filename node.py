
"""atomic node in graph, based on tree structure
tree structure may eventually be based on graph
"""



from __future__ import annotations

import typing
from typing import Union, TYPE_CHECKING, Set, Callable, Type
from enum import Enum
from functools import partial

from tree import Tree, Signal

from treegraph.base import GraphNodeBase
from treegraph.constant import NodeState
from treegraph.datatype import DataTypes
from treegraph.attr import NodeAttr

if TYPE_CHECKING:
	from treegraph import Graph, GraphEdge



class NodeMeta(type):
	def __call__(cls, *args, **kwargs):
		ins = super(NodeMeta, cls).__call__(*args, **kwargs)
		ins.postInit()
		return ins


class GraphNode(Tree, GraphNodeBase,
                metaclass=NodeMeta
                ):
	"""node node managed by node graph
	interfaces with direct operations, and with UI"""

	sep = "."

	defaultName = "basicAbstract"
	realClass = None
	branchesInheritType = False

	# attach datatypes as class attribute
	DataTypes = DataTypes

	State = NodeState


	# physical coords of node in graph
	position = Tree.TreePropertyDescriptor("position", default=[0, 0])
	# execution state of node / graph
	state = Tree.TreePropertyDescriptor("state", default=NodeState.neutral)
	# is this node currently selected
	selected = Tree.TreePropertyDescriptor("selected", default=False)



	def __init__(self, name=None, graph=None,
	             uid=None):
		"""say no to spaghett
		"""
		super(GraphNode, self).__init__(name=name, treeUid=uid)

		self.state = self.State.neutral

		"""initialise attribute hierarchy"""
		self.addChild(NodeAttr(
			node=self, dataType=NodeAttr.DataTypes.Null,
		                              name="input"))
		self.addChild(NodeAttr(
			node=self, dataType=NodeAttr.DataTypes.Null,
		                              name="output"))
		self.addChild(Tree("settings"))

		# set signal breakpoints at settings and attr roots
		for i in (self.inputRoot, self.outputRoot, self.settings):
			i.setBreakTags( {"main"} )
			i.setReceivesSignals(True)


		# signals
		self.attrsChanged = Signal()
		self.attrValueChanged = Signal() # emit tuple of attrItem, value
		self.stateChanged = Signal()
		self.connectionsChanged = Signal()
		self.nodeChanged = Signal()
		self.wireSignals()


		"""right click actions for ui
		left as a tree to allow custom structuring when wanted"""
		self.baseActionTree = Tree(name="actions") #type:Tree[str, partial]

		# user override methods
		self.defineSettings()
		self.defineAttrs()


	@property
	def graph(self)->Graph:
		""""""
		return self.parent

	@property
	def inputRoot(self)->NodeAttr:
		return self("input")
	@property
	def outputRoot(self)->NodeAttr:
		return self("output")
	@property
	def settings(self)->Tree:
		return self("settings")

	@property
	def inEdges(self)->Set["GraphEdge"]:
		"""look up edges in graph"""
		return self.graph.nodeEdges(self, outputs=False)

	@property
	def outEdges(self) -> Set["GraphEdge"]:
		"""look up edges in graph"""
		return self.graph.nodeEdges(self, outputs=True)

	@property
	def edges(self)->Set["GraphEdge"]:
		return self.inEdges.union(self.outEdges)
	@property
	def history(self):
		return self.graph.getNodesInHistory(self)

	@property
	def future(self):
		return self.graph.getNodesInFuture(self)

	@property
	def directFuture(self)-> Set[GraphNode]:
		""" all nodes in this node's direct history
		might get a bit pricey but
		not a problem for now """
		return self.graph.adjacentNodes(self, future=True)

	@property
	def directHistory(self) -> Set[GraphNode]:
		""" all nodes in this node's direct history
		might get a bit pricey but
		not a problem for now """
		return self.graph.adjacentNodes(self, history=True)

	@property
	def data(self):
		""" returns a corresponding graph data slot
		works off uid
		abstractNodes only have access to data - graph may know more
		:rtype Tree """
		data = self.graph.getNodeMemoryCell(self)
		return data

	def wireSignals(self):
		"""sets up signal hierarchy"""
		intermediateSignals = [self.attrsChanged, self.stateChanged, self.connectionsChanged]
		for i in intermediateSignals:
			# connect everything to nodeChanged
			i.connect(self.nodeChanged)

		self.nodeChanged.connect(self.onNodeChanged)
		self.stateChanged.connect(self.onStateChanged)

	# signal-fired methods
	def onNodeChanged(self, *args, **kwargs):
		pass
	def onAttrsChanged(self, *args, **kwargs):
		pass
	def onStateChanged(self, *args, **kwargs):
		pass
	def onConnectionsChanged(self, *args, **kwargs):
		pass

	def initSettings(self):
		"""putting here as temp, this all needs restructuring"""
		self.addChild(Tree("settings", None))

	def setState(self, state:State):
		self.state = state
		self.stateChanged()


	@property
	def dataPath(self):
		return self.graph.dataPath + "/" + self.idTag

	@property
	def idTag(self):
		return self.name + "_" + str(self.uid)


	def log(self, message):
		"""if we implement proper logging replace everything here"""
		self.graph.log(message)

	# region override methods
	def postInit(self):
		"""called after any subclassed init is complete"""
		pass

	def defineAttrs(self):
		"""define the attribute pattern of a node"""
		#raise NotImplementedError
		pass

	def defineSettings(self):
		"""define the settings tree of a node, if needed"""
		pass

	def preExecution(self):
		"""run before execution"""
		self.setState(self.State.executing)
		pass

	def execute(self):
		"""define execution of a node
		override in subclasses"""
		pass

	def postExecution(self, excType:Type[Exception]=None, excVal=None, excTb=None):
		"""run after execution - passed the same exit arguments
		as context manager __exit__"""
		if excType:
			self.setState(self.State.failed)
			return
		self.setState(self.State.complete)
		pass


	# region execution
	def executionStages(self):
		"""defining multiple execution stages -
		for now only 1 is used"""
		return {
			"main" : (self.preExecution, self.execute, self.postExecution)
		}

	def execStage(self, stageIndex=0):
		"""handle pre-, main and post-execution functions on given stage"""
		key = tuple(self.executionStages().keys())[stageIndex]
		execFunctions = self.executionStages()[key]

		errorType, errorVal, errorTb = None, None, None
		preResult = execFunctions[0]()
		try:
			mainResult = execFunctions[1]()
		except Exception as e:
			errorType = e
		postResult = execFunctions[2](errorType, errorVal, errorTb)

	def execToStage(self, stageIndex=0):
		endIndex = stageIndex if stageIndex > -1 else (len(self.executionStages()) + stageIndex)
		for i in range(endIndex):
			self.execStage(i)





	def propagateOutputs(self):
		"""references the value of every output to that of every connected input"""
		for i in self.outEdges:
			i.dest[1].value = i.source[1].value

	def reset(self):
		if self.state != self.State.neutral:
			self.setState(self.State.neutral)
	#endregion

	# ATTRIBUTES
	@property
	def inputs(self):
		return self.inputRoot.allBranches()

	@property
	def outputs(self):
		#return {i.name : i for i in self.output.allBranches()}
		return self.outputRoot.allBranches()

	def addInput(self, name:str,

	             dataType=None, desc="", isArray=False,
	             parent: NodeAttr = None,
	             allowMultipleConnections=False,):
		parent = parent or self.inputRoot
		newAttr = parent.addAttr(name, dataType=dataType,
		                         default=None, desc=desc)
		return newAttr

	def addOutput(self, name:str,
	             dataType=None, desc="", isArray=False,
	              parent: NodeAttr = None,
	             allowMultipleConnections=False,
	              *args, **kwargs):
		parent = parent or self.outputRoot
		result = parent.addAttr(parent=parent, name=name, dataType=dataType,
		                    desc=desc, #default=default,
		                    #attrItem=attrItem,
		                      *args, **kwargs)
		return result


	def removeAttr(self, name, role="output", emit=True):
		if role == "output":
			attr = self.getOutput(name=name)
		else:
			attr = self.getInput(name=name)
		#attr.parent.removeAttr(name)
		attr.parent.remove(name)
		if emit: # for bulk attribute reordering call signal by hand
			self.attrsChanged()

	def getInput(self, name):
		return self.inputRoot.attrFromName(name)

	def searchInputs(self, match):
		return [i for i in self.inputs if match in i.name]

	def searchOutputs(self, match):
		return [i for i in self.outputs if match in i.name]

	def getOutput(self, name):
		return self.outputRoot.attrFromName(name)

	def connectableInputs(self):
		return self.inputRoot.getAllConnectable()

	def interactibleInputs(self):
		return self.inputRoot.getAllInteractible()

	def connectableOutputs(self):
		return self.outputRoot.getAllConnectable()

	def getConnectedInputs(self):
		inputs = self.inputRoot.allBranches()
		return [i for i in inputs if i.getConnections()]

	def getConnectedOutputs(self):
		outputs = self.outputRoot.allBranches()
		return [i for i in outputs if i.getConnections()]

	def clearOutputs(self, search=""):
		for i in self.outputs:
			if search in i.name or not search:
				self.removeAttr(i)

	def clearInputs(self, search=""):
		for i in self.inputs:
			if search in i.name or not search:
				self.removeAttr(i, role="input")

	# settings
	def addSetting(self, parent=None, entryName=None, value=None,
	               options=None, min=None, max=None):
		"""add setting entry to abstractTree"""
		parent = parent or self.settings
		branch = parent(entryName)
		if options == bool: options = (True, False)
		extras = {"options" : options,
		          "min" : min,
		          "max" : max}
		branch.extras = {k : v for k, v in extras.items() if v}
		branch.value = value

	# sets
	def addToSet(self, setName):
		self.graph.addNodeToSet(self, setName)

	def removeFromSet(self, setName):
		self.graph.removeNodeFromSet(self, setName)

	def getConnectedSets(self):
		return self.graph.getSetsFromNode(self)

	# actions
	def getActions(self)->Tree:
		"""return actions to display for this node
		when right-clicked
		only show up when selected
		"""
		return self.baseActionTree


	# io
	def serialise(self, includeAddress=False):
		"""converts node and everything it contains to dict"""
		serial = {
			"uid" : self.uid,
			"name" : self.name,
			"input" : self.inputRoot.serialise(),
			"output" : self.outputRoot.serialise(),
			"extras" : self.extras,
			"settings" : self.settings.serialise(),
			#"CLASS" : self.__class__.__name__
		}
		if self.real:
			serial["real"] = self.real.serialise()
			#serial["memory"] = self.real.memory.serialise()
		return serial

	# @classmethod
	# def fromDict(cls, fromDict, graph=None):
	# 	"""classmethod because returned node should be the right child class
	# 	so this is carnage"""
	# 	realClass = None
	# 	# try to load real component class from module
	#
	# 	if "real" in list(fromDict.keys()):
	# 		realDict = fromDict["real"]
	# 		realClass = loadObjectClass(realDict["objInfo"])
	#
	# 	if realClass:
	# 		newClass = cls.generateAbstractClass(realClass)
	# 	else:
	# 		newClass = cls
	#
	# 	# node reconstruction
	# 	newInst = newClass(graph)
	# 	newInst.uid = fromDict["uid"]
	# 	newInst.rename(fromDict["name"])
	#
	# 	# newInst.output = NodeAttr.fromDict(regenDict=fromDict["output"],
	# 	#                                            node=newInst)
	# 	newInst.outputRoot = NodeAttr.fromDict(regenDict=fromDict["output"])
	# 	newInst.outputRoot._node = newInst
	# 	# newInst.input = NodeAttr.fromDict(regenDict=fromDict["input"],
	# 	#                                           node=newInst)
	# 	newInst.inputRoot = NodeAttr.fromDict(regenDict=fromDict["input"])
	# 	newInst.inputRoot._node = newInst
	# 	newInst.settings = Tree.fromDict(fromDict["settings"])
	#
	# 	if "real" in list(fromDict.keys()):
	# 		realDict = fromDict["real"]
	# 		realInstance = realClass.fromDict(realDict, node=newInst)
	# 		newInst.setRealInstance(realInstance, define=False)
	# 		newInst.real.makeBaseActions()
	# 
	# 	return newInst

	def delete(self):
		"""deletes node node and real component
		edges will already have been deleted by graph"""
		self.inputRoot.delete()
		self.outputRoot.delete()
		super(GraphNode, self).delete()



if __name__ == '__main__':
	pass





