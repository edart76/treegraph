
from __future__ import annotations

import pprint
from weakref import WeakSet, WeakValueDictionary
from collections import defaultdict
from typing import List, Callable, Dict, Union, Set, TYPE_CHECKING, Sequence
from functools import partial
from enum import Enum

import itertools
from importlib import reload
from tree import Tree, Signal


class NodeSet(object):
	"""Container for a set of nodes
	mainly to interface better with transforms and proxying
	"""
	def __init__(self, name="newSet"):
		self._name = None
		self.nodes = WeakSet()

		self.nodesChanged = Signal()

	def add(self, node):
		self.nodes.add(node)
		self.nodesChanged()

	def remove(self, node):
		self.nodes.remove(node)
		self.nodesChanged()

	def __contains__(self, item):
		return item in self.nodes
	def __len__(self):
		return len(self.nodes)




