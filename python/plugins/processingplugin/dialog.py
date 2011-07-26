# -*- coding: utf-8 -*-

#	QGIS Processing panel plugin.
#
#	dialog.py (C) Camilo Polymeris
#	
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#       
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#   MA 02110-1301, USA.

from PyQt4.QtGui import *
from PyQt4.QtCore import QObject, SIGNAL
from ui_dialog import Ui_runDialog
import processing
from processing.parameters import *

class Dialog(QDialog, Ui_runDialog):
    def __init__(self, iface, module):
        QDialog.__init__(self, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.moduleinstance = module.instance()
        self.setupUi(self)
        self.setWindowTitle(self.windowTitle() + " - " + module.name())
        self.text.setText(module.description())
        execButton = QPushButton(self.tr("&Execute"));
        execButton.setDefault(True)
        self.buttons.addButton(execButton, QDialogButtonBox.ActionRole);
        self.rebuildDialog()
        # Rebuild the dialog if parameter structure changes.
        QObject.connect(self.moduleinstance,
            self.moduleinstance.valueChangedSignal(),
            self.rebuildDialog)
        # Start module instance on button click
        QObject.connect(execButton, SIGNAL("clicked()"),
            self._onExecButtonClicked)
    def rebuildDialog(self):
        for param, value in self.moduleinstance.parameters().items():
            label = param.name()
            if not param.isMandatory(): # optional parameters in italics
                label = '<i>%s</i>' % label
            if param.role() == Parameter.Role.output:
                label = '&gt; %s' % label
            label = '<html>%s</html>' % label
            widget = self._widgetByType(param, value)
            if widget is not None:
                self.form.addRow(label, widget)
    def _connectWidgetToParameter(self, widget,
        param, signal, setter, getter):
        instance = self.moduleinstance
        QObject.connect(widget, SIGNAL(signal),
            lambda v: instance.setValue(param, v))
            # only change the widget's value if it is different to
            # prevent circular signaling.
        valueSet = lambda v: v == getter(widget) or setter(widget, v)
        QObject.connect(instance, instance.valueChangedSignal(param),
            valueSet)
    def _widgetByType(self, param, value):
        try:
            w = param.widget(param, value)
            return w
        except AttributeError:
            pass
        pc = param.__class__
        if pc == StateParameter:
            return None
        if pc == NumericParameter:
            w = QSpinBox(None)
            w.setValue(value)
            self._connectWidgetToParameter(w, param,
                "valueChanged(int)", QSpinBox.setValue, QSpinBox.value)
            return w
        if pc == BooleanParameter:
            w = QCheckBox(None)
            w.setChecked(value)
            self._connectWidgetToParameter(w, param,
                "toggled(bool)",
                QCheckBox.setChecked, QCheckBox.isChecked)
            return w
        if pc == ChoiceParameter:
            w = QComboBox(None)
            w.addItems(param.choices())
            w.setCurrentIndex(value)
            self._connectWidgetToParameter(w, param,
                "currentIndexChanged(int)",
                QComboBox.setCurrentIndex,
                QComboBox.currentIndex)
            return w
        if pc == PathParameter:
            w = FileSelector()
            self._connectWidgetToParameter(w.lineEdit, param,
                "textChanged(QString)",
                QLineEdit.setText,
                QLineEdit.text)
            return w
        if (pc == LayerParameter or
            pc == VectorLayerParameter or
            pc == RasterLayerParameter):
            layers = self.canvas.layers()
            layerNames = [l.name() for l in layers]
            if param.role() == Parameter.Role.output:
                layerNames = [self.tr("[create]")] + layerNames
            w = QComboBox(None)
            w.addItems(layerNames)
            self._connectWidgetToParameter(w, param,
                "currentIndexChanged(int)",
                QComboBox.setCurrentIndex,
                QComboBox.currentIndex)
            return w
        if True: # default case
            w = QLineEdit(str(value), None)
            self._connectWidgetToParameter(w, param,
                "textChanged(QString)", QLineEdit.setText, QLineEdit.text)
            return w
    def _onExecButtonClicked(self):
        self.moduleinstance.setState(StateParameter.State.running)

class FileSelector(QHBoxLayout):
    def __init__(self, path = None, parent = None):
        QHBoxLayout.__init__(self, parent)
        self.lineEdit = QLineEdit(parent)
        self.button = QPushButton(self.tr("Browse..."), parent)
        QObject.connect(self.button,
            SIGNAL("clicked()"), self.onButtonClicked)
        self.addWidget(self.lineEdit)
        self.addWidget(self.button)
    def onButtonClicked(self):
        self.setPath(QFileDialog.getOpenFileName(self.button))
    def setPath(self, path):
        self.lineEdit.setText(path)
    def path(self):
        return self.lineEdit.text()
