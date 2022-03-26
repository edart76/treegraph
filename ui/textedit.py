# widget incorporating better editing of python code callbacks
# translated from qt docs

import traceback, ast

from PySide2 import QtCore, QtWidgets, QtGui

from treegraph.ui.lib import KeyState, keyDict, returnLines, pyInterpLines
from treegraph.ui.highlighter import PythonHighlighter

class LineNumberArea(QtWidgets.QWidget):
	""""""
	def __init__(self, editor):
		super(LineNumberArea, self).__init__(editor)
		self.editor = editor
		self.editor.textChanged.connect(self.onTextChanged)

	def onTextChanged(self, *args):
		self.update()

	def sizeHint(self):
		return QtCore.QSize(self.editor.lineNumberAreaWidth(), 0)

	def paintEvent(self, event):
		self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QtWidgets.QPlainTextEdit):
	""""""
	def __init__(self, parent=None):
		super(CodeEditor, self).__init__(parent)
		self.lineNumberArea = LineNumberArea(self)

		self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
		#self.updateRequest.connect(self.updateLineNumberAreaWidth)
		self.textChanged.connect(self.updateLineNumberAreaWidth)
		self.cursorPositionChanged.connect(self.highlightCurrentLine)

		# immediate updates
		self.textChanged.connect(self.updateLineNumberAreaWidth)

		self.updateLineNumberAreaWidth(0)
		self.highlightCurrentLine()

		codeFont = QtGui.QFont("Courier")
		codeFont.setPointSize(1)
		self.document().setDefaultFont(codeFont)
		self.setPlaceholderText("enter python code...")

	@property
	def text(self):
		return self.toPlainText()

	def lineNumberAreaWith(self):
		digits = 1
		limit = self.blockCount() or 1
		while limit >= 10:
			limit /= 10
			digits += 1

		#space = 3 + self.fontMetrics().horizontalAdvance(QtCore.QLatin1Char("9")) * digits
		# horizontalAdvance doesn't exist
		space = 3 + 12 * digits
		return space

	def updateLineNumberAreaWidth(self, *args, **kwargs):
		# (int /* newBlockCount */) # what does this mean?
		self.setViewportMargins(self.lineNumberAreaWith(), 0, 0, 0)

	# def proxyUpdateLineNumberAreaWidth(self, *args, **kwargs):
	# 	#?????
	# 	self.setViewportMargins(self.lineNumberAreaWith(), 0, 0, 0)

	def updateLineNumberArea(self, rect=None, dy=None):
		if dy:
			self.lineNumberArea.scroll(0, dy)
		else:
			self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(),
			                           rect.height())

		if rect.contains(self.viewport().rect()):
			self.updateLineNumberAreaWidth(0)

	def resizeEvent(self, event):
		super(CodeEditor, self).resizeEvent(event)
		cr = self.contentsRect()
		self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(),
		                                             self.lineNumberAreaWith(),
		                                             cr.height()))

	def lineNumberAreaPaintEvent(self, event):
		painter = QtGui.QPainter(self.lineNumberArea)
		painter.fillRect(event.rect(), QtCore.Qt.darkGray) # lol they can't spell

		block = self.firstVisibleBlock()
		blockNumber = block.blockNumber()
		top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
		bottom = top + int(self.blockBoundingRect(block).height())

		while block.isValid() and top <= event.rect().bottom():
			if block.isVisible() and bottom >= event.rect().top():
				number = str(blockNumber+1)
				painter.setPen(QtCore.Qt.white)
				painter.drawText(0, top, self.lineNumberArea.width(),
				                 self.fontMetrics().height(),
				                 QtCore.Qt.AlignRight, number)
			block = block.next()
			top = bottom # cats and dogs
			bottom = top + int(self.blockBoundingRect(block).height())
			blockNumber += 1

	def highlightCurrentLine(self): # later
		pass


class PyCodeEditor(CodeEditor):
	"""syntax highlighting and basic autoformatting for
	python code"""

	def __init__(self, parent=None):
		super(PyCodeEditor, self).__init__(parent)
		self.textChanged.connect(self.updateAstBlocks)
		self.highlighter = PythonHighlighter(self.document())

	def updateAstBlocks(self, *args):
		"""update ast systems for syntax highlighting"""
		text = self.text.strip()
		try:
			tree = ast.parse(text, mode="exec")
		except SyntaxError:
			#traceback.print_exc()
			return


	def keyPressEvent(self, e:QtGui.QKeyEvent):
		keyName = keyDict[e.key()]

		return super(PyCodeEditor, self).keyPressEvent(e)



class TextEditWidget(QtWidgets.QWidget):
	"""holds line numbers and text edit"""
	backgroundColour = QtGui.QColor(30, 10, 10)
	textColour = QtGui.QColor(170, 170, 170)
	execCalled = QtCore.Signal()
	def __init__(self, parent=None, exeButton=True):
		super(TextEditWidget, self).__init__(parent)
		#self.editor = CodeEditor(parent=self)
		self.editor = PyCodeEditor(parent=self)
		self.toolBar = QtWidgets.QToolBar(self)
		self.exeBtn = QtWidgets.QToolButton(self.toolBar)
		self.exeBtn.setArrowType(QtCore.Qt.RightArrow)
		self.toolBar.addWidget(self.exeBtn)

		#self.exeBtn.triggered.connect(self.execCalled)
		self.exeBtn.clicked.connect(self.execCalled)
		self.execCalled.connect(self.onExecCalled)

		self.toolBar.setFixedHeight(20)
		#self.toolBar.setContentsMargins(2, 2, 2, 2)

		palette = self.palette()
		palette.setColor(QtGui.QPalette.Base,
		                 self.backgroundColour)
		palette.setColor(QtGui.QPalette.Text,
		                 self.textColour)
		self.setPalette(palette)
		self.makeLayout()
		#self.setContentsMargins(2, 2, 2, 2)

	@property
	def text(self):
		return self.editor.text
	def setText(self, text):
		self.editor.setPlainText(text)

	def onExecCalled(self):
		text = self.editor.text
		print("exec")
		#print(text)
		cursor = self.editor.textCursor()
		start, end = cursor.selectionStart(), cursor.selectionEnd()
		#print(text[start:end])

		splitLines = returnLines(text)
		#print("ret lines", splitLines)
		pyLines = pyInterpLines(splitLines)
		#print("py lines", pyLines)

		tree = ast.parse(text)
		print(ast.dump(tree))


	def makeLayout(self):
		vl = QtWidgets.QVBoxLayout()
		vl.addWidget(self.toolBar)
		vl.addWidget(self.editor)
		vl.setContentsMargins(2, 2, 2, 2)
		self.setLayout(vl)




