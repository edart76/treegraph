
"""Alternate use for a tree widget, for selecting a single tree branch"""

from PySide2 import QtCore, QtWidgets, QtGui
from tree import Tree
from tree.ui.widget import TreeWidget
from tree.ui.constant import treeObjRole, addressRole, relAddressRole
#from tree.ui.delegate import treeObjRole

class TreeCompleter(QtWidgets.QCompleter):

	pass


class SelectorWidget(QtWidgets.QLineEdit):
	# signature {"old" : previous branch, "new" : new branch}
	branchChanged = QtCore.Signal(dict)
	def __init__(self, tree=None, parent=None,
	             showFileIO=False):
		super(SelectorWidget, self).__init__(parent)
		self.tree = None # at root
		self._prevValue = None
		self._branch = None
		self.treeWidg = TreeWidget(
			parent=self,
			showValues=False,
			alternatingRows=False
		)

		self.treeCompleter = TreeCompleter(self.treeWidg.model)
		self.treeCompleter.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		#self.treeCompleter.setCompletionMode(self.treeCompleter.InlineCompletion)
		self.setCompleter(self.treeCompleter)

		if tree:
			self.setTree(tree)

		self.returnPressed.connect(self.onTextSubmitted)

		self.treeWidg.hide()

	@property
	def branch(self)->Tree:
		"""return the currently selected branch"""
		return self._branch

	def setBranch(self, branch:Tree, emit=True):
		oldBranch = self._branch
		self._branch = branch
		self.setText(branch.stringAddress())
		self._prevValue = branch.stringAddress()
		if emit:
			self.branchChanged.emit({"old" : oldBranch, "new" : branch})

	def onTextSubmitted(self, *args, **kwargs):
		"""check if valid address has been given - if so, return that branch"""
		address = self.text()
		oldBranch = self.branch
		try:
			branch = self.tree(self.text(), create=False)
			self.setBranch(branch)

			return
		except:
			self.setText(self._prevValue)
			return



	def setTree(self, tree:Tree):
		self.tree = tree
		self.treeWidg.setTree(tree)


		branchNames = [i.stringAddress() for i in self.tree.allBranches(includeSelf=False)]
		listModel = QtCore.QStringListModel(branchNames)
		self.treeCompleter.setModel(listModel)



if __name__ == '__main__':
	def test():
		from tree.test.test_tree import midTree
		import sys
		app = QtWidgets.QApplication(sys.argv)
		win = QtWidgets.QMainWindow()

		w = QtWidgets.QWidget(win)
		vl = QtWidgets.QVBoxLayout()



		vl.addWidget(SelectorWidget(tree=midTree, parent=win))
		vl.addWidget(SelectorWidget(tree=midTree, parent=win))
		# widg = SelectorWidget(tree=midTree, parent=win)

		w.setLayout(vl)
		win.setCentralWidget(w)
		win.show()
		sys.exit(app.exec_())

	test()
