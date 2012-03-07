import cPickle
import pickle

from PyQt4.QtGui import QDialog, QStandardItemModel 
from PyQt4.QtCore import QString #, QAbstractItemModel

from gui import DiagramScene
from ui_workflowBuilder import Ui_workflowBuilder

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s
    
#class QPortsInformationModel(QAbstractItemModel):
#    def __init__(self,  parent = None):
#        super(QPortsInformationModel, self).__init__(parent)

class WorkflowBuilder(QDialog, Ui_workflowBuilder):
    '''
        Vytvoreni vlastniho dialogu.
    '''
    def __init__(self,  iface ):
        QDialog.__init__(self,  iface.mainWindow())
        self.setupUi(self)
        self.setWindowTitle(QString("Workflow Builder v0.01alpha"))
        self.resize(800, 400)
        self.scene = DiagramScene(self)
        self.graphicsView.setScene(self.scene)
        ### information about module's ports on the right panel
        # QStandardItemModel??
        self.modelInput = QStandardItemModel()
        self.modelOutput = QStandardItemModel()
        self.treeViewIn.setModel(self.modelInput)
        self.treeViewOut.setModel(self.modelOutput)
