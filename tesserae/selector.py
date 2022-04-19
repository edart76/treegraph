
from __future__ import annotations

from PySide2 import QtCore, QtWidgets, QtGui

from treegraph.glimport import *
from tree import TreeWidget
from tree.ui.delegate import TreeNameDelegate
if Ty.TYPE_CHECKING:
	from treegraph.tesserae.mainwidget import TesseraeWidget
	from treegraph.tesserae.graphtabwidget import GraphTabWidget

print("treeW", TreeWidget)

class GraphSelector(TreeWidget):
	"""display available graphs and the files to which they are linked"""

	def __init__(self, parent:GraphTabWidget=None,
	             ):
		
		super(GraphSelector, self).__init__(
			parent, tree=None,
		showValues=False,
		showRoot=False,
		showHeader=False,
		alternatingRows=False,
		allowNameMerging=False,
		collapsible=True)


	pass

