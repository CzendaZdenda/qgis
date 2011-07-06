# -*- coding: utf-8 -*-

#	QGIS Processing panel plugin.
#
#	gui/__init__.py (C) Camilo Polymeris
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
from PyQt4.QtCore import QObject, SIGNAL, Qt
from ui_dialog import Ui_runDialog
from ui_panel import Ui_dock
import processing
from processing.parameters import *

class Panel(QDockWidget, Ui_dock):
    def __init__(self, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self._iface = iface
        self._dialogs = list()
        self.setupUi(self)
        tags = processing.framework.representativeTags()
        self.buildModuleList(tags)
    	QObject.connect(self.moduleList,
			SIGNAL("itemActivated(QTreeWidgetItem *, int)"),
			self.onItemActivated)
        self.setFloating(False)
        self._iface.addDockWidget(Qt.RightDockWidgetArea, self)
    ## The TreeWidget's items:
    class TagItem(QTreeWidgetItem):
        """ First hierarchical level: order by tags """
        def __init__(self, parent, tag = "other"):
            QTreeWidgetItem.__init__(self, parent, [tag])
    class ModuleItem(QTreeWidgetItem):
        """ Second hierarchical level: modules by name """
        def __init__(self, module):
            QTreeWidgetItem.__init__(self,[module.name()])
            self._module = module
        def module(self):
            return self._module
    def buildModuleList(self, tags):
        """ Construct the tree of modules. """
        topNode = self.moduleList
        topNode.clear()
        # a set of modules not yet added to the list
        pending = set(processing.framework.modules())
        # add a node for each tag
        for tag in tags:
            tagNode = Panel.TagItem(topNode, tag)
            # and its children
            #, sorted alphabetically
            modules = sorted(processing.framework.modulesByTag(tag),
                key=lambda x: x.name())
            for mod in modules:
                modNode = Panel.ModuleItem(mod)
                tagNode.addChild(modNode)
                pending.discard(mod)
        # add non-tagged modules
        tagNode = Panel.TagItem(topNode)
        for mod in sorted(pending, key=lambda x: x.name()):
            modNode = Panel.ModuleItem(mod)
            tagNode.addChild(modNode)
    def onItemActivated(self, item, _):
        """ This slot pops up the relevant dialog. """
        if type(item) is Panel.ModuleItem:
            dialog = Dialog(self._iface, item.module())
            self._dialogs.append(dialog)
            dialog.show()

class Dialog(QDialog, Ui_runDialog):
    def __init__(self, iface, module):
        QDialog.__init__(self, iface.mainWindow())
        self.canvas = iface.mapCanvas()
        self.moduleinstance = processing.ModuleInstance(module)
        self.setupUi(self)
        self.setWindowTitle(self.windowTitle() + " - " + module.name())
        self.text.setText(module.description())
        self.rebuildDialog()
        QObject.connect(self.moduleinstance,
            SIGNAL("parametersChanged"), self.rebuildDialog)
    def rebuildDialog(self):
        for param, value in self.moduleinstance.parameters().items():
            widget = self._widgetByType(param, value)
            self.form.addRow(param.name(), widget)
    def _connectWidgetToParameter(self, widget,
        param, signal, setter, getter):
        instance = self.moduleinstance
        QObject.connect(widget, SIGNAL(signal),
            lambda v: instance.__setitem__(param, v))
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
                QCheckBox.setChecked, QCheckBox.checked)
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
            return w
        if (pc == LayerParameter or
            pc == VectorLayerParameter or
            pc == RasterLayerParameter):
            layers = self.canvas.layers()
            layerNames = [l.name() for l in layers]
            if param.role == Parameter.Role.output:
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
                "textChanged(str)", QLineEdit.setText, QLineEdit.text)
            return w

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
