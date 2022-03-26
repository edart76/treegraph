# smaller widgets contained on ui tiles to avoid attribute editors
from PySide2 import QtCore, QtWidgets, QtGui
import random

class NodeGroupBox(QtWidgets.QGroupBox):
	"""container for holding individual widgets"""
	def __init__(self, label, parent=None):
		super(NodeGroupBox, self).__init__(parent)
		margin = (0, 0, 0, 0)
		if label == '':
			margin = (0, 2, 0, 0)

		self.setMaximumSize(120, 50)
		self.setTitle(label)

		self._layout = QtWidgets.QVBoxLayout(self)
		self._layout.setContentsMargins(*margin)
		self._layout.setSpacing(1)

	def addNodeWidget(self, widget):
		self._layout.addWidget(widget)


class NodeBaseWidget(QtWidgets.QGraphicsProxyWidget):
	"""	proxy to embed widgets in node graphics
	"""
	valueChanged = QtCore.Signal(str, object)

	def __init__(self, parent=None, name='widget', label=''):
		super(NodeBaseWidget, self).__init__(parent)
		self._name = name
		self._label = label

	def keyPressEvent(self, event:QtGui.QKeyEvent) -> None:
		"""accept any events passed to node widgets,
		prevent them propagating back to other classes"""
		#print("proxy keypress event", event.key())
		#self.widget.keyPressEvent(event)
		event.accept()
		result = super(NodeBaseWidget, self).keyPressEvent(event)
		#print("proxy event accepted", event.isAccepted())

	def setWidget(self, widget):
		"""set proper alignment automatically"""
		super(NodeBaseWidget, self).setWidget(widget)
		widget.setAlignment(QtCore.Qt.AlignCenter)
		widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
		                        QtWidgets.QSizePolicy.Ignored)

	def emitValueChanged(self):
		self.valueChanged.emit(self.name, self.value)

	def setToolTip(self, tooltip):
		tooltip = tooltip.replace('\n', '<br/>')
		tooltip = '<b>{}</b><br/>{}'.format(self.name, tooltip)
		super(NodeBaseWidget, self).setToolTip(tooltip)

	def disable(self):
		"""stops user input on connected inputs"""
		self.widget.setReadOnly(True)

	def enable(self):
		self.widget.setReadOnly(False)

	@property
	def widget(self):
		raise NotImplementedError

	@property
	def value(self):
		raise NotImplementedError

	@value.setter
	def value(self, text):
		raise NotImplementedError

	@property
	def label(self):
		return self._label

	@label.setter
	def label(self, label):
		self._label = label

	@property
	def type(self):
		return str(self.__class__.__name__)

	@property
	def node(self):
		return self.parentItem()

	@property
	def name(self):
		return self._name


class DebugLineEdit(QtWidgets.QLineEdit):
	def keyPressEvent(self, event:QtGui.QKeyEvent) -> None:
		print("line key event", event)
		return super(DebugLineEdit, self).keyPressEvent(event)

class NameTagWidget(NodeBaseWidget):
	"""used to display the name of a node and fluidly rename it"""
	def __init__(self, parent=None, initName="newNode", label=""):
		super(NameTagWidget, self).__init__(parent)
		self.line = QtWidgets.QLineEdit()
		#self.line = DebugLineEdit
		self.line.setText(initName)
		self.line.setAlignment(QtCore.Qt.AlignCenter)
		self.line.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
		                        QtWidgets.QSizePolicy.Ignored)
		self.line.updateGeometry()
		self.line.editingFinished.connect(self.emitValueChanged)
		self.line.editingFinished.connect(self.onEditFinished)
		self.setWidget(self.line)

	def onEditFinished(self, *args, **kwargs):
		"""return to read-only"""
		# self.line.setReadOnly(True)
		self.line.updateGeometry()

	@property
	def widget(self):
		return self.line

	@property
	def value(self):
		return self.line.text()

	@value.setter
	def value(self, val):
		self.line.setText(val)

class NodeLabel(NodeBaseWidget):
	"""used to put a label on it"""

class NodeComboBox(NodeBaseWidget):
	"""
	ComboBox Node Widget.
	"""

	def __init__(self, parent=None, name='', value=None, label='', items=None):
		super(NodeComboBox, self).__init__(parent, name, label)
		self.comboBox = QtWidgets.QComboBox()
		self.comboBox.setMinimumHeight(24)
		self.comboBox.activated.connect(self.emitValueChanged)
		comboView = QtWidgets.QListView(self.comboBox)
		self.comboBox.setView(comboView)
		self.comboBox.clearFocus()
		group = NodeGroupBox(label)
		group.addNodeWidget(self.comboBox)

		self.setWidget(group)
		self.add_items(items)
		if value:
			self.value = value

	@property
	def type(self):
		return 'ComboNodeWidget'

	@property
	def widget(self):
		return self.comboBox

	@property
	def value(self):
		return str(self.comboBox.currentText())

	@value.setter
	def value(self, text=''):
		index = self.comboBox.findText(text, QtCore.Qt.MatchExactly)
		self.comboBox.setCurrentIndex(index)

	def add_item(self, item):
		self.comboBox.addItem(item)

	def add_items(self, items=None):
		if items:
			self.comboBox.addItems(items)

	def all_items(self):
		return [self.comboBox.itemText(i) for i in range(self.comboBox.count)]

	def sort_items(self):
		items = sorted(self.all_items())
		self.comboBox.clear()
		self.comboBox.addItems(items)

	def clear(self):
		self.comboBox.clear()


class NodeLineEdit(NodeBaseWidget):
	"""
	LineEdit Node Widget.
	"""

	def __init__(self, parent=None, name='', label='', text=''):
		super(NodeLineEdit, self).__init__(parent, name, label)
		self.line = QtWidgets.QLineEdit()
		self.line.setAlignment(QtCore.Qt.AlignLeft)
		self.line.editingFinished.connect(self.emitValueChanged)
		self.line.clearFocus()
		group = NodeGroupBox(label)
		group.addNodeWidget(self.line)
		self.setWidget(group)
		self.text = text
		self.value = text

	@property
	def type(self):
		return 'LineEditNodeWidget'

	@property
	def widget(self):
		return self.line

	@property
	def value(self):
		return str(self.line.text())

	@value.setter
	def value(self, text=''):
		self.line.setText(text)


class NodeCheckBox(NodeBaseWidget):
	"""
	CheckBox Node Widget.
	"""

	def __init__(self, parent=None, name='', label='', text='', state=False):
		super(NodeCheckBox, self).__init__(parent, name, label)
		self.checkBox = QtWidgets.QCheckBox(text)
		self.checkBox.setChecked(state)
		self.checkBox.setMinimumWidth(80)
		# self._cbox.setStyleSheet(STYLE_QCHECKBOX)
		font = self.checkBox.font()
		font.setPointSize(11)
		self.checkBox.setFont(font)
		self.checkBox.stateChanged.connect(self.emitValueChanged)
		group = NodeGroupBox(label)
		group.addNodeWidget(self.checkBox)
		self.setWidget(group)
		self.text = text
		self.state = state

	@property
	def type(self):
		return 'CheckboxNodeWidget'

	@property
	def widget(self):
		return self.checkBox

	@property
	def value(self):
		return self.checkBox.isChecked()

	@value.setter
	def value(self, state=False):
		self.checkBox.setChecked(state)

class NodeColourBox(NodeBaseWidget):
	"""box to select a specific RGB colour - maybe later RGBA"""
	def __init__(self, parent=None, name="", label="", value=None):
		if not value:
			value = (random.randint(1,255), random.randint(1,255), random.randint(60,255))
		super(NodeColourBox, self).__init__(parent, name, label)
		self.box = self.makeBox(value)
		self._value = None
		self.qValue = None
		self.value = value
		# self.dialog = QtWidgets.QColorDialog(QtGui.QColour(*value), parent=self)
		# self.dialog.setOption(QtWidgets.QColourDialog.NoButtons, True)
		# self.dialog.setOption(QtWidgets.QColourDialog.ShowAlphaChannel, False)

	def mousePressEvent(self, event):
		"""creates colour dialog on mouse click"""
		colour = QtWidgets.QColorDialog.getColor(
			initial = self.qValue,
			options=[QtWidgets.QColorDialog.NoButtons]
		)
		if colour.isValid():
			self.value = colour
		super(NodeColourBox, self).mousePressEvent(event)

	def makeBox(self, value):
		"""creates a small widget of block colour to display current value"""
		box = QtWidgets.QWidget(self)
		box.setAutoFillBackground(True)
		return box

	def setBoxColour(self, val):
		p = self.box.palette()
		p.setColour(self.box.backgroundRole(), QtGui.QColor(val))
		self.box.setPalette(p)

	@property
	def type(self):
		return "pretty colours"

	@property
	def widget(self):
		return self.box

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, val):
		self._value = val
		self.qValue = QtGui.QColor(*val)
		self.setBoxColour(self.qValue)


class NodeIntSpinbox(NodeBaseWidget):
	"""
	Int spinbox Node Widget.
	"""

	def __init__(self, parent=None, name='', label='', value=1, min=None, max=None):
		super(NodeIntSpinbox, self).__init__(parent, name, label)
		self._field = self.getField()
		self._field.setMinimumWidth(80)
		# self._field.setStyleSheet(STYLE_QCHECKBOX)
		font = self._field.font()
		font.setPointSize(11)
		self._field.setFont(font)
		self._field.valueChanged.connect(self.emitValueChanged)
		group = NodeGroupBox(label)
		group.addNodeWidget(self._field)
		self.setWidget(group)
		self.value = value
		if max:
			self._field.setMaximum(max)
		if min:
			self._field.setMinimum(min)

	def getField(self):
		return QtWidgets.QSpinBox()

	@property
	def type(self):
		return 'IntSpinboxNodeWidget'

	@property
	def widget(self):
		return self._field

	@property
	def value(self):
		return self._field.value()

	@value.setter
	def value(self, val):
		self._field.setValue(val)

class NodeFloatSpinbox(NodeIntSpinbox):
	def __init__(self, parent=None, name='', label='', value=1, min=None, max=None):
		super(NodeFloatSpinbox, self).__init__(parent, name, label, value, min, max)

	def getField(self):
		return QtWidgets.QDoubleSpinBox()

	@property
	def type(self):
		return 'FloatSpinboxNodeWidget'

