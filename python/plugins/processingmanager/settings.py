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
from PyQt4.QtCore import Qt, QObject, SIGNAL
from ui_settings import Ui_settingsDialog
import processing

class Settings(QDialog, Ui_settingsDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        tabs = self.settingsTabs
        tabs.addTab(SettingsPage(self), self.tr("General"))
        appereancePage = AppereanceSettingsPage(self)
        tabs.addTab(appereancePage, self.tr("Appereance"))
        #for s in processing.framework.settings():
        #    tabs.addTab(SettingsPage(self), s.name())

class SettingsPage(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.setLayout(QFormLayout(self))

class AppereanceSettingsPage(SettingsPage):
    def __init__(self, parent):
        SettingsPage.__init__(self, parent)
        l = self.layout()
        showAdvanced = QCheckBox(self)
        l.addRow(
            self.tr("Allways show advanced parameters"),
            showAdvanced)
        hideUnsupported = QCheckBox(self.tr("(slow)"), self)
        l.addRow(
            self.tr("Hide unsupported modules && parameters"),
            hideUnsupported)
        tagNumber = QSlider(Qt.Horizontal, self)
        tagNumber.setMaximum(4)
        tagLabel = QLabel()
        tagNumberNames = [ self.tr(n) for n in [
            "Flat list", "Few", "More", "Many", "All"]]
        setTagLabelText = lambda n: tagLabel.setText(tagNumberNames[n])
        setTagLabelText(tagNumber.value())
        QObject.connect(tagNumber,
            SIGNAL("valueChanged(int)"),
            setTagLabelText)
        tagLayout = QHBoxLayout()
        tagLayout.addWidget(tagNumber)
        tagLayout.addWidget(tagLabel)
        l.addRow(
            self.tr("Number of tags to show"),
            tagLayout)
        
