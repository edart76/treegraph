

"""dcc- or software-specific implementations of general tesserae-operations -
this is used to get round some kind of horrific inheritance pattern for Graph,
subclassing for graph functionality in one axis,
but for dcc implementation in another.

if tesserae has to interact with its host software, extend this class,
not the base Graph classes

for now we use one function set per root graph, with child graphs inheriting it

"""

from __future__ import annotations
import typing as T
if T.TYPE_CHECKING:
	from treegraph.graph import Graph


class GraphFunctionSet(object):

	def __init__(self, rootGraph:Graph):
		self.graph = rootGraph
		pass


