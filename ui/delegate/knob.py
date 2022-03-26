from PySide2 import QtWidgets, QtGui, QtCore
from treegraph import NodeAttr
from treegraph.ui.constant import baseColour


class Knob(QtWidgets.QGraphicsRectItem):
	"""handle marking inputs and outputs"""
	def __init__(self, parent=None, tree:NodeAttr=None, extras={}):
		super(Knob, self).__init__(parent)
		self.extras = dict(extras)
		self.baseSize = 20
		self.setRect(0,0, self.baseSize, self.baseSize)
		if not tree:
			raise RuntimeError("no attrItem supplied")
		#self.attr = attr
		self.role = self.tree.role
		self.name = self.tree.name + "Knob"
		self.colour = baseColour
		self.pipes = []
		self.pen = QtGui.QPen()
		self.pen.setStyle(QtCore.Qt.NoPen)
		self.brush = QtGui.QBrush(QtGui.QColor(*self.colour),
		                          bs=QtCore.Qt.SolidPattern)
		#self.brush.setColor()
		self.setPen(self.pen)
		self.setBrush(self.brush)
		self.setAcceptHoverEvents(True)

	@property
	def tree(self):
		return self.parentItem().tree

	def __repr__(self):
		return self.name

	# visuals
	def hoverEnterEvent(self, event):
		"""tweak to allow knobs to expand pleasingly when you touch them"""
		self.setTumescent()

	def hoverLeaveEvent(self, event):
		"""return knobs to normal flaccid state"""
		self.setFlaccid()

	def setTumescent(self):
		scale = 1.3
		new = int(self.baseSize * scale)
		newOrigin = (new - self.baseSize) / 2
		self.setRect(-newOrigin, -newOrigin, new, new)

	def setFlaccid(self):
		self.setRect(0, 0, self.baseSize, self.baseSize)