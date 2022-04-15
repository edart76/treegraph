

from __future__ import annotations

import random
import colorsys
from tree import Tree

from typing import TYPE_CHECKING, Union, Dict, List
import typing as T

from PySide2 import QtCore, QtWidgets, QtGui

# ugly fake imports for type hinting
if TYPE_CHECKING:
	from treegraph.ui.view import GraphView

# scene holding visual node graph

from treegraph.ui.delegate.node import NodeDelegate
from treegraph.ui.delegate.edge import EdgeDelegate
from treegraph import GraphNode, Graph, GraphEdge

from treegraph.ui.style import (VIEWER_BG_COLOR,
                                      VIEWER_GRID_COLOR,
                                      VIEWER_GRID_OVERLAY)
from treegraph.ui import relax
from tree.ui.lib import KeyState, keyDict


debugEvents = False

def randomPastel(seed):
	random.seed(a=seed)
	h = random.random()
	s = 0.5 + ((random.random()) / 3.0)
	v = 0.7 + ((random.random()) / 5.0)
	rgb = colorsys.hsv_to_rgb(h, s, v)
	return rgb

class GraphScene(QtWidgets.QGraphicsScene):
	"""graphics scene for interfacing with abstractgraph and ui
	hook directly into abstractgraph tree signals
	"""

	delegateMap = {GraphNode : NodeDelegate} #type:T.Dict[T.Type[GraphNode] : T.Type[NodeDelegate]]

	def __init__(self, parent=None, graph:Graph=None,
	             # view:"edRig.tesserae.ui2.GraphView"=None
	             view:"GraphView"=None
	             ):
		super(GraphScene, self).__init__(parent)
		self.views = [view]
		# eventually allowing multiple codependent views of the same graph
		self.activeView = view

		# scene is tied to GRAPH, not to view
		self._graph = graph


		self.setSceneRect(1000, 200, 0, 0)
		self.tiles = {} #type: Dict[GraphNode, NodeDelegate]
		#self.tiles = WeakKeyDictionary() #type: Dict[GraphNode, NodeDelegate]
		self.pipes = {} #type: Dict[GraphEdge, EdgeDelegate]
		# self.pipes = WeakKeyDictionary() #type: Dict[GraphEdge, EdgeDelegate]


		self.background_color = VIEWER_BG_COLOR
		self.grid = VIEWER_GRID_OVERLAY
		self.grid_color = VIEWER_GRID_COLOR

		# tree signal hookups
		self.graph.structureChanged.connect(self.onNodesChanged)
		self.graph.edgesChanged.connect(self.onEdgesChanged)

		self.selectionChanged.connect(self.onSceneSelectionChanged)

		# temp
		self.mouseMoveCounter = 0


	@property
	def graph(self)->Graph:
		return self._graph

	def getTile(self, node):
		"""returns tile for the given node, name, path or uuid
		"""
		print("scene getTile", node)
		node = self.graph.getNode(node)
		result = self.tiles.get(node)
		if not result:
			print("no tile for node {} found".format(node))
			return None
		return result

	### region graph signal functions, direct match to tree signals
	def onNodesChanged(self, node:GraphNode, parent=None, oldParent=None,
	                   eventType=Tree.StructureEvents.branchRemoved):
		if not isinstance(node, GraphNode):
			#print("node is not node, skipping")
			return
		# node created
		if eventType == Tree.StructureEvents.branchAdded:
			# print("scene signal node added")
			tile = self.makeTile(abstract=node)
			return tile
		#elif eventType == Tree.StructureEvents.branchRemoved:
		elif eventType == Tree.StructureEvents.beforeBranchRemoved:
			# print("scene signal node removed")
			tile = self.getTile(node)
			if tile:
				self.deleteTile(tile)
			return tile


	def onEdgesChanged(self, edge:GraphEdge,
	                   event=Graph.EdgeEvents.added):
		"""called when an edge is created or dereferenced in the graph"""
		print("scene onEdgesChanged")
		if event == Graph.EdgeEvents.removed:
			pipe = self.pipes.get(edge)
			if not pipe:
				return
			self.deletePipe(pipe)
		elif event == Graph.EdgeEvents.added:
			self.addEdgePipe(edge)


	@classmethod
	def registerNodeDelegate(cls, nodeCls, delegateCls):
		"""used to register custom node drawing class"""
		cls.delegateMap[nodeCls] = delegateCls

	@classmethod
	def delegateForNode(cls, node:GraphNode):
		"""look up the nearest matching delegate for
		given node"""
		for i in [type(node), *type(node).__mro__]:
			if i in cls.delegateMap:
				return cls.delegateMap[i]
		raise RuntimeError("No drawing delegate found for {} or in {}".format(
			type(node), type(node).__mro__	))

	def makeTile(self, abstract:GraphNode=None,
	             pos:Union[
		             QtCore.QPoint, QtCore.QPointF, None]=None
	             )->NodeDelegate:
		if isinstance(self.tiles.get(abstract), NodeDelegate):
			raise RuntimeError("added node already in scene")

		delegateCls = self.delegateForNode(abstract)

		tile = delegateCls(abstractNode=abstract,

		                    )
		self.addItem(tile)
		tile.arrange()
		# get default position
		if pos is None:
			#print("adding random pos")
			# pos = (self.activeView.camCentre +
			# 	QtCore.QPoint(random.random(), random.random()) * 10)
			pos = self.activeView.camCentre #type: QtCore.QPoint
			pos.setX(pos.x() + random.random() * 100)

		# # set random jitter position
		# tile.setPos(random.random(), random.random())
		# self.relaxItems([tile])
		if isinstance(pos, (QtCore.QPointF, QtCore.QPoint)):
			tile.setPos(pos)
		else:
			tile.setPos(*pos)
		self.tiles[abstract] = tile
		#self.addItem(tile.settingsProxy)
		self.relaxItems([tile], iterations=2)
		return tile

	def addEdgePipe(self, edge:GraphEdge=None):
		"""can only be done with an existing abstractEdge"""
		if debugEvents: print("scene addEdgePipe")
		if edge:
			start = self.tiles[edge.source[0]].knobs[
				edge.source[1].stringAddress()]
			end = self.tiles[edge.dest[0]].knobs[
				edge.dest[1].stringAddress()]
			pipe = EdgeDelegate(start=start, end=end, edge=edge)

			self.pipes[edge] = pipe

			self.addPipe(pipe)

			return pipe

	def addPipe(self, pipe):
		self.addItem(pipe)
		pipe.drawPath(pipe.start, pipe.end)

	def updatePipePaths(self, tiles:List[NodeDelegate]=None):
		"""updates everything for now - if that gets laggy only redraw changed"""
		# print("scene update")
		# print("graph edges", self.graph.edges)
		if tiles:
			edges = set()
			for i in tiles:
				# edges.update(i.node.edges)
				edges.update(self.graph.nodeEdges(i.node, all=True))
			pipes = [self.pipes[i] for i in edges]
		else:
			pipes = self.pipes.values()
		for i in pipes:
			i.redrawPath()

	# def clearSelectionAttr(self):
	# 	"""clears "selected" attr for tiles and pipes that are not selected"""

	def onSceneSelectionChanged(self, *args, **kwargs):
		"""passed no arguments, just fires every change
		iterate through nodes - call the selected signal on each"""
		for i in self.tiles.values():
			i.onSceneSelectionChanged()

	def onDeleteCalled(self):
		"""delete selected tiles and pipes"""
		if debugEvents:print("scene onDeleteCalled")
		if debugEvents: print("selection is {}".format(self.selectedItems()))
		for i in self.selectedPipes():
			self.graph.deleteEdge(i.edge)
		for i in self.selectedTiles():
			self.deleteTile(i)
			self.graph.deleteNode(i.node)
			#print("node graph nodes are {}".format(self.graph.knownNames))


			#self.deletePipe(i)

		#print self.selectedTiles()


	def deleteTile(self, tile):
		"""ONLY VISUAL"""
		if isinstance(tile, GraphNode):
			if tile not in list(self.tiles.keys()):
				return
			tile = self.tiles[tile]
		for i in tile.node.edges:
			pipe = self.pipes[i]
			self.deletePipe(pipe)
		# for k, v in self.tiles.iteritems():
		# 	if v == tile:
		# 		target = k
		#self.tiles.pop(target)
		self.tiles.pop(tile.node)
		self.removeItem(tile)

	def deleteEdgePipe(self, edge:GraphEdge):
		"""called when a graph edge is deleted or dereferenced
		"""


	def deletePipe(self, pipe:EdgeDelegate):
		if debugEvents: print("scene deletePipe")
		# if isinstance(pipe, GraphEdge):
		# 	if pipe not in list(self.pipes.keys()):
		# 		return
		# 	pipe = self.pipes[pipe]

		self.pipes.pop(pipe.edge)

		# remove pipe references from knobs
		for knob in pipe.start, pipe.end:
			if pipe in knob.pipes:
				knob.pipes.remove(pipe)
		self.removeItem(pipe)
		# i never want to tipe pipe


	def selectedTiles(self):
		nodes = []
		for item in self.selectedItems():
			if isinstance(item, NodeDelegate):
				nodes.append(item)
		return nodes

	def selectedPipes(self):
		return [i for i in self.selectedItems()
		        if isinstance(i, EdgeDelegate)]

	def mousePressEvent(self, event):
		if debugEvents: print("scene mousePress")
		super(GraphScene, self).mousePressEvent(event)
		if event.isAccepted():
			if debugEvents: print("scene mousePress accepted, returning")
			return True
		selected_nodes = self.selectedTiles()
		# if self.activeView:
		# 	self.activeView.beginDrawPipes(event)

	def mouseMoveEvent(self, event):

		self.updatePipePaths(self.selectedTiles())

		self.mouseMoveCounter += 1
		self.mouseMoveCounter = self.mouseMoveCounter % 6

		if self.mouseMoveCounter:
			return super(GraphScene, self).mouseMoveEvent(event)

		# only activate occasionally
		# get intersecting tiles
		toRelax = []
		expand = 20
		margins = QtCore.QMargins(expand, expand, expand, expand)
		for i in self.selectedTiles():
			items = self.items(i.sceneBoundingRect().marginsAdded(margins))
			items = set(filter(lambda x: isinstance(x, NodeDelegate), items))
			items = (items).difference(set(self.selectedTiles()))

			toRelax.extend(items)

		#for i in self.selectedTiles():
		#self.relaxItems(toRelax) # not needed
		#self.update()
		super(GraphScene, self).mouseMoveEvent(event)

	def relaxItems(self, items, iterations=1):
		#print("scene relax items")
		for n in range(iterations):
			for i in items:
				force = relax.getForce(i)
				#print("force", force)
				i.setPos(i.pos() + force.toPointF())

	def layoutTiles(self, tiles:List[NodeDelegate]=None):
		"""single shot layout of all given nodes
		seed nodes are only arranged vertically
		Longest critical path taken as the baseline,
		other nodes laid out relative to it


		"""
		tiles = tiles or set(self.tiles.values())
		nodes = set(i.node for i in tiles)
		islands = self.graph.getIslands(nodes)
		for index, island in islands.items():
			ordered = self.graph.orderNodes(island)

			# only x for now
			baseTile = self.tiles[ordered[0]]
			separation = 75
			baseX = baseTile.pos().x() + baseTile.sceneBoundingRect().width() + separation
			x = baseX
			for i in ordered[1:]:
				tile = self.tiles[i]
				tile.setX(x)
				x += tile.sceneBoundingRect().width() + separation
		self.updatePipePaths(tiles)

	def mouseReleaseEvent(self, event):
		if self.activeView:
			self.activeView.endDrawPipes(event)
		super(GraphScene, self).mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		"""we first dispatch event to any scene widgets,
		as event flow in graphics scene goes from outer
		to inner, not the reverse

		only run scene operations if it has NOT been accepted"""
		#print("scene keyPressEvent", keyDict[event.key()])
		super(GraphScene, self).keyPressEvent(event)
		if event.isAccepted():
			#print("scene event accepted")
			return

		if event.key() in ( QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace ):
			self.onDeleteCalled()



	def dragMoveEvent(self, event:QtWidgets.QGraphicsSceneDragDropEvent):
		if debugEvents:print("scene dragMoveEvent")
		return super().dragMoveEvent(event)


	### region drawing

	def _draw_grid(self, painter, rect, pen, grid_size):
		# change to points
		lines = []
		left = int(rect.left()) - (int(rect.left()) % grid_size)
		top = int(rect.top()) - (int(rect.top()) % grid_size)
		x = left
		while x < rect.right():
			x += grid_size
			lines.append(QtCore.QLineF(x, rect.top(), x, rect.bottom()))
		y = top
		while y < rect.bottom():
			y += grid_size
			lines.append(QtCore.QLineF(rect.left(), y, rect.right(), y))
		painter.setPen(pen)
		painter.drawLines(lines)


	def drawBackground(self, painter, rect):
		#painter.save()
		# draw solid background
		color = QtGui.QColor(*self.background_color)
		painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
		painter.setBrush(color)
		painter.drawRect(rect.normalized())
		if not self.grid:
			return
		zoom = self.activeView.get_zoom()
		grid_size = 20
		if zoom > -0.5:
			color = QtGui.QColor(*self.grid_color)
			pen = QtGui.QPen(color, 0.65)
			self._draw_grid(painter, rect, pen, grid_size)
		color = QtGui.QColor(*VIEWER_BG_COLOR)
		color = color.lighter(130)
		color = QtCore.Qt.lightGray

		pen = QtGui.QPen(color, 0.65)
		self._draw_grid(painter, rect, pen, grid_size * 8)

		# draw node set fields
		# how many sets is each node part of
		tileDepth = {i : 1 for i in self.tiles.values()}
		for n, (name, data) in enumerate(
				self.graph.nodeSets.items()):
			tiles = [self.tiles[i] for i in data.nodes]

			# get random colour for this set
			s = hash(name)
			rgb = randomPastel(s)
			colour = QtGui.QColor.fromRgbF( *rgb )
			painter.pen().setColor(colour)
			painter.setPen(colour)
			colour.setAlphaF(0.2)
			painter.brush().setColor(colour)
			painter.setBrush(colour)

			# gather corner points of all nodes
			points = [None] * len(tiles) * 4
			for i, tile in enumerate(tiles):

				# expand for each set node is part of
				expansion = 10 * tileDepth[tile]
				margins = QtCore.QMargins(
					expansion, expansion, expansion, expansion
				)

				r = tile.sceneBoundingRect()
				r = r.marginsAdded(margins)
				points[i * 4] = r.topLeft()
				points[i * 4 + 1] = r.topRight()
				points[i * 4 + 2] = r.bottomRight()
				points[i * 4 + 3] = r.bottomLeft()

				tileDepth[tile] += 1
			# points = [QtCore.QPoint(j) for j in points]
			points = [j.toPoint() for j in points]
			poly = QtGui.QPolygon.fromList(points)
			painter.drawConvexPolygon(poly)


		#painter.restore()
	# endregion

	def serialiseUi(self, graphData):
		"""adds ui information to serialised output from graph
		no idea where better to put this"""
		for node, tile in self.tiles.items():
			graphData["nodes"][node.uid]["ui"] = tile.serialise()

	def regenUi(self, graphData):
		"""reapplies saved ui information to tiles"""
		for uid, info in graphData["nodes"].items():
			node = self.graph.nodeFromUID(uid)
			tile = self.tiles[node]
			tile.setPos(QtCore.QPointF(*info["ui"]["pos"]))

