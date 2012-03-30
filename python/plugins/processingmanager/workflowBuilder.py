from PyQt4.QtGui import QDialog, QStandardItemModel,  QHBoxLayout
from PyQt4.QtCore import QString, SIGNAL,  QObject
from qgis.core import *

from gui import DiagramScene
from core import Graph, SubGraph, PortType
from ui_workflowBuilder import Ui_workflowBuilder
import processing

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class WorkflowBuilder(QDialog, Ui_workflowBuilder):
    '''
        Dialog where you can create you own Module and save it.
    '''
    def __init__(self,  iface ):
        QDialog.__init__(self,  iface.mainWindow())
        self.setupUi(self)
        self.setWindowTitle(QString("Workflow Builder v0.01alpha"))
        self.resize(800, 400)
        self.scene = DiagramScene(self)
        self.graphicsView.setScene(self.scene)
        
        # SIGNALS and SLOTS
        QObject.connect(self.executeButton, SIGNAL("clicked()"), self._onExecuteButtonClicked)
        QObject.connect(self.saveButton, SIGNAL("clicked()"), self._onSaveButtonClicked)
        QObject.connect(self.cancelButton, SIGNAL("clicked()"), self._onCancelButtonClicked)
        QObject.connect(self.clearButton, SIGNAL("clicked()"), self._onClearButtonClicked)

    def createGraph(self):
        """
            From modules and connections in scene we will create Graph and sort Modules to Subgraphs.
        """
        # get list of Modules available from 'scene'
        modules = map( lambda m: m.module,  self.scene.modules.values() )
        # get list of Connections available from 'scene'
        cons =  map ( lambda c: c.connection, self.scene.connections.values() )
        
        def findConnections(mod):
            '''
                Get Modules connected with 'mod' Module and are still avaliable from 'modules' (list of Modules getting at the begging from scene).
                mod: Module
            '''
            mods = []
            for con in cons:
                if con.sModule == mod:
                    mods.append(con.dModule)
                elif con.dModule == mod:
                    mods.append(con.sModule)
            mods = filter(lambda m: True if m in modules else False, list(set(mods)))
            #
            while mods:
                tmp = mods.pop()
                if tmp in modules:
                    modules.pop(modules.index(tmp))
                    findConnections(tmp)
                    sGraph.addModule(tmp)

        # filling Graph
        self._graph = Graph()
        while modules:
            sGraph = SubGraph()
            mod = modules.pop()
            findConnections(mod)

            sGraph.addModule(mod)
            sGraphCon = filter(lambda c: c.sModule in sGraph.getModules() , cons)
            sGraph.setConnections(sGraphCon)
            self._graph.addSGraph(sGraph)        
    
#    def createIODialog(self, inputs, outputs):
#        """
#            TODO:
#                Dialog for setting inputs layers and others parameters, if user want.
#                Move it somewhere to gui.py file.
#        """
#        dialog = QDialog(self)
#        dialog.show()
#        layout = QVBoxLayout()
#        dialog.setLayout(layout)
#        for i in inputs:
#            w = self.scene.widgetByPort(i)
#            layout.addWidget(w)
#        for i in outputs:
#            w = self.scene.widgetByPort(i)
#            layout.addWidget(w)
        
    def _onExecuteButtonClicked(self):
        """
            Create Graph, check if everything is set. Execute it.
            TODO: 
                Open dialog to set inputs layers.
                There should be possibility to point which parameters should be set before executing Workflow/Graph.
        """
        self.statusBar.showMessage(QString("Execute..."),  2000)
        self.createGraph()
        self._graph.executeGraph()        
        
    def _onSaveButtonClicked(self):
        """
            TODO:
                Possibility to save Graph/Workflow as new Module in PRocessing Framework to (re)use it.
        """
        self.statusBar.showMessage(QString("Save..."),  2000)

    def _onCancelButtonClicked(self):
        self.statusBar.showMessage(QString("Cancel..."),  2000)

    def _onClearButtonClicked(self):
        """
            Clean the scene. Delete all modules and connections.
        """
        self.scene.clearDockPanel()
        self.scene.clear()
        self.scene.modules = {}
        self.statusBar.showMessage(QString("Clear..."),  2000)
