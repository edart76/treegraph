# base machinery for all visual nodes
from  __future__ import annotations
from tree import TreeWidget

from typing import List, Dict

from PySide2 import QtCore, QtWidgets, QtGui
from treegraph.node import GraphNode
#from edRig.tesserae.action import Action
from treegraph.ui import tilewidget

from treegraph.ui.style import *
from treegraph.ui.constant import nameBarHeight, settingsPadding
from treegraph.ui.delegate.attr import AttrDelegate
from treegraph.ui.delegate.knob import Knob

from treegraph.ui.lib import AllEventEater

"""
events are gathered from QGraphicsScene and view, 
passed through those objects,
THEN passed to the proxy widgets.

"""

class SettingsProxy(QtWidgets.QGraphicsProxyWidget):
	"""test for event filtering
	STILL doesn't receive events before view and scene"""



class NodeDelegate(QtWidgets.QGraphicsItem):
	""" now DIRECT link between node and tile,
	 sync used to start over entirely

	 """
	def __init__(self, parent=None, abstractNode:GraphNode=None,
	             ):
		super(NodeDelegate, self).__init__(parent)
		if not isinstance(abstractNode, GraphNode):
			raise RuntimeError("no abstractNode provided!")
		self.node = abstractNode
		self.settingsProxy = None
		self.settingsWidg : TreeWidget = None

		self.nameTag = tilewidget.NameTagWidget(self, abstractNode.name)
		self.classTag = QtWidgets.QGraphicsTextItem(
			self.node.__class__.__name__, self)

		#self.nameTag.installEventFilter(AllEventEater(self.nameTag))


		self.addSettings(self.node.settings )
		self.settingsWidg.expandAll()

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)


		self.attrBlocks = [AttrDelegate(parent=self,
		                                tree=self.node.inputRoot),
		                   AttrDelegate(parent=self,
		                                tree=self.node.outputRoot)] #type:List[AttrDelegate]

		self.actions = {}

		# set reference to this tile on abstractNode???????
		self.node.ui = self

		# appearance
		#self.width, self.height = self.getSize()
		self.entryHeight = 20
		self.colour = self.node.extras.get("colour", (50, 50, 120))
		self.borderColour = (200,200,250)
		textColour = QtGui.QColor(200, 200, 200)
		self.classTag.setDefaultTextColor(textColour)
		self.classTag.setPos(self.boundingRect().width(), 0)

		# resizing
		#self.width, self.height = self.getSize()
		#self.arrange()

	@property
	def width(self):
		return self.boundingRect().width()

	@property
	def height(self):
		return self.boundingRect().height()

	def makeConnections(self):
		self.node.nameChanged.connect(self.onNodeNameChange)
		self.nameTag.valueChanged.connect(self._onNameTagChange)

	@property
	def entries(self)->Dict[str, AttrDelegate]:
		"""full flat composite string address map of all items"""
		# entries = WeakValueDictionary()
		entries = {}
		for i in self.attrBlocks:
			entries.update(i.getEntryMap())
		return entries

	@property
	def knobs(self)->Dict[str, Knob]:
		"""return flat map of address : Knob object"""
		# knobs = WeakValueDictionary()
		knobs = {}
		for k, v in self.entries.items():
			knobs[k] = v.knob
		return knobs

	def arrange(self):
		for i in self.attrBlocks:
			i.arrange()
		y = nameBarHeight  # height of name and class tag

		self.attrBlocks[0].setPos(0, y)
		y += self.attrBlocks[0].boundingRect().height() + 7

		self.attrBlocks[1].setPos(self.boundingRect().width(), y)
		y += self.attrBlocks[1].boundingRect().height() + 7

		#y += 30
		#self.settingsWidg.resizeToTree()
		self.settingsProxy.setGeometry( QtCore.QRect(
			settingsPadding, y,
			max(self.settingsWidg.width(), self.width) - settingsPadding * 2 ,
		    self.settingsWidg.height() ) )

		self.getSize()

	def dragMoveEvent(self, event:QtWidgets.QGraphicsSceneDragDropEvent):
		"""test"""
		print("tile dragMoveEvent")
		return super(NodeDelegate, self).dragMoveEvent(event)


	def _onNameTagChange(self, widget, name):
		self.node.setName(name)

	def onNodeNameChange(self, branch, newName, oldName):
		self.nameTag.value = newName


	def getSize(self):
		"""
		calculate minimum node size.
		"""
		minRect = self.nameTag.boundingRect()
		minWidth = minRect.x() + 150
		#minWidth = minRect.x()
		minHeight = minRect.y() + 20

		for i in self.attrBlocks:
			if not i:
				continue
			minHeight += i.boundingRect().height() + 10

		minHeight += self.settingsProxy.rect().height()
		minHeight += settingsPadding * 2

		# self.width = minWidth
		# self.height = minHeight
		return minWidth, minHeight

	def boundingRect(self):
		minWidth, minHeight = self.getSize()
		return QtCore.QRect(0, 0, minWidth, minHeight)

	def paint(self, painter, option, widget):
		"""Paint the main background shape of the node"""
		painter.save()
		self.getSize()

		baseBorder = 1.0
		rect = QtCore.QRectF(0.5 - (baseBorder / 2),
							 0.5 - (baseBorder / 2),
							 self.width + baseBorder,
							 self.height + baseBorder)
		radius_x = 2
		radius_y = 2
		path = QtGui.QPainterPath()
		path.addRoundedRect(rect, radius_x, radius_y)
		painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 255), 1.5))
		painter.drawPath(path)

		rect = self.boundingRect()
		bg_color = QtGui.QColor(*self.colour)
		painter.setBrush(bg_color)
		painter.setPen(QtCore.Qt.NoPen)
		#painter.drawRoundRect(rect, radius_x, radius_y)
		painter.drawRect(rect)

		if self.isSelected():
			painter.setBrush(QtGui.QColor(*NODE_SEL_COLOR))
			painter.drawRoundRect(rect, radius_x, radius_y)

		label_rect = QtCore.QRectF(rect.left() + (radius_x / 2),
								   rect.top() + (radius_x / 2),
								   self.width - (radius_x / 1.25),
								   28)
		path = QtGui.QPainterPath()
		path.addRoundedRect(label_rect, radius_x / 1.5, radius_y / 1.5)
		painter.setBrush(QtGui.QColor(0, 0, 0, 50))
		painter.fillPath(path, painter.brush())

		border_width = 0.8
		border_color = QtGui.QColor(*self.borderColour)
		if self.isSelected():
			border_width = 1.2
			border_color = QtGui.QColor(*NODE_SEL_BORDER_COLOR)
		border_rect = QtCore.QRectF(rect.left() - (border_width / 2),
									rect.top() - (border_width / 2),
									rect.width() + border_width,
									rect.height() + border_width)
		path = QtGui.QPainterPath()
		path.addRoundedRect(border_rect, radius_x, radius_y)
		painter.setBrush(QtCore.Qt.NoBrush)
		painter.setPen(QtGui.QPen(border_color, border_width))
		painter.drawPath(path)
		painter.restore()

	def addSettings(self, tree):
		"""create a new abstractTree widget and add it to the bottom of node"""
		self.settingsProxy = SettingsProxy(self)

		topWidg = QtWidgets.QApplication.topLevelWidgets()[0]
		self.settingsWidg = TreeWidget(tree=tree)
		self.settingsProxy.setWidget(self.settingsWidg)
		# self.scene().addItem(self.settingsProxy)

		# connect collapse and expand signals to update size properly
		# self.settingsWidg.collapsed.connect( self._resizeSettings )
		# self.settingsWidg.expanded.connect( self._resizeSettings )

		return self.settingsWidg

	def getActions(self)->List[Action]:
		return self.node.getAllActions()

	def serialise(self):
		"""save position in view"""
		return {
			"pos" :	(self.pos().x(), self.pos().y()),
			}




