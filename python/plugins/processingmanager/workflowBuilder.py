from PyQt4.QtGui import QDialog, QStandardItemModel,  QHBoxLayout
from PyQt4.QtCore import QString, SIGNAL,  QObject
from qgis.core import *

from gui import DiagramScene, SaveDialog
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
        self.graph = Graph()
        
        # SIGNALS and SLOTS
        QObject.connect(self.executeButton, SIGNAL("clicked()"), self._onExecuteButtonClicked)
        QObject.connect(self.saveButton, SIGNAL("clicked()"), self._onSaveButtonClicked)
        QObject.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
        QObject.connect(self.clearButton, SIGNAL("clicked()"), self._onClearButtonClicked)

    def createGraph(self):
        """
            From modules and connections in scene we will create Graph and sort Modules to Subgraphs.
        """
        modules = self.graph.modules.values()
        cons = self.graph.connections.values()
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
        self.graph.subgraphs = {}
        while modules:
            sGraph = SubGraph()
            self.graph.addSubGraph(sGraph)

            mod = modules.pop()
            findConnections(mod)

            sGraph.addModule(mod)
            sGraphCon = filter(lambda c: c.sModule in sGraph.getModules() , cons)
            sGraph.setConnections(sGraphCon)
        
    def _onExecuteButtonClicked(self):
        """
            Create Graph, check if everything is set. Execute it.
            TODO: 
                Open dialog to set inputs layers.
                There should be possibility to point which parameters should be set before executing Workflow/Graph.
        """
        self.statusBar.showMessage(QString("Executing..."),  200000)
        self.createGraph()
        if self.graph.executeGraph():
            self.statusBar.showMessage(QString("Executed successfully."),  2000)
        else:
            self.statusBar.showMessage(QString("You should set selected modules."),  5000)
            self.scene.clearSelection()
            self.scene.clearDockPanel()
            for key in self.graph._invalidSubGraph._invalidInputs.keys():
                invalidMod = self.graph._invalidSubGraph._invalidInputs[key]
                invalidPort = key
                gInvalidMod = self.scene.findGraphicsModule(invalidMod)
                if gInvalidMod:
                    gInvalidMod.setSelected(True)
                
    def _onSaveButtonClicked(self):
        """
            TODO:
                Possibility to save Graph/Workflow as new Module in Processing Framework to (re)use it.
        """
        self.statusBar.showMessage(QString("Saving..."),  2000)
        #TODO - open dialog for where user will set which parameter should be set, name of module, description, tags, ...
        #           - after accepting dialog, save it as new modul - as XML
        self.createGraph()
        if self.graph:
            svDialog = SaveDialog(self.graph, self)
            svDialog.show()

    def _onClearButtonClicked(self):
        """
            Clean the scene. Delete all modules and connections.
        """
        self.graph =Graph()
        self.scene.clearDockPanel()
        self.scene.clear()
        self.scene.modules = {}
        self.statusBar.showMessage(QString("Clear..."),  2000)
