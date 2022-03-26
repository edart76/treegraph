from __future__ import print_function

import typing as T

from PySide2 import QtCore
from tree.ui.lib import *



def cursorLine(doc):
	"""returns ilne number of the cursor's
	current line in document """


def returnLines(text=""):
	"""returns text split by newline characters
	probably inefficient"""
	newIndices = [0]
	for i, char in enumerate(text):
		if char != "\n":
			continue
		newIndices.append(i)

	lines = []
	newIndices.append(-1)
	for i, v in enumerate(newIndices[:-1]):
		lines.append(text[ v : newIndices[i+1] ])
	return lines

def pyInterpLines(splitLines=T.List[str]):
	"""return lines as a python interpreter would read them -
	if any line ends with backslash char,
	those two lines are joined"""
	interpLines = []
	i = 0
	while i < len(splitLines):
		if splitLines[i].endswith("\\"):
			interpLines.append(splitLines[i][:-1] + splitLines[i + 1][1:])
			i += 2
			continue
		interpLines.append(splitLines[i])
		i += 1
	return interpLines


