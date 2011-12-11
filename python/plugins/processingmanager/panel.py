# -*- coding: utf-8 -*-

#	QGIS Processing panel plugin.
#
#	panel.py (C) Camilo Polymeris
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
from dialog import Dialog
from ui_panel import Ui_dock
import processing

class ProxyModel(QSortFilterProxyModel):
    '''
    Custom proxy model for useful filtering.
    '''
    def filterAcceptsRow(self, source_row, source_parent ): 
        index = self.sourceModel().index(source_row,  0,  source_parent)
        return self.hasToBeDisplayed(index)
        
    def hasToBeDisplayed(self, index):
        result = False
        # how many child element has
        if ( self.sourceModel().rowCount(index) > 0 ):
            ii = 0
            while ( ii < self.sourceModel().rowCount(index) ):
                childIndex = self.sourceModel().index(ii, 0, index)
                if (not childIndex.isValid()):
                    break
                result = self.hasToBeDisplayed(childIndex)
                if ( result ):
                    break
                ii +=1
        else:
            useIndex = self.sourceModel().index(index.row(), 0, index.parent())
            type = self.sourceModel().data(useIndex, Qt.DisplayRole).toString()
            if ( not type.contains(self.filterRegExp()) ):
                result = False
            else:
                result = True

        return result
    
class Panel(QDockWidget, Ui_dock):
    def __init__(self, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self._iface = iface
        self._dialogs = list()
        self.setupUi(self)
        tags = list(processing.framework.usedTags())
        tags.sort()

        # use custom ProxyModel based on QSortFilterProxyModel
        self.model = QStandardItemModel(self)
        self.proxyModel = ProxyModel()
        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setFilterCaseSensitivity(0)
        self.proxyModel.setDynamicSortFilter(True)
        self.moduleList.setModel(self.proxyModel)

        # header is not nessery to visible
        self.moduleList.header().setVisible(False)
        # build list of modules and sort by tag
        self.buildModuleList(tags)
        
        self.setFloating(False)
        self._iface.addDockWidget(Qt.RightDockWidgetArea, self)

        ## connects
        # if we activated some model from a list/tree
        self.connect(self.moduleList, 
                     SIGNAL("activated(QModelIndex)"), 
                     self.activated)
        # change offer during searching the module
        self.connect(self.filterBox,
                     SIGNAL("editTextChanged(QString)"),
                     self.onFilterTextChanged)

    def onFilterTextChanged(self, string):
        self.proxyModel.setFilterRegExp(string)
        self.moduleList.expandAll()	
        if string.isEmpty():
            self.moduleList.collapseAll()
        #self.moduleList.keyboardSearch(string)

    def activated(self, index):
        if not (index.parent().data().toString().isEmpty()):	    
            module = self.moduleList.model().data(index,Qt.UserRole+1).toPyObject()
            dialog = Dialog(self._iface, module) 
            dialog.show()
        else:
            pass		


    ## The TreeWidget's items:
    def buildModuleList(self, tags):

        parentItem = self.model.invisibleRootItem()
        # a set of modules not yet added to the list
        pending = set(processing.framework.modules())
        
        for tag in tags:
                branch = QStandardItem(tag)
                modules = sorted(processing.framework.modulesByTag(tag), key=lambda x: x.name())
                for mod in modules:
                        leaf = QStandardItem(mod.name())
                        leaf.setData(mod)
                        leaf.setEditable(False)
                        branch.appendRow(leaf)
                        pending.discard(mod)
                branch.setEditable(False)
                branch.setSelectable(False)
                parentItem.appendRow(branch)
        
        branch = QStandardItem("other")
        for mod in sorted(pending, key=lambda x: x.name()):
                leaf = QStandardItem(mod.name())
                leaf.setData(mod)
                branch.appendRow(leaf)
                pending.discard(mod)
