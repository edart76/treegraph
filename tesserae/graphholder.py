

from PySide2 import QtCore, QtWidgets, QtGui

from treegraph.ui.view import GraphView
from treegraph.ui.scene import GraphScene

class GraphWidget(QtWidgets.QWidget):
	"""container widget for a graph view in Tesserae -
	holds toolbar, path selector
	"""

	def __init__(self, parent=None):
		super(GraphWidget, self).__init__(parent)

		self.graphs = {} # {uuid : graph }






