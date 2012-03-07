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
    return """Lists available modules sorted by tag in a panel.\n
    http://polymeris.github.com/qgis/"""
    
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
        self.workflowBuilder = None
        
    def initGui(self):
        from PyQt4.QtCore import QObject, SIGNAL
        from PyQt4.QtGui import QMenu
        self.menu = QMenu()
        self.menu.setTitle(self.menu.tr("&Processing", "Processing"))

        # We only generate the panel & populate the menu when needed,
        # to increase our chances that the framework has been loaded.
        QObject.connect(self.menu, SIGNAL("aboutToShow()"),
            self.populateMenu)
        
        menuBar = self._iface.mainWindow().menuBar()   
        menuBar.insertMenu(menuBar.actions()[-1], self.menu)

    def populateMenu(self):
        from panel import Panel
        from PyQt4.QtCore import QObject, SIGNAL
        from PyQt4.QtGui import QAction
        
        if not self.panel:
            self.panel = Panel(self._iface)
            self.panel.setVisible(False)
            self.panelAction = self.panel.toggleViewAction()

            self.menu.addAction(self.panelAction)
            
            self.settingsAction = QAction(
                self.menu.tr("&Settings", "Processing"),
                self._iface.mainWindow())
            self.menu.addAction(self.settingsAction)
            QObject.connect(self.settingsAction,
                SIGNAL("triggered()"), self.showSettings)

            self.workflowBuilderAction= QAction(
                self.menu.tr("&Workflow builder", "Processing"),
                self._iface.mainWindow())
            self.menu.addAction(self.workflowBuilderAction)
            QObject.connect(self.workflowBuilderAction,
                SIGNAL("triggered()"), self.showWorkflowBuilder)

            self.aboutAction = QAction(
                self.menu.tr("&About", "Processing"),
                self._iface.mainWindow())
            self.menu.addAction(self.aboutAction)
            QObject.connect(self.aboutAction,
                SIGNAL("triggered()"), self.showAboutDialog)
    
    def unload(self):
        if self.panel:
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
        
    def showWorkflowBuilder(self):
        from workflowBuilder import WorkflowBuilder
        if not self.workflowBuilder:
            self.workflowBuilder = WorkflowBuilder(self._iface)
        self.workflowBuilder.setVisible(True)
        
def classFactory(iface):
    return ProcessingManager(iface)
