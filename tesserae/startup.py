
"""create an instance of tesserae and initialise with an
empty graph"""

from __future__ import annotations
import typing as Ty
from tree import TreeWidget
from tree.ui.delegate import TreeNameDelegate
from treegraph.graph import Graph
if Ty.TYPE_CHECKING:
	from treegraph.tesserae.mainwidget import TesseraeWidget
	from treegraph.tesserae.graphtabwidget import GraphTabWidget
from treegraph.ui.view import GraphView
from treegraph.ui.scene import GraphScene


