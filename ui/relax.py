
from __future__ import annotations

# scene holding visual node graph
from PySide2 import QtCore, QtGui

from treegraph.ui.delegate.node import NodeDelegate

"""functions for graph layout and relaxing
going for simple spring setup

n-squared 

"""

separation = 10.0

expand = 20
margins = QtCore.QMargins(expand, expand, expand, expand)

def getForce(tile:NodeDelegate)->QtGui.QVector2D:
	"""for given tile, return resultant force acting upon it
	check each corner of the node for intersection
	"""

	# rect = QtCore.QRectF(tile.boundingRect())
	rect = QtCore.QRectF(tile.sceneBoundingRect().marginsAdded(margins))
	# rect = QtCore.QRectF(*tile.getSize())
	scene = tile.scene()
	# get intersecting tiles
	items = scene.items(rect)
	# remove this tile and any pipes (for now)
	#items.remove(tile)
	items = tuple(filter(lambda x: isinstance(x, NodeDelegate), items))
	sumForce = QtGui.QVector2D(0, 0)

	#print(rect)
	for i in items: #type: NodeDelegate
		if i is tile:
			continue

		#print("item", i.node.name)
		#print(i.boundingRect())
		# get intersection
		# iRect = rect.intersected(i.boundingRect())
		iRect = rect.intersected(i.sceneBoundingRect())
		#print("iRect", iRect)
		# get span of intersection
		span = QtGui.QVector2D(iRect.bottomRight() - iRect.topLeft()).length()
		# print("span", span)
		fDir = QtGui.QVector2D(rect.center() - iRect.center()).normalized()
		# fDir = QtGui.QVector2D(iRect.center()) -QtGui.QVector2D(rect.center())
		# print(iRect.center(), rect.center())
		# print(fDir)
		force = fDir * span
		sumForce = sumForce + force
	return sumForce * 0.4















