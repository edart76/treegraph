import pprint

from PySide2 import QtCore, QtWidgets, QtGui

from treegraph.glimport import *

from treegraph.ui.view import GraphView
from treegraph.ui.scene import GraphScene
from treegraph.graph import Graph
from treegraph.node import GraphNode, NodeAttr

from treegraph.tesserae.graphtabwidget import GraphTabWidget


def setStyleFile(widget, filePath=r"../ui/style/dark/stylesheet.qss"):
	stylePath = filePath
	settingFile = QtCore.QFile(stylePath)
	settingFile.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
	stream = QtCore.QTextStream(settingFile)
	widget.setStyleSheet(stream.readAll())


class TesseraeWidget(QtWidgets.QWidget):
	"""top level window for Tesserae application
	holds master register of loaded paths and graphs
	"""

	appName = "tesserae"

	graphsChanged = QtCore.Signal(dict)

	def __init__(self, parent=None):
		super(TesseraeWidget, self).__init__(parent)

		#self.graphs = WeakValueDictionary() # {uuid : graph }

		self.graphIndex = Tree("tessGraphIndex")
		topBranch = Graph.globalTree(self.appName, create=True)

		self.setObjectName("tesserae")
		self.setWindowTitle("tesserae")

		# make these dockable eventually
		self.tabWidgets = [GraphTabWidget(parent=self)]
		self.makeLayout()
		self.makeSignals()

	def makeSignals(self):
		for i in (Graph.globalTree.nameChanged,
		          Graph.globalTree.valueChanged,
		          Graph.globalTree.structureChanged,):
			i.connect(self.onRootGraphsChanged)
		self.graphsChanged.connect(self.onRootGraphsChanged)

	def makeLayout(self):
		vl = QtWidgets.QVBoxLayout()
		vl.addWidget(self.tabWidgets[0])
		vl.setContentsMargins(0, 0, 0, 0)
		self.setLayout(vl)

	def onRootGraphsChanged(self, *args, **kwargs):
		"""a change has been made to the structure of available
		graphs - regenerate uuid tree"""
		self.buildSelectorTree()

	def addRootGraph(self, graph:Graph):

		Graph.addGlobalRoot(graph, (self.appName, graph.name))
		graph.structureChanged.connect(lambda x: self.graphsChanged.emit({}))
		graph.nameChanged.connect(lambda x: self.graphsChanged.emit({}))
		# self.graphsChanged.emit({})
		return graph

	def rootGraphs(self)->Ty.List[Graph]:
		"""all top-level graphs"""
		topBranch = Graph.globalTree(self.appName)
		# print("globals")
		# print(Graph.globalTree.display())
		return list(filter(None, (i.value for i in topBranch.branches)))

	def availableGraphTree(self)->Tree:
		"""return tree composed of all top-level graphs, and
		all their branches"""
		baseTree = Tree("availableGraphs")
		# print("root graphs")
		#print(self.rootGraphs())
		for i in self.rootGraphs():
			#print("subs", i.allSubGraphs())
			for branch in i.allSubGraphs(includeSelf=True):
				#print("")
				#print("address", branch.address(includeSelf=True), branch)
				#baseBranch = baseTree(branch.address(includeSelf=True), create=True)
				#print("baseBranch", baseBranch)
				baseTree(branch.address(includeSelf=True), create=True).value = branch.uid

				#raise
		#print("end available", baseTree.display())
		return baseTree



	def removeRootGraph(self, graph:Graph):
		topBranch = Graph.globalTree(self.appName, create=True)
		topBranch.remove(graph)
		return graph

	def buildSelectorTree(self):
		"""build separate tree for addresses into graphs
		identical except it provides stable root reference
		"""
		#print("build selector tree")
		#print(self.availableGraphTree().display())
		self.graphIndex.clear()
		for graph in self.availableGraphTree().branches:
			self.graphIndex.addChild(graph.copy())



	def graphFromSelectorBranch(self, selectorBranch:Tree):
		"""no idea if this is the place to put this
		given the stripped down selector branch, retrieve
		the correct graph from among those loaded"""

		# get graph from selected uid
		retrieveBranch = Graph.byUid(selectorBranch.value)
		if not retrieveBranch:
			raise RuntimeError("uid {} not found in root graph uid register".format(selectorBranch.value))
		return retrieveBranch


	# region io functions
	def serialiseGraph(self, graph:Graph):
		"""return serialised dict for the given graph"""
		return graph.serialise()

	def startup(self):
		graph = self.addRootGraph(Graph("newGraph"))
		self.tabWidgets[0].addGraph(graph)

		#print("start index")
		#print(self.graphIndex.display())



def testWindow():
	#return

	from tree.test.constant import midTree
	#return



	widg = TesseraeWidget()
	setStyleFile(widg)

	widg.startup()

	# retrieve root graph and add node
	newGraph = widg.rootGraphs()[0]
	newGraph.addNode(GraphNode("newNode"))

	from treegraph.example import pluginnode
	return widg



def testWithApp():
	import sys
	app = QtWidgets.QApplication(sys.argv)

	tessWidg = testWindow()

	win = QtWidgets.QMainWindow()
	tessWidg.setParent(win)
	win.setCentralWidget(tessWidg)

	win.show()
	win.setFixedSize(1000, 600)


	sys.exit(app.exec_())


if __name__ == "__main__":
	from treegraph.example import pluginnode
	w = testWindow()





