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
from PyQt4.QtCore import QObject, SIGNAL, Qt,  QString
from dialog import Dialog
from ui_panel import Ui_dock
import processing

class ProxyModel(QSortFilterProxyModel):
    '''
    Custom proxy model for useful filtering.
    '''
    def filterAcceptsRow( self, source_row, source_parent ): 
        '''
        Re-implementation of QSortFilterProxyModel's' filterAcceptsRow( self, source_row, source_parent ) function.
        It uses not only 'name' of the item, but also tags of item/modul.
        '''
        result = False
        
        useIndex = self.sourceModel().index(source_row,  0,  source_parent)
        name = self.sourceModel().data(useIndex, Qt.DisplayRole).toString()

        if ( name.contains(self.filterRegExp()) ):
            result = True
        else:
            # searching in tags 
            # TODO: searching in description?
            mod = self.sourceModel().data(useIndex, Qt.UserRole+1).toPyObject()
            for tag in mod.tags():
                tag = QString(tag)
                if ( tag.contains(self.filterRegExp()) ):
                    result = True
                    break
        return result
    
class Panel(QDockWidget, Ui_dock):
    def __init__(self, iface):
        QDockWidget.__init__(self, iface.mainWindow())
        self._iface = iface
        self._dialogs = list()
        self.setupUi(self)
        tags = list(processing.framework.usedTags())
        tags.sort()

        # use custom ProxyModel based on QSortFilterProxyModel where source model is QStandardItemModel
        self.listModel = QStandardItemModel(self)        
        self.proxyModel = ProxyModel()
        self.proxyModel.setSourceModel(self.listModel)
        self.proxyModel.setFilterCaseSensitivity(0)
        self.proxyModel.setDynamicSortFilter(True)
        
        # tree-based model, which is default for our view (QTreeView)
        self.treeModel = QStandardItemModel(self)
        self.moduleList.setModel(self.treeModel)
        
        # header is not necessary to visible
        self.moduleList.header().setVisible(False)
        
        # build tree of modules sorted by tag
        self.buildModuleTree(tags)
        # build list of modules
        self.buildModuleList()
        
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
        '''
        If string is not empty -> change model in treeView from tree model to list model. Then start filtering/searching.
        '''
        self.moduleList.setModel(self.proxyModel)
        self.proxyModel.setFilterRegExp(string)
        if string.isEmpty():
            self.moduleList.setModel(self.treeModel)
        #self.moduleList.keyboardSearch(string)

    def activated(self, index):
        '''
        After activated item from list, appropriate dialog will appear.
        '''
        if not ( index.parent().data().toString().isEmpty() ) or not ( isinstance(index.model(), QStandardItemModel) ):	    
            module = self.moduleList.model().data(index,Qt.UserRole+1).toPyObject()
            dialog = Dialog(self._iface, module) 
            dialog.show()
        else:
            pass

    def buildModuleTree(self, tags):
        '''
        Build tree model, where tags will be branches and modules leaves.
        '''
        parentItem = self.treeModel.invisibleRootItem()
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
        # if there are some modules without tags
        branch = QStandardItem("other")
        for mod in sorted(pending, key=lambda x: x.name()):
                leaf = QStandardItem(mod.name())
                leaf.setData(mod)
                branch.appendRow(leaf)
                pending.discard(mod)
        branch.setEditable(False)
        branch.setSelectable(False)
        parentItem.appendRow(branch)

    def buildModuleList(self):
        '''
        Build list model of modules. This model is used for filtering/searching.
        '''
        # take all available modules 
        modules = set(processing.framework.modules())
        
        for mod in  modules:
            item = QStandardItem(mod.name())
            item.setData(mod)
            item.setEditable(False)
            item.setSelectable(False)
            self.listModel.appendRow(item)

        self.listModel.sort(0)
