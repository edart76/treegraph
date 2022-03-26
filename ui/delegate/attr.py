
import typing as T

from PySide2 import QtWidgets, QtGui, QtCore

from tree import Tree
from treegraph import NodeAttr
from treegraph.ui import tilewidget
from treegraph.ui.constant import entryHeight
from treegraph.ui.delegate.knob import Knob


class AttrDelegate(QtWidgets.QGraphicsRectItem):
	"""testing live autonomous tracking of tree object
	feels very weird not to have a master sync function
	 """

	treeKeys = ("name", "dataType", "extras", "role", "depth")


	def __init__(self, parent=None, tree:NodeAttr=None,
	             text=True, recurse=True):
		if not tree:
			raise RuntimeError("no attrItem supplied!")
		super(AttrDelegate, self).__init__(parent)

		# lambdas to lookup on tree, to make live
		self.tree = tree
		tree.structureChanged.connect(self.onStructureChanged)

		# widget support if it ever comes back
		self.widg = None
		self.label = None
		self.knob = None

		# overridden later by arrange()
		if tree.isConnectable():
			self.knob = Knob(self, tree=self.tree)

		# appearance
		# base visual dimensions
		self.edgePad = 5
		self.unitHeight = entryHeight

		self.setToolTip(self.tree.desc)
		self.text = QtWidgets.QGraphicsTextItem(self.tree.name, self)
		#self.text.adjustSize()
		self.text.setDefaultTextColor(QtCore.Qt.lightGray)
		if not text:
			self.text.setVisible( False )

		self.pen = QtGui.QPen()
		self.brush = QtGui.QBrush()
		self.setPen(self.pen)
		self.setBrush(self.brush)

		self.children = {}
		self.setRect(0,0,
		             self.edgePad,
		             self.unitHeight)
		if recurse:
			for i in tree.branches:
				self.addChild(i)
		self.arrange()

	#("name", "dataType", "extras", "role", "depth")
	@property
	def name(self):
		return self.tree.name
	@property
	def dataType(self):
		return self.tree.dataType
	@property
	def extras(self):
		return self.tree.role
	@property
	def depth(self):
		return self.tree.depth
	@property
	def role(self):
		return self.tree.role

	def boundingRect(self):
		base = super(AttrDelegate, self).boundingRect()
		height = base.height() + sum(
			i.boundingRect().height() for i in self.children.values())
		return QtCore.QRect(base.left(), base.top(),
		                    base.width(), height)

	@property
	def width(self):
		return self.boundingRect().width()
	@property
	def height(self):
		return self.boundingRect().height()


	def onStructureChanged(self, branch, parent, code:Tree.StructureEvents ):
		"""test for autonomous distributed tracking
		of tree structure instead of in
		master sync method """

		if not parent is self.tree:
			return
		if code == Tree.StructureEvents.branchAdded:
			self.addChild(branch)
		elif code == Tree.StructureEvents.branchRemoved:
			self.removeChild(branch)
		self.arrange()


	def addChild(self, branch:Tree):
		"""bit weird to accept a tree object
		but I don't care anymore"""
		entry = AttrDelegate(
			parent=self, tree=branch,
		)
		self.children[branch] = entry
		return entry

	def removeChild(self, branch:Tree):
		entry = self.children[branch]
		self.scene().removeItem(entry)
		self.children.pop(branch)


	def onConnectionMade(self):
		"""disable widget if it exists"""
		if self.widg and self.role == "input":
			self.widg.disable()

	def onConnectionBroken(self, dest):
		"""disable widget if it exists"""
		if self.widg and self.role == "input":
			self.widg.enable()


	def getEntryMap(self):
		""" returns FLAT map of {address : entry} for all child entries """
		# entryMap = {self.attr.stringAddress() : self}
		entryMap = {}
		entryMap[self.tree.stringAddress()] = self
		for i in self.children.values():
			entryMap.update(i.getEntryMap())
		return entryMap


	def arrange(self, parentWidth=None, depth=0, n=0, d=0):
		"""recursively lay out tree structure
		 """
		# depth first
		childEntries = list(self.children.values())
		for i in childEntries:
			i.arrange()

		# main param values
		depth = self.tree.depth
		iSide = int(self.role == NodeAttr.Roles.Output)
		f = -1 if self.role == NodeAttr.Roles.Output else 1
		y = (self.tree.index() + 1) * self.unitHeight
		x = (depth - 1) * 10 * f
		mainWidth = self.rect().width()
		limitX = mainWidth

		#self.setPos(x, y)
		self.setPos(0, y)
		# move knob
		knobWidth = self.knob.boundingRect().width() / 2.0
		self.knob.setPos(limitX * iSide - knobWidth / 2.0, 0)

		textBox = self.text.boundingRect()
		textWidth = textBox.width()
		textX = limitX * iSide + knobWidth * 2 * f - textWidth * iSide
		self.text.setPos(textX, 1)


		height = sum([i.rect().height() for i in childEntries])



		if self.label:
			labelRect = self.label.boundingRect()
			self.label.setPos(0, 0)

		# place text outside node
		#
		if self.role == NodeAttr.Roles.Output:
			x = mainWidth
			textX = mainWidth - textWidth

		else:
			# position knob on left
			x = x - 20
			textX = x
			textX += self.knob.boundingRect().width()
			#textX = textWidth * -1
			#textX = 20
		knobY = self.height /2.0 - self.knob.boundingRect().height() / 2.0




	def makeWidg(self):
		name = self.tree.name
		value = self.tree.value
		if self.dataType == "int":
			widg = tilewidget.NodeIntSpinbox(parent=self, name=name,
			                                  value=value, min=self.extras.get("min"),
			                                  max=self.extras.get("max"))
		elif self.dataType == "float":
			widg = tilewidget.NodeFloatSpinbox(parent=self, name=name,
			                                  value=value, min=self.extras.get("min"),
			                                  max=self.extras.get("max"))
		elif self.dataType == "enum":
			widg = tilewidget.NodeComboBox(parent=self, name=name,
			                                value=value,
			                                items= self.extras.get("items"))
		elif self.dataType == "string":
			widg = tilewidget.NodeLineEdit(parent=self, name=name,
			                                text=value)
		elif self.dataType == "boolean":
			widg = tilewidget.NodeCheckBox(parent=self, name=name,
			                                state=value)
		elif self.dataType == "colour":
			widg = tilewidget.NodeColourBox(parent=self, name=name,
			                                 value=value)
		else:
			raise RuntimeError("datatype {} not associated with tileWidget".format(
				self.dataType))
		return widg


class PassthroughAttrDelegate(AttrDelegate):
	"""same as above but for pass-through attributes
	extraAttr MUST be an output"""

	def __init__(self, extraAttr=None, *args, **kwargs):
		"""input attr still informs the main entry body"""
		if extraAttr.role != "output":
			raise RuntimeError("passthrough tileEntry called incorrectly,"
			                   "extraAttr must be output")
		super(PassthroughAttrDelegate, self).__init__(*args, **kwargs)
		if self.tree.role != "input":
			raise RuntimeError("passthrough tileEntry called incorrectly,"
			                   "first attr must be input")
		self.extraAttr = extraAttr
		self.role = "passthrough"

		self.extraText = QtWidgets.QGraphicsTextItem(self.extraAttr.name, self)
		self.extraText.adjustSize()

		self.extraKnob = Knob(self, tree=self.extraAttr)

		self.arrangeExtra()


	def arrangeExtra(self):
		"""someday go back and refactor this, but for now it's fine"""

		# place text outside node
		textBox = self.extraText.boundingRect()
		textWidth = textBox.width() + 30
		mainWidth = self.rect().width()

		x = mainWidth
		textX = mainWidth + 30
		knobY = self.height /2.0 - self.extraKnob.boundingRect().height() / 2.0
		self.extraKnob.setPos(x, knobY)
		self.extraText.setPos(textX, 1)