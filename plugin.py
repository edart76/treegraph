
"""
we take inspiration from Maya and the way it handles user plugin registration
specific node types are registered against graph object classes?
allowing for different nodes in different graph contexts?

"""
import typing as T

from treegraph.node import GraphNode
from treegraph.graph import Graph

from treegraph.ui.scene import GraphScene
from treegraph.ui.delegate import NodeDelegate


def registerNode(nodeCls:T.Type[GraphNode],
                 graphCls:T.Type[Graph]=Graph):
	"""registers node class, adds it to list of registered nodes"""
	graphCls.registerNodeClasses([nodeCls])

def registerNodeDelegate(nodeCls:T.Type[GraphNode],
                         delegateCls:T.Type[NodeDelegate],
                         sceneCls:T.Type[GraphScene]=GraphScene):
	"""register specific delegate class for drawing a given node class"""
	sceneCls.registerNodeDelegate(nodeCls, delegateCls)

	pass
