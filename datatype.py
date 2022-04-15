

from enum import Enum
import typing as T
from tree.lib.object import ExtensibleEnumLike
from treegraph.lib.python import itersubclasses


class DataTypeBase(object):
	"""base class for data type passed through the graph
	semi-dataclass,
	not sure if this should carry the actual value"""

	@classmethod
	def allDataTypes(cls):
		return list(itersubclasses(cls))

class Null(DataTypeBase):
	pass

class Int(DataTypeBase):
	pass

class Float(DataTypeBase):
	pass

class String(DataTypeBase):
	pass

class Dict(DataTypeBase):
	pass

# available plug types
class DataTypes(ExtensibleEnumLike):
	"""Redefine your own data types in inheriting programs
	add them as members to this class"""
	Null = Null
	Int = Int
	Float = Float
	String = String
	Dict = Dict

	@classmethod
	def registerDataType(cls, registerClass:T):
		assert DataTypeBase in registerClass.__mro__
		cls.registerMember(registerClass)
