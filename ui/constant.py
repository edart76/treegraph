from PySide2 import QtCore
from treegraph.ui.style import PIPE_STYLE_DEFAULT, PIPE_STYLE_DASHED, PIPE_STYLE_DOTTED

entryHeight = 20
nameBarHeight = 30
settingsPadding = 5
PIPE_STYLES = {
    PIPE_STYLE_DEFAULT: QtCore.Qt.PenStyle.SolidLine,
    PIPE_STYLE_DASHED: QtCore.Qt.PenStyle.DashDotDotLine,
    PIPE_STYLE_DOTTED: QtCore.Qt.PenStyle.DotLine
}

baseColour = (100, 100, 200)

