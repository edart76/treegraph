
"""
we take inspiration from Maya and the way it handles user plugin registration
specific node types are registered against graph object classesToReload?
allowing for different nodes in different graph contexts?

"""
import sys, os
import typing as T
from pathlib import Path, PurePath

from treegraph.node import GraphNode
from treegraph.graph import Graph

from treegraph.ui.scene import GraphScene
from treegraph.ui.delegate import NodeDelegate


def registerNodes(nodeClasses:T.Set[type],
                 graphCls:T.Type[Graph]=Graph):
	"""registers node class, adds it to list of registered nodes"""
	graphCls.registerNodeClasses(nodeClasses)


def scanNodeDirs(nodeDirs:T.List[PurePath], validBaseClasses=(GraphNode, )):
	"""scan through all modules in nodeDirs recursively, checking for
	objects inheriting from validBaseClasses
	return resulting list of objects
	nameclashes are not handled - for now Tesserae nodes must have globally
	unique class names
	"""
	nodeClasses = {}
	for nodeDir in nodeDirs:
		for root, dirs, files in os.walk(nodeDir):
			for dirFile in files:
				if not dirFile.endswith(".py"):
					continue
				filePath = Path(root) / dirFile

def registerNodeDelegate(nodeCls:T.Type[GraphNode],
                         delegateCls:T.Type[NodeDelegate],
                         sceneCls:T.Type[GraphScene]=GraphScene):
	"""register specific delegate class for drawing a given node class"""
	sceneCls.registerNodeDelegate(nodeCls, delegateCls)

	pass
