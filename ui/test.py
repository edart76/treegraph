

from PySide2 import QtCore, QtWidgets
from treegraph.ui.view import GraphView
from treegraph import Graph
from treegraph.ui.textedit import TextEditWidget


class TestWin(QtWidgets.QWidget):
	def __init__(self, parent, graph):
		super(TestWin, self).__init__(parent)

		self.view = GraphView(parent=self, graph=graph)
		self.edit = TextEditWidget(parent=self)

		vl = QtWidgets.QVBoxLayout()
		vl.addWidget(self.view)
		vl.addWidget(self.edit)
		vl.setContentsMargins(2, 2, 2, 2)
		self.setLayout(vl)
		#self.setContentsMargins(2, 2, 2, 2)

"""

def test():
	a = 2
	c, b, \
		= 4, 5


"""

testCodeStr = r"""def test():
	a = 2 
	c, b, \
		= 4, 5


"""



if __name__ == '__main__':

	import sys
	from PySide2.QtWidgets import QApplication

	graph = Graph()


	app = QApplication(sys.argv)
	win = QtWidgets.QMainWindow()
	widg = TestWin(parent=win, graph=graph)
	win.setCentralWidget(widg)
	win.show()
	win.setGeometry(200, 200, 400, 400)
	widg.edit.setText(testCodeStr)

	stylePath = r"./style/dark/stylesheet.qss"
	settingFile = QtCore.QFile(stylePath)
	print(settingFile.exists(stylePath))
	settingFile.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
	stream = QtCore.QTextStream(settingFile)
	app.setStyleSheet(stream.readAll())

	iNode = graph.createNode("IntNode", name="newNode", add=True)

	sys.exit(app.exec_())
	pass










