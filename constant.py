
from enum import Enum
from tree.lib.object import ExtensibleEnumLike


class NodeState(ExtensibleEnumLike
                ):
	"""state of node in an execution graph"""
	neutral = "neutral"
	executing = "executing"
	complete = "complete"
	failed = "failed"
	approved = "approved"
