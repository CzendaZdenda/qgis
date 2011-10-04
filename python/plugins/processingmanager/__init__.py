# -*- coding: utf-8 -*-

#	QGIS Processing panel plugin.
#
#	__init__.py (C) Camilo Polymeris, Julien Malik
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

def name():
    return "Processing Framework Manager"

def description():
    return "Lists available modules sorted by tag in a panel."
    
def icon():
    import processing_rc
    return ":/icon/32"
    
def version():
    return "Version 0.1"
    
def qgisMinimumVersion():
    return "1.5" # required by MapCanvas.layers()
    
def authorName():
    return "Camilo Polymeris & Julien Malik"

class ProcessingManager:
    """ Processing plugin
    """
    def __init__(self, iface):
        self._iface = iface
        self.panel = None
        self.settings = None
        self.aboutDialog = None
        
    def initGui(self):
        from PyQt4.QtCore import QObject, SIGNAL
        from PyQt4.QtGui import QAction, QMenu
        self.menu = QMenu()
        self.menu.setTitle(self.menu.tr("Processing", "Processing"))
        
        self.panelAction = QAction(
            self.menu.tr("&Panel", "Processing"),
            self._iface.mainWindow())
        self.panelAction.setCheckable(True)
        self.menu.addAction(self.panelAction)
        QObject.connect(self.panelAction,
            SIGNAL("triggered(bool)"), self.showPanel)
        menuBar = self._iface.mainWindow().menuBar()
        
        self.settingsAction = QAction(
            self.menu.tr("&Settings", "Processing"),
            self._iface.mainWindow())
        self.menu.addAction(self.settingsAction)
        QObject.connect(self.settingsAction,
            SIGNAL("triggered()"), self.showSettings)
        
        self.aboutAction = QAction(
            self.menu.tr("&About", "Processing"),
            self._iface.mainWindow())
        self.menu.addAction(self.aboutAction)
        QObject.connect(self.aboutAction,
            SIGNAL("triggered()"), self.showAboutDialog)
        
        menuBar.insertMenu(menuBar.actions()[-1], self.menu)
        
    def unload(self):
        if self.panel is not None:
            self.panel.setVisible(False)
            
    def showSettings(self):
        from settings import Settings
        if not self.settings:
            self.settings = Settings(self._iface.mainWindow())
        self.settings.setVisible(True)
    
    def showAboutDialog(self):
        from aboutdialog import AboutDialog
        if not self.aboutDialog:
            self.aboutDialog = AboutDialog(self._iface.mainWindow())
        self.aboutDialog.setVisible(True)
        
    def showPanel(self, visible = True):
        from panel import Panel
        from PyQt4.QtCore import QObject, SIGNAL
        if not self.panel:
            self.panel = Panel(self._iface)
            QObject.connect(self.panel,
                SIGNAL("visiblityChanged(bool)"),
                self.panelAction.setChecked)
        self.panel.setVisible(visible)

def classFactory(iface):
    return ProcessingManager(iface)
