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
from qgis.core import *

class Dialog(QDialog, Ui_runDialog):
    def __init__(self, iface, module):
        QDialog.__init__(self, iface.mainWindow())
        layerRegistry = QgsMapLayerRegistry.instance()
        self.mapLayers = layerRegistry.mapLayers().values()
        self.vectorLayers = filter(
            lambda x: x.type() == QgsMapLayer.VectorLayer,
            self.mapLayers)
        self.rasterLayers = filter(
            lambda x: x.type() == QgsMapLayer.RasterLayer,
            self.mapLayers)
        
        self.moduleinstance = module.instance()
        self.setupUi(self)
        
        self.setWindowTitle(self.windowTitle() + " - " + module.name())
        self._fillTextTab(module)
        self.execButton = QPushButton(self.tr("&Execute"));
        self.execButton.setDefault(True)
        self.buttons.addButton(self.execButton, QDialogButtonBox.ActionRole);
        self.rebuildDialog()
        self.advancedScroll.hide()
        self.progressBar = QProgressBar()
        self.statusBar.addPermanentWidget(self.progressBar)
        self.progressBar.hide()
        
        # Rebuild the dialog if parameter structure changes.
        QObject.connect(self.moduleinstance,
            self.moduleinstance.valueChangedSignal(),
            self.rebuildDialog)
        QObject.connect(self.moduleinstance,
            self.moduleinstance.valueChangedSignal(self.moduleinstance.feedbackParameter),
            self.onFeedbackChange)
        QObject.connect(self.moduleinstance,
            self.moduleinstance.valueChangedSignal(self.moduleinstance.progressParameter),
            self.onProgressChange)
        QObject.connect(self.moduleinstance,
            self.moduleinstance.valueChangedSignal(self.moduleinstance.stateParameter),
            self.onStateChange)
        # Start module instance on button click
        QObject.connect(self.execButton, SIGNAL("clicked()"),
            self._onExecButtonClicked)
    def _fillTextTab(self, module):
        mDesc = module.description()
        pWithDesc = filter(lambda p: p.description(), module.parameters())
        if not (mDesc or pWithDesc):
            self.tabWidget.removeTab(1)
            return
        mTitle = "Module <em>%s</em>" % module.name()
        text = "<h1 class='module'>%s</h1>" % mTitle
        tags = ", ".join(module.tags())
        text += "<p class='tags'><small>%s</small></p>" % tags
        text += "<p class='module'>%s</p>" %  mDesc
        for p in pWithDesc:
            pTitle = "Parameter <em>%s</em>" % p.name()
            text += "<h2 class='param'>%s</h2>" % pTitle
            text += "<p class='param'>%s</p>" % p.description()
        self.text.setText("<html><body>%s</body></html>" % text)
    def rebuildDialog(self):
        for param in self.moduleinstance.module().parameters():
            value = self.moduleinstance[param]
            label = param.name()
            if param.role() == Parameter.Role.output:
                label = '&gt; %s' % label
            label = '<html>%s</html>' % label
            widget = self._widgetByType(param, value)
            if widget is None:
                continue
            if param.isMandatory():
                self.mandatoryForm.addRow(label, widget)
                continue
            if param.userLevel() == Parameter.UserLevel.basic:
                self.optionalForm.addRow(label, widget)
                continue
            self.advancedForm.addRow(label, widget)
        if not self.mandatoryForm.rowCount():
            self.mandatoryTab.hide()
        if not (self.optionalForm.rowCount() +
            self.advancedForm.rowCount()):
                self.optionalTab.hide()
        if not self.advancedForm.rowCount():
            self.advancedButton.hide()
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
            w = param.widget(value)
            self._connectWidgetToParameter(w, param,
                "valueChanged", type(w).setValue, type(w).value)
            return w
        except NotImplementedError:
            pass
        pc = param.__class__
        if pc == StateParameter:
            return None
        if pc == FeedbackParameter:
            return None
        if pc == NumericParameter:
            w = QDoubleSpinBox(None)
            val = param.validator()
            if val:
                w.setRange(val.bottom(), val.top())
            w.setValue(value)
            self._connectWidgetToParameter(w, param,
                "valueChanged(double)",
                QDoubleSpinBox.setValue, QDoubleSpinBox.value)
            return w
        if pc == RangeParameter:
            w = RangeBox(None)
            w.setValue(value)
            self._connectWidgetToParameter(w, param,
                "valueChanged", RangeBox.setValue, RangeBox.value)
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
        if pc == LayerParameter:
            layers = self.mapLayers
        if pc == VectorLayerParameter:
            layers = self.vectorLayers
        if pc == RasterLayerParameter:
            layers = self.rasterLayers
        if (pc == LayerParameter or
            pc == VectorLayerParameter or
            pc == RasterLayerParameter):
            w = LayerComboBox(layers)
            self._connectWidgetToParameter(w, param,
                "currentLayerChanged",
                LayerComboBox.setCurrentLayer,
                LayerComboBox.currentLayer)
            return w
        if True: # default case
            w = QLineEdit(str(value), None)
            self._connectWidgetToParameter(w, param,
                "textChanged(QString)", QLineEdit.setText, QLineEdit.text)
            return w
    def _onExecButtonClicked(self):
        self.moduleinstance.setState(StateParameter.State.running)
    def onFeedbackChange(self, fb):
        self.statusBar.showMessage(fb)
        self.logText.append("%s<br/>" % fb)
    def onProgressChange(self, p):
        if p is None:
            self.progressBar.hide()
        else:
            self.progressBar.show()
            self.progressBar.setValue(p)
    def onStateChange(self, state):
        if state == StateParameter.State.running:
            #self.execButton.setEnabled(False)
            pass
        if state == StateParameter.State.stopped:
            pass
            #self.execButton.setEnabled(True)
            #self.setVisible(False)

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

class LayerComboBox(QComboBox):
    def __init__(self, layers, parent = None):
        QComboBox.__init__(self, parent)
        self.setLayers(layers)
        self.connect(self, SIGNAL("currentIndexChanged(int)"),
            self.onCurrentIndexChanged)
    def setLayers(self, layers):
        self.layers = list(layers)
        self.layers.insert(0, None)
        layerNames = list()
        for l in self.layers:
            if not l:
                layerNames.append(self.tr("- none selected -"))
            else:
                layerNames.append(l.name())
        self.clear()
        self.addItems(layerNames)
    def currentLayer(self):
        return self.layers[self.currentIndex()]
    def setCurrentLayer(self, layer):
        try:
            ix = self.layers.index(layer)
        except:
            self.layers.append(layer)
            self.setLayers(self.layers)
            ix = self.layers.index(layer)
        self.setCurrentIndex(ix)
    def onCurrentIndexChanged(self, ix):
        self.emit(SIGNAL("currentLayerChanged"), self.layers[ix])

class RangeBox(QHBoxLayout):
    def __init__(self, values = None, parent = None):
        QHBoxLayout.__init__(self, parent)
        self.lowBox = QDoubleSpinBox(parent)
        self.highBox = QDoubleSpinBox(parent)
        try:
            from sys import float_info
            fMin = float_info.min
            fMax = float_info.max
        except ImportError:
            # workaround for py < 2.6
            fMin = 10**-38
            fMax = 10**38
        self.lowBox.setMinimum(fMin)
        self.highBox.setMaximum(fMax)
        self.addWidget(self.lowBox)
        self.addWidget(self.highBox)
        if values:
            self.setValue(values)
        QObject.connect(self.lowBox,
            SIGNAL("valueChanged(int)"), self.onLowValueChanged)
        QObject.connect(self.highBox,
            SIGNAL("valueChanged(int)"), self.onHighValueChanged)
    def setValue(self, values):
        low, high = sorted(values)
        self.lowBox.setValue(low)
        self.highBox.setValue(high)
        self.lowBox.setMaximum(high)
        self.highBox.setMinimum(low)
    def value(self):
        low = self.lowBox.value()
        high = self.highBox.value()
        return (low, high)
    def onLowValueChanged(self, value):
        self.highBox.setMinimum(value)
        self.emit(SIGNAL("valueChanged"), self.value())
    def onHighValueChanged(self, value):
        self.lowBox.setMaximum(value)
        self.emit(SIGNAL("valueChanged"), self.value())

class ListParameterBox(QGridLayout):
    """ The getter parameter must be a function that returns a
    string or QListWidgetItem when passed an instance of itemWidget.
    """
    def __init__(self, itemWidget, getter, parent = None):
        QGridLayout.__init__(self, parent)
        self.itemWidget = itemWidget
        self.getter = getter
        self.addButton = QPushButton(self.tr("Add"), parent)
        self.removeButton = QPushButton(self.tr("Remove"), parent)
        self.listBox = QListWidget(parent)
        QObject.connect(self.addButton,
            SIGNAL("clicked()"), self.onAddButtonClicked)
        QObject.connect(self.removeButton,
            SIGNAL("clicked()"), self.onRemoveButtonClicked)
        self.addWidget(self.itemWidget, 0, 0)
        self.addWidget(self.addButton, 0, 1)
        self.addWidget(self.removeButton, 0, 2)
        self.addWidget(self.listBox, 1, 0, -1, -1)
    def onAddButtonClicked(self):
        self.listBox.addItem(self.getter(self.itemWidget))
    def onRemoveButtonClicked(self):
        self.listBox.removeItemWidget(self.listBox.currentItem())
