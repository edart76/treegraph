

from __future__ import annotations
"""specific tree subclass to support closer integration with ui,
and with graph state"""
import typing as T
from tree.lib.path import PurePath
from tree import Tree

from tree.lib.constant import AtomicWidgetType, AtomicWidgetSemanticType
from tree.ui.atomicwidget import AtomicWidgetParams, optionType
from tree.util.ui import markBranchForUIWidget

class NodeSettings(Tree):
	"""minimal behaviour overrides - just tool and ui methods"""

	# settings
	def addSetting(self, settingName, value=None, options=None, min=None, max=None, uiParams:AtomicWidgetParams=None):
		"""add setting entry to abstractTree"""

		branch = self(settingName)
		if options == bool:
			options = (True, False)
		extras = {"options" : options,
		          "min" : min,
		          "max" : max}
		branch.extras = {k : v for k, v in extras.items() if v}
		branch.value = value

		if uiParams is not None:
			markBranchForUIWidget(branch, params=uiParams)

		return branch

	def addBoolSetting(self, name:str, value:bool):
		params = AtomicWidgetParams(type=AtomicWidgetType.BoolCheckBox)
		self.addSetting(settingName=name, value=value, uiParams=params)

	def addOptionSetting(self, name:str, value:bool, options:optionType,
	                     widgetType=AtomicWidgetType.EnumMenu):
		params = AtomicWidgetParams(type=widgetType, options=options)
		return self.addSetting(name, value, options, uiParams=params)

	def addFilePathSetting(self, name:str, value:(str, PurePath)="",
	                       defaultFolder:(str, PurePath)="",
	                       fileMask="*.py;"
	                       ):
		params = AtomicWidgetParams(type=AtomicWidgetType.File,
		                            fileMask=fileMask,
		                            defaultFolder=defaultFolder)

		fileBranch = self.addSetting(name, value, params)




