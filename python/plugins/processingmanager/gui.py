# inspired by VisTrails

import copy
import math
import cPickle
import pickle

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.Qt import *

from qgis.core import *
from qgis.utils import *

from core import PortType,  Connection,  Module,  Port,  Graph
import processingplugin
import processing
from processing.parameters import *
from ui_savedialog import Ui_savedialog

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

# some graphics parameters...
PORT_WIDTH = 10
PORT_HEIGHT = 10
MODULE_PEN = QPen( QBrush( QColor(Qt.black )), 2)
MODULE_SELECTED_PEN = QPen( QBrush( QColor(Qt.darkYellow) ), 3 )
MODULE_LABEL_SELECTED_PEN = QPen( QBrush( QColor(Qt.black)),  2 )
MODULE_LABEL_PEN = QPen( QBrush( QColor(Qt.black)),  2 )
BREAKPOINT_MODULE_BRUSH = QPen( QBrush( QColor(Qt.black)),  2 )
MODULE_LABEL_MARGIN = (20, 20, 20, 15)
MODULE_PORT_MARGIN = (4, 4, 4, 4)
MODULE_PORT_SPACE = 4
MODULE_PORT_PADDED_SPACE = 20
CONNECTION_PEN = QPen( QBrush( QColor(Qt.black), 2 ) )
CONNECTION_SELECTED_PEN = QPen( QBrush( QColor(Qt.yellow ), 3 ) )

def widgetByPort(port, save=False):
    widget = QWidget(None)
    wVLayout = QVBoxLayout(widget)
    wHLayout = QHBoxLayout()
    
    # add name to layout
    if port.portType is PortType.Destination:
        label = QLabel(QString("{0}".format(port.name)))
    elif port.portType is PortType.Source:
        label = QLabel(QString("> {0}".format(port.name)))
        label.setToolTip("output")
    wVLayout.addWidget(label)
        
    if (save):
        # Add checkbox            > if Layer - disable - connected with Port to set setIt atribute
        checkSetIt = QCheckBox()
        QObject.connect(checkSetIt, SIGNAL("toggled(bool)"), lambda v: port.setSetIt(v) )
        # everytime user has to set raster and vector layers, so there is no choice
        if ( port.type == processing.parameters.LayerParameter or port.type == processing.parameters.VectorLayerParameter or port.type == processing.parameters.RasterLayerParameter):
            checkSetIt.setEnabled(False)
            checkSetIt.setChecked(True)
    
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(checkSetIt.sizePolicy().hasHeightForWidth())
        checkSetIt.setSizePolicy(sizePolicy)
        checkSetIt.setTristate(False)
        
        wHLayout.addWidget(checkSetIt)
    else:
        pass

    # Add parameterValue  > if Layer - disable     
    pc = port.type
    value = port.getValue()
    w = None
    if pc == processing.parameters.StateParameter:
        pass
    if pc == processing.parameters.FeedbackParameter:
        pass
    if pc == processing.parameters.NumericParameter:
        w = QDoubleSpinBox(None)
        w.setValue(value)
        QObject.connect(w,  SIGNAL("valueChanged(double)"), lambda v: port.setValue(v))
    if pc == processing.parameters.RangeParameter:
        w = RangeBox(None)
        w.setValue(value)
        QObject.connect(w,  SIGNAL("valueChanged"), lambda v: port.setValue(v))
    if pc == processing.parameters.BooleanParameter:
        w = QCheckBox(None)
        w.setChecked(value)
        QObject.connect(w,  SIGNAL("toggled(bool)"), lambda v: port.setValue(v))

    if pc == processing.parameters.ChoiceParameter:
        w = QComboBox(None)
        w.addItems(port.getData())
        w.setCurrentIndex(value)
        QObject.connect(w,  SIGNAL("currentIndexChanged(int)"), lambda v: port.setValue(v))

    if pc == processing.parameters.PathParameter:
        w = FileSelector()
        if value:
            w.setPath(value)
        QObject.connect(w.lineEdit,  SIGNAL("textChanged(QString)"), lambda v: port.setValue(v))
    if (pc == processing.parameters.LayerParameter or
        pc == processing.parameters.VectorLayerParameter or
        pc == processing.parameters.RasterLayerParameter):
        layerRegistry = QgsMapLayerRegistry.instance()
        mapLayers = layerRegistry.mapLayers().values()
        vectorLayers = filter( lambda x: x.type() == QgsMapLayer.VectorLayer, mapLayers)
        rasterLayers = filter( lambda x: x.type() == QgsMapLayer.RasterLayer, mapLayers)               
        if pc == processing.parameters.LayerParameter:
            layers = mapLayers
        if pc == processing.parameters.VectorLayerParameter:
            layers = vectorLayers
        if pc == processing.parameters.RasterLayerParameter:
            layers = rasterLayers
            
        w = LayerComboBox(layers)
        if value:
            w.setCurrentLayer(value)
        if (save):
            w.setEnabled(False)
        QObject.connect(w,  SIGNAL("currentLayerChanged"), lambda v: port.setValue(v))
    if w is None: # default case
        w = QLineEdit(str(value), None)
        QObject.connect(w,  SIGNAL("textChanged(QString)"), lambda v: port.setValue(v))

    if w.isWidgetType():
        wHLayout.addWidget(w)
    else:
        wHLayout.addLayout(w)

    if not save and not port.isEmpty():
        isChained = QLabel()
        pixmap = QPixmap(_fromUtf8(":/icon/chain"))
        isChained.setMaximumSize(QSize(24, 24))
        isChained.setPixmap(pixmap)
        isChained.setToolTip("is connected with other parameter")
        wHLayout.addWidget(isChained)


    if (save):
        alternativeName = QLineEdit("Alternative name for parameter", None)
        QObject.connect( alternativeName,  SIGNAL("textChanged(QString)"), lambda v: port.setAlternativeName(v) )
        wHLayout.addWidget( alternativeName )
        
    wVLayout.addLayout(wHLayout)
    # if it is output layer, we can set name of layer and if we want add it to canvas
    if port.portType == PortType.Source and (port.type == processing.parameters.VectorLayerParameter or port.type == processing.parameters.RasterLayerParameter):
        # Add checkbox  > 
        outputHLayout = QHBoxLayout()
        checkAddIt = QCheckBox()
        QObject.connect(checkAddIt, SIGNAL("toggled(bool)"), lambda v: port.setAddItToCanvas(v) )
        newName = QLineEdit("{0}".format(port.name), None)
        QObject.connect(newName,  SIGNAL("textChanged(QString)"), lambda v: port.setOutputName(v))
        outputHLayout.addWidget(checkAddIt)
        outputHLayout.addWidget(newName)
        wVLayout.addLayout(outputHLayout)

    return widget
    

class SaveDialog(QDialog,  Ui_savedialog):
    def __init__(self, graph, parent=None ):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(QString("Workflow Builder - save workflow as new module"))
        self.graph = graph    
        # prepare dialog
        self.prepareDialog()
        QObject.connect(self.buttonBox, SIGNAL("accepted()"), self.saveWorkflow)

    def prepareDialog(self):
        for sub in self.graph.subgraphs.values():
            for mod in sub.getModules():
                label = QLabel( QString("{0}".format(mod.label)) )
                self.formParameters.addRow(label)
                for port in mod.getPorts(PortType.Destination):
                    if port.empty:
                        widget = widgetByPort(port,  save=True)
                        self.formParameters.addRow(widget)
                        
    def saveWorkflow(self):
        self.graph.name = self.lineEditName.text()
        if self.graph.name == "":
            msgBox = QMessageBox(self)
            msgBox.setText("You have to type name of your new module.")
            msgBox.show()
            #msgBox.exec_()
        else:
            # TODO: check whether exist file with this name
            self.graph.description = self.description.toPlainText()
            self.graph.tags = str( self.lineEditTags.text() ).split( "," )
            self.graph.save()
            #TODO: after saving load it into PF Manager
            reloadPlugin('workflow_builder')
            reloadPlugin('processingplugin')
        
class GraphicsView(QGraphicsView):
    '''
        QGraphicsView.
        It accepts drags and drops.
        It handles inserting/creating modules (Module) and key press events.
    '''
    def __init__(self,  parent = None ):
        super(GraphicsView, self).__init__(parent)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.Antialiasing)
        
    def wheelEvent(self, event):
        factor = 1.41 ** (-event.delta() / 240.0)
        self.scale(factor, factor)
    
    # Drag & Drop
    def dragEnterEvent(self, event):
        """
            Accept drag.
        """
        event.accept()

    def dragMoveEvent(self, event):
        """
            Accept moving with dragged item.
        """
        event.accept()

    def dropEvent(self,event):
        """
            Accept dropped items, that were dragged from QModuleTreeList.
        """
        if (type( event.source() ) == processingplugin.ui_panel.QModuleTreeView):
            try:
                # Get PF modul from QModuleTreeView.
                d = event.mimeData()
                b = d.retrieveData("application/x-pf", QVariant.ByteArray)
                pfM = pickle.loads(b.toByteArray())
        
                index2 = event.source().indexAt(pfM)
                module = event.source().model().data(index2,Qt.UserRole+1).toPyObject()
                # in scene Module and QGraphicsModuleItem will be create from PF Module
                self.scene().addModule(module, event.pos())
            except:
                pass
        
    def keyPressEvent(self, event):
        """
            If user press Del-key, remove module or connection from workflow if possible.
        """
        if event.key() == Qt.Key_Delete:
            delItems = self.scene().selectedItems()
            if (delItems):
                self.scene().clearDockPanel()
                for item in delItems:
                    if isinstance(item, QGraphicsModuleItem):
                        # remove module
                        self.scene().delModule(item)
                    elif isinstance(item, QGraphicsConnectionItem):
                        # remove connection
                        self.scene().delConnection(item)

        self.parent().statusBar.showMessage(QString(event.text()), 2000)

    
        event.accept()

class DiagramScene(QGraphicsScene):
    '''
        QGraphicsScene.
    '''
    def __init__(self,  parent = None):
        super(DiagramScene,  self).__init__(parent)
        self.line = 0
        self.textItem = 0
        self.myItemColor = Qt.white
        self.myTextColor = Qt.black
        self.myLineColor = Qt.black
        # from VisTrails
        self.modules = {}
        self.connections = {}
        self.justClick = False
        self.graph = Graph()
        
    # VisTrails
    def addModule(self, mod, position = QPointF(100, 100), moduleBrush=None):
        """ 
        module: Module
        position: QPointF
        moduleBrush: QBrush
        -> QGraphicsModuleItem
        Add a module to the scene 
        """
        # first ve create Module and after that, we create QGraphicsModuleItem
        ports = mod.parameters()
        # create workflow builder module
        module = Module()
        # now we add Module to Graph (Graph is store in WorkflowBuilder)
        self.parent().graph.addModule(module)
        module.label = mod.name()
        module.description = mod.description()
        for tag in list(mod.tags()):
            module.tags.append(tag)
        module.tags = list( mod.tags() )
        
        # add Ports into Module
        for i in ports:
            if (i.role() == processing.parameters.Parameter.Role.input ):
                PType = PortType.Destination
            elif (i.role() == processing.parameters.Parameter.Role.output ):
                PType = PortType.Source
            else:
                pass
            
            tmpPort = None
            if i.isMandatory():
                tmpPort = Port(i.defaultValue(), PType, i.__class__,  module.id, i.name())
            else:
                tmpPort = Port(i.defaultValue(), PType, i.__class__,  module.id, i.name(), True)
            if i.__class__ == ChoiceParameter:
                tmpPort.setData(i.choices())
            tmpPort.description = i.description()
            tmpPort.parameterInstance = i
            
            module.addPort(tmpPort)
        
        # create QGraphicsModuleItem
        moduleItem = QGraphicsModuleItem(None)
        moduleItem.setupModule(module)
        moduleItem.setPos(QPointF(position))
        if moduleBrush:
            moduleItem.moduleBrush = moduleBrush
        self.addItem(moduleItem)
        self.modules[module.id] = moduleItem        

    def addConnection(self, connection):
        """ 
        connection: Connection
        -> QGraphicsConnectionItem
        Add connection to the scene.        
        """
        srcModule = self.modules[connection.source.moduleId]
        dstModule = self.modules[connection.destination.moduleId]
        srcPoint = srcModule.getOutputPortPosition(connection.source)
        dstPoint = dstModule.getInputPortPosition(connection.destination)
        connectionItem = QGraphicsConnectionItem(srcPoint, dstPoint, srcModule, dstModule, connection)
        connectionItem.id = connection.id
        connectionItem.connection = connection
        self.addItem(connectionItem)
        
        self.connections[connection.id] = connectionItem
        #self._old_connection_ids.add(connection.id)
        return connectionItem

        
    def mousePressEvent(self, mouseEvent):
        '''
            If user clicks on a port/parameter, we make the curve, that connects this port with another.
        '''
        self.clearDockPanel()
        QGraphicsScene.mousePressEvent(self, mouseEvent)
        if mouseEvent.button() == Qt.LeftButton:            
            self.justClick = True
            items = self.items(mouseEvent.scenePos())
            for i in items:
                if (type(i) == QGraphicsPortItem):
                    self.line = QGraphicsLineItem(QLineF(mouseEvent.scenePos(), mouseEvent.scenePos()))
                    self.line.setPen(QPen(self.myLineColor, 2))
                    self.addItem(self.line)
                    break

    def mouseMoveEvent(self,  mouseEvent):
        self.justClick = False
        if self.line != 0:
            newLine = QLineF(self.line.line().p1(), mouseEvent.scenePos())
            self.line.setLine(newLine)
        else :
            QGraphicsScene.mouseMoveEvent(self, mouseEvent)
        
    def mouseReleaseEvent(self, mouseEvent):
        """
            Alter release mouse, we want:
                show parameters of Module
                show parameters of Port
                finish connection
        """        
        QGraphicsScene.mouseReleaseEvent(self, mouseEvent)
        if mouseEvent.button() == Qt.LeftButton:
            
            if not self.justClick:
                '''
                    Some line is prepare, so try to make connection.
                '''
                items = self.items(mouseEvent.scenePos())
                # preparing variable for making connection
                startPort = None
                endPort = None
                startModule = None
                endModule = None
    
                for item in items:
                    '''
                        Looking for source port - QGraphicsPortItem.
                    '''
                    if self.line and (type(item) == QGraphicsPortItem):
                        items2 = self.items(self.line.line().p1())
                        endModule = item.findModuleUnder(item.scenePos()).module
                        endPort = item.port
                        for item2 in items2:
                            '''
                                Looking for destination port - QGraphicsPortItem.
                            '''
                            if type(item2) == QGraphicsPortItem:

                                startPort = item2.port
                                startModule = item2.findModuleUnder(item2.scenePos()).module
                        # one port shloud be Source, the other one Destination and both should be of same type (like Numeric, Raster, ...)
                        if startPort.type == endPort.type and startPort.portType != endPort.portType and startModule.id != endModule.id and startPort.isEmpty() and endPort.isEmpty():
                            # test if startPoint is really source point of connection, otherwise switch them
                            if startPort.portType != PortType.Source:
                                tmp = endPort
                                endPort = startPort
                                startPort = tmp
                                tmp = endModule
                                endModule = startModule
                                startModule = tmp
                            # connect ports/modules by Connection
                            con = Connection(startPort, endPort, startModule,  endModule)
                            self.parent().graph.addConnection(con)
                            self.addConnection(con)
                            
                            # start port could be source for more then one destination/end port, but destination have to have just one input
                            #startPort.setEmpty(False)
                            endPort.setEmpty(False)
                            
                if self.line:
                    try:
                        self.removeItem(self.line)
                    except:
                        pass
                    self.line = 0
            else:
                '''
                    There is no line. User probably want to see/set informations/parameters of Module/Port.
                '''
                items = self.items(mouseEvent.scenePos())
                if len(items):
                    '''
                        User really wants to do smth.
                    '''
                    tmpPort = None
                    tmpModule = None
                    for i in items:
                        if (type(i) == QGraphicsPortItem):
                            tmpPort = i
                            break
                        elif (type(i) == QGraphicsModuleItem):
                            tmpModule = i
                            
                    if (tmpPort):
                        '''
                            Give information about port.
                        '''
                        port = tmpPort.port
                        self.parent().item.setText(QString("Port - %s" % (port.name) ))
                        self.parent().textEditDesc.setText(QString("{1} --> {0}, {2}".format(port.description, port.type, port.getValue())))
                        self.parent().toolBox.setCurrentIndex(1)
                        self.parent().toolBox.setCurrentIndex(1)
                        self.parent().toolBox.setItemEnabled(0, False)

                    elif (tmpModule):
                        """
                            Give information about module.
                        """
                        module = tmpModule.module
                        self.parent().item.setText(QString("Module - %s" % (module.label)))
                        self.parent().textEditDesc.setText(module.description)
                        self.parent().toolBox.setCurrentIndex(0)
                        self.parent().toolBox.setItemEnabled(0, True)
                        # devide mandatory and optional ports/parameters 
                        for port in module._ports.values():
                            widget = widgetByPort(port)
                            if port.optional:
                                self.parent().optionalForm.addRow(widget)
                            else:
                                self.parent().mandatoryForm.addRow(widget)

            self.justClick = False
        
    def clearDockPanel(self):
        for w in self.parent().mandatoryWidget.children():
            if w.isWidgetType():
                w.setParent(None)
                del(w)
        for w in self.parent().optionalWidget.children():
            if w.isWidgetType():
                w.setParent(None)
                del(w)
        self.parent().item.setText(QString("Item"))
        self.parent().textEditDesc.clear()
    def delModule(self, item):
        """
            Remove module from scene and graph . Also remove connection and clean after that.
        """
        for con in item.dependingConnectionItems():         
            con[0].delConnectionItem(con)
            self.removeItem(con[0])
            del self.parent().graph.connections[con[0].id]
#            for i, n in self.connections.iteritems():
#                if n == con:
#                    del self.connections[i]
#                    break

        self.removeItem(item)
        del self.modules[item.module.id] 
        del self.parent().graph.modules[item.module.id]

    def delConnection(self, con):
        con.delConnectionItem(con)
        self.removeItem(con)
        for i, n in self.connections.iteritems():
            if n == con:
                del self.connections[i]
                del self.parent().graph.connections[i]
                break

    def findGraphicsModule(self, mod):
        return self.modules[mod.id]
class FileSelector(QHBoxLayout):
    def __init__(self, path = None, parent = None):
        QHBoxLayout.__init__(self, parent)
        self.lineEdit = QLineEdit(parent)
        self.button = QPushButton(self.tr("Browse..."), parent)
        QObject.connect(self.button, SIGNAL("clicked()"), self.onButtonClicked)
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
        self.connect(self, SIGNAL("currentIndexChanged(int)"), self.onCurrentIndexChanged)
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
        QObject.connect(self.lowBox, SIGNAL("valueChanged(double)"), self.onLowValueChanged)
        QObject.connect(self.highBox, SIGNAL("valueChanged(double)"), self.onHighValueChanged)
        
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


class QGraphicsPortItem(QGraphicsRectItem):
    '''
        Port - input/output of the module.
    '''
    def __init__(self, x, y, parent = None,  optional = False):
        _rect = QRectF(0, 0, PORT_WIDTH, PORT_HEIGHT)
        QGraphicsRectItem.__init__(self,  _rect.translated(x, y), parent)
        self.setZValue(1)
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        
        if not optional:
            self.paint = self.paintRect
        else:
            self.paint = self.paintEllipse            
        
    def findModuleUnder(self, pos, scene=None):
        if scene is None:
            scene = self.scene()
        itemsUnder = scene.items(pos)
        for item in itemsUnder:
            if type(item) == QGraphicsModuleItem:
                return item
        return None
        
    def paintEllipse(self, painter, option, widget=None):
        """ paintEllipse(painter: QPainter, option: QStyleOptionGraphicsItem,
                  widget: QWidget) -> None
        Peform actual painting of the optional port
        
        """
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawEllipse(self.rect())

    def paintRect(self, painter, option, widget=None):
        """ paintRect(painter: QPainter, option: QStyleOptionGraphicsItem,
                  widget: QWidget) -> None
        Peform actual painting of the regular port
        
        """
        QGraphicsRectItem.paint(self, painter, option, widget)

class QGraphicsModuleItem(QGraphicsItem):
    def __init__(self, parent=None, scene=None):
        """ QGraphicsModuleItem(parent: QGraphicsItem, scene: QGraphicsScene)
                                -> QGraphicsModuleItem
        Create the shape, initialize its pen and brush accordingly
        
        """
        QGraphicsItem.__init__(self, parent, scene)
        self.paddedRect = QRectF(0, 0, 100, 60)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(0)
        self.labelFont = QFont("Arial", 12, QFont.Bold)
        self.labelFontMetric = QFontMetrics(self.labelFont)
        self.descFont = QFont("Arial", 10)
        self.descFontMetric = QFontMetrics(self.descFont)
        self.modulePen = QPen( QBrush( Qt.black ) , 2 )
        self.moduleBrush = QBrush(Qt.lightGray)
        self.labelPen = QPen(QBrush(Qt.black), 2)
        self.customBrush = None
        self.statusBrush = None
        self.labelRect = QRectF()
        self.descRect = QRectF()
        self.abstRect = QRectF()
        self.id = -1
        self.label = ''
        self.description = ''
        self.inputPorts = {}
        self.outputPorts = {}
        self.controller = None
        self.module = None
        self.ghosted = False
        self.invalid = False
        self._module_shape = None
        self._original_module_shape = None
        self._old_connection_ids = None
        self.errorTrace = None
        self.is_breakpoint = False
        self._needs_state_updated = True
        self.progress = 0.0
        self.progressBrush = QBrush( QColor(Qt.green))
        # list of Connection
        self.connections = []
        
    def addConnection(self, con, tf):
        """
            con: Connection
            tf: bool
        """
        self.connections.append((con, tf))

    def delConnection(self, con):
        for connection in self.connections:
            if isinstance(con, tuple):
                if connection[0] == con[0]:
                    self.connections.pop(self.connections.index(connection))
                    break
            elif isinstance(con, QGraphicsConnectionItem):
                if connection[0] == con:
                    self.connections.pop(self.connections.index(connection))
                    break

    def boundingRect(self):
        try:
            r = self.paddedRect.adjusted(-2, -2, 2, 2)
        except:
            r = QRectF()
        return r

    def setPainterState(self):
            self.modulePen = MODULE_SELECTED_PEN
            self.labelPen = MODULE_LABEL_SELECTED_PEN
            self.moduleBrush = BREAKPOINT_MODULE_BRUSH

    
    def computeBoundingRect(self):
        """ computeBoundingRect() -> None
        Adjust the module size according to the text size
        
        """
        labelRect = self.labelFontMetric.boundingRect(self.label)
        if self.module.tags:
            tmp = ""
            tmpTags = copy.copy(self.module.tags)
            while len(tmpTags) > 1:
                tmp += "{0}, ".format(tmpTags.pop())
            tmp += "{0}".format(tmpTags.pop())
            #self.module.tags = '(' + tmp + ')'
            #TODO:
            descRect = self.descFontMetric.boundingRect("")
            # adjust labelRect in case descRect is wider
            labelRect = labelRect.united(descRect)
            descRect.adjust(0, 0, 0, MODULE_PORT_MARGIN[3])
        else:
            descRect = QRectF(0, 0, 0, 0)

        labelRect.translate(-labelRect.center().x(), -labelRect.center().y())
        self.paddedRect = QRectF(
            labelRect.adjusted(-MODULE_LABEL_MARGIN[0],
                                -MODULE_LABEL_MARGIN[1]
                                -descRect.height()/2,
                                MODULE_LABEL_MARGIN[2],
                                MODULE_LABEL_MARGIN[3]
                                +descRect.height()/2))
        
        self.labelRect = QRectF(
            self.paddedRect.left(),
            -(labelRect.height()+descRect.height())/2,
            self.paddedRect.width(),
            labelRect.height())
        self.descRect = QRectF(
            self.paddedRect.left(),
            self.labelRect.bottom(),
            self.paddedRect.width(),
            descRect.height())
        self.abstRect = QRectF(
            self.paddedRect.left(),
            -self.labelRect.top()-MODULE_PORT_MARGIN[3],
            labelRect.left()-self.paddedRect.left(),
            self.paddedRect.bottom()+self.labelRect.top())
            
    def paint(self, painter, option, widget=None):
        """ paint(painter: QPainter, option: QStyleOptionGraphicsItem,
                  widget: QWidget) -> None
        """
        # if item isSelected()
        if self.isSelected():
            self.modulePen = MODULE_SELECTED_PEN
            self.labelPen = MODULE_LABEL_SELECTED_PEN
        else:
            self.modulePen = MODULE_PEN
            self.labelPen = MODULE_LABEL_PEN
            
        # draw module shape
        painter.setBrush(self.moduleBrush)
        painter.setPen(self.modulePen)
        painter.fillRect(self.paddedRect, painter.brush())
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.paddedRect)
    
        # draw module labels
        painter.setPen(self.labelPen)
        painter.setFont(self.labelFont)
        painter.drawText(self.labelRect, Qt.AlignCenter, self.label)

    def adjustWidthToMin(self, minWidth):
        """ adjustWidthToContain(minWidth: int) -> None
        Resize the module width to at least be minWidth
        
        """
        if minWidth>self.paddedRect.width():
            diff = minWidth - self.paddedRect.width() + 1
            self.paddedRect.adjust(-diff/2, 0, diff/2, 0)

    def setupModule(self, module):
        # Update module info and visual
        self.id = module.id
        self.setZValue(0)
        self.module = module
        self.center = copy.copy(module.center)

        self.label = module.label
        self.description = module.description
        self.computeBoundingRect()

        # get I/O ports
        inputPorts = []
        self.inputPorts = {}
        self.optionalInputPorts = []

        outputPorts = []
        self.outputPorts = {}
        self.optionalOutputPorts = []

        d = PortType.Destination
        for p in module.getPorts(d):
            if not p.optional:
                inputPorts.append(p)
            else:
                self.optionalInputPorts.append(p)
        inputPorts += self.optionalInputPorts

        s = PortType.Source
        for p in module.getPorts(s):
            if not p.optional:
                outputPorts.append(p)
            else:
                self.optionalOutputPorts.append(p)
        outputPorts += self.optionalOutputPorts

        # Local dictionary lookups are faster than global ones..
        (mpm0, mpm1, mpm2, mpm3) = MODULE_PORT_MARGIN

        # Adjust the width to fit all ports
        maxPortCount = max(len(inputPorts), len(outputPorts))
        minWidth = (mpm0 +
                    PORT_WIDTH*maxPortCount +
                    MODULE_PORT_SPACE*(maxPortCount-1) +
                    mpm2 +
                    MODULE_PORT_PADDED_SPACE)
        self.adjustWidthToMin(minWidth)

        self.nextInputPortPos = [self.paddedRect.x() + mpm0,
                                 self.paddedRect.y() + mpm1]
        self.nextOutputPortPos = [self.paddedRect.right() - \
                                      PORT_WIDTH - mpm2,
                                  self.paddedRect.bottom() - \
                                      PORT_HEIGHT - mpm3]

        # Update input ports - slovnik 
        [x, y] = self.nextInputPortPos
        for port in inputPorts:
            self.inputPorts[port] = self.createPortItem(port, x, y)
            x += PORT_WIDTH + MODULE_PORT_SPACE
        self.nextInputPortPos = [x,y]

        # Update output ports
        [x, y] = self.nextOutputPortPos
        for port in outputPorts: 
            self.outputPorts[port] = self.createPortItem(port, x, y)
            x -= PORT_WIDTH + MODULE_PORT_SPACE
        self.nextOutputPortPos = [x, y]

    def createPortItem(self, port, x, y):
        """ createPortItem(port: Port, x: int, y: int) -> QGraphicsPortItem
        Create a item from the port spec
        
        """
        portShape = QGraphicsPortItem(x, y, self, port.optional)
        portShape.port = port
        # sest tooltip
        tooltip = port.getToolTip()
        portShape.setToolTip(tooltip)
        return portShape
    
    def getPortPosition(self, port, portDict):
        """ getPortPosition(port: Port,
                            portDict: {Port:QGraphicsPortItem})
                            -> QPointF
        Return the scene position of a port matched 'port' in portDict
        
        """
        for (p, item) in portDict.iteritems():
            if p.type == port.type and p.name == port.name:
                return item.sceneBoundingRect().center()
        return None

    def getInputPortPosition(self, port):
        """ getInputPortPosition(port: Port) -> QPointF
        Just an overload function of getPortPosition to get from input ports
        
        """
        pos = self.getPortPosition(port, self.inputPorts)
        return pos
        
    def getOutputPortPosition(self, port):
        """ getOutputPortPosition(port: Port} -> QRectF
        Just an overload function of getPortPosition to get from output ports
        
        """
        pos = self.getPortPosition(port, self.outputPorts)
        return pos
        
    def dependingConnectionItems(self):
        """
            Return connection depended on the item.
        """
#        sc = self.scene()
        result = self.connections
        return result

    def itemChange(self, change, value):
        """ itemChange(change: GraphicsItemChange, value: QVariant) -> QVariant
        Capture move event to also move the connections.  Also unselect any
        connections between unselected modules
        
        """
        # Move connections with modules
        if change == QGraphicsItem.ItemPositionChange:
            self._moved = True
            oldPos = self.pos()
            newPos = value.toPointF()
            dis = newPos - oldPos
            for connectionItem, s in self.dependingConnectionItems():
                # If both modules are selected, both of them will
                # trigger itemChange events.

                # If we just add 'dis' to both connection endpoints, we'll
                # end up moving each endpoint twice.

                # But we also don't want to call setupConnection twice on these
                # connections, so we ignore one of the endpoint dependencies and
                # perform the change on the other one

                (srcModule, dstModule) = connectionItem.connectingModules
                start_s = srcModule.isSelected()
                end_s = dstModule.isSelected()
                
                if start_s and end_s and s:
                    continue

                start = connectionItem.startPos
                end = connectionItem.endPos

                if start_s: start += dis
                if end_s: end += dis
                
                connectionItem.prepareGeometryChange()
                connectionItem.setupConnection(start, end)
        # Do not allow lone connections to be selected with modules.
        # Also autoselect connections between selected modules.  Thus the
        # selection is always the subgraph
        elif change==QGraphicsItem.ItemSelectedChange:
            # Unselect any connections between modules that are not selected
            for item in self.scene().selectedItems():
                if isinstance(item,QGraphicsConnectionItem):
                    (srcModule, dstModule) = item.connectingModules
                    if (not srcModule.isSelected() or 
                        not dstModule.isSelected()):
                        item.useSelectionRules = False
                        item.setSelected(False)
            # Handle connections from self
            for (item, start) in self.dependingConnectionItems():
                # Select any connections between self and other selected modules
                (srcModule, dstModule) = item.connectingModules
                if value.toBool():
                    if (srcModule==self and dstModule.isSelected() or
                        dstModule==self and srcModule.isSelected()):
                        # Because we are setting a state variable in the
                        # connection, do not make the change unless it is
                        # actually going to be performed
                        if not item.isSelected():
                            item.useSelectionRules = False
                            item.setSelected(True)
                # Unselect any connections between self and other modules
                else:
                    if item.isSelected():
                        item.useSelectionRules = False
                        item.setSelected(False)
            # Capture only selected modules + or - self for selection signal
            selectedItems = []
            selectedId = -1
            if value.toBool():
                selectedItems = [m for m in self.scene().selectedItems() 
                                 if isinstance(m,QGraphicsModuleItem)]
                selectedItems.append(self)
            else:
                selectedItems = [m for m in self.scene().selectedItems()
                                 if (isinstance(m,QGraphicsModuleItem) and 
                                     m != self)]
            if len(selectedItems)==1:
                selectedId = selectedItems[0].id
            self.scene().emit(SIGNAL('moduleSelected'),
                              selectedId, selectedItems)
        return QGraphicsItem.itemChange(self, change, value)

class QGraphicsConnectionItem(QGraphicsPathItem):
    def create_path(self, startPos, endPos):
            self.startPos = startPos
            self.endPos = endPos

            dx = abs(self.endPos.x() - self.startPos.x())
            dy = (self.startPos.y() - self.endPos.y())

            # This is reasonably ugly logic to get reasonably nice
            # curves. Here goes: we use a cubic bezier p0,p1,p2,p3, where:

            # p0 is the source port center
            # p3 is the destination port center
            # p1 is a control point displaced vertically from p0
            # p2 is a control point displaced vertically from p3

            # m is the monotonicity breakdown point: this is the minimum
            # displacement when dy/dx is low
            m = float(MODULE_LABEL_MARGIN[0]) * 3.0

            # positive_d and negative_d are the displacements when dy/dx is
            # large positive and large negative
            positive_d = max(m/3.0, dy / 2.0)
            negative_d = max(m/3.0, -dy / 4.0)

            if dx == 0.0:
                v = 0.0
            else:
                w = math.atan(dy/dx) * (2 / math.pi)
                if w < 0:
                    w = -w
                    v = w * negative_d + (1.0 - w) * m
                else:
                    v = w * positive_d + (1.0 - w) * m

            displacement = QPointF(0.0, v)
            self._control_1 = startPos + displacement
            self._control_2 = endPos - displacement

            path = QPainterPath(self.startPos)
            path.cubicTo(self._control_1, self._control_2, self.endPos)
            return path
     
    def  __init__(self, srcPoint, dstPoint, srcModule, dstModule, connection, parent=None):
        """
            srcPoint, dstPoint: QPointF
            srcModule, dstModule: QGraphicsModuleItem
            connection: Connection
            parent: QGraphicsItem
        """
        self.id = connection.id
        srcModule.addConnection(self, False)
        dstModule.addConnection(self, True)
        path = self.create_path(srcPoint, dstPoint)
        QGraphicsPolygonItem.__init__(self, path, parent)
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        # Bump it slightly higher than the highest module
        self.setZValue(max(srcModule.id,
                            dstModule.id) + 0.1)
        self.connectionPen = CONNECTION_PEN
        self.connectingModules = (srcModule, dstModule)
        self.connection = connection
        self.id = connection.id
        # Keep a flag for changing selection state during module selection
        self.useSelectionRules = True        
        
    def setupConnection(self, startPos, endPos):
        path = self.create_path(startPos, endPos)
        self.setPath(path)

    def paint(self, painter, option, widget=None):
        """ paint(painter: QPainter, option: QStyleOptionGraphicsItem,
                  widget: QWidget) -> None
        Peform actual painting of the connection.

        """
        # TODO: isSelected????? doesn't work as i thought
        if self.isSelected():
            painter.setPen(CONNECTION_SELECTED_PEN)
        else:
            painter.setPen(self.connectionPen)
        painter.drawPath(self.path())
    
    def itemChange(self, change, value):
        """ itemChange(change: GraphicsItemChange, value: QVariant) -> QVariant
        If modules are selected, only allow connections between 
        selected modules 

        """
        # Selection rules to be used only when a module isn't forcing 
        # the update
        if (change == QGraphicsItem.ItemSelectedChange and self.useSelectionRules):
            # Check for a selected module
            selectedItems = self.scene().selectedItems()
            selectedModules = False
            for item in selectedItems:
                if type(item)==QGraphicsModuleItem:
                    selectedModules = True
                    break
            if selectedModules:
                # Don't allow a connection between selected
                # modules to be deselected
                if (self.connectingModules[0].isSelected() and
                    self.connectingModules[1].isSelected()):
                    if not value.toBool():
                        return QVariant(True)
                # Don't allow a connection to be selected if
                # it is not between selected modules
                else:
                    if value.toBool():
                        return QVariant(False)
        self.useSelectionRules = True
        return QGraphicsPathItem.itemChange(self, change, value) 
    def delConnectionItem(self, con):
        """
            Depends if we want remove connection from one Module or from both.
        """
        mod = None
        if isinstance(con, tuple):
            if con[1]:
                mod = self.connectingModules[0]
                con[0].connection.source.setEmpty(True)
            else:
                mod = self.connectingModules[1]
                con[0].connection.destination.setEmpty(True)
            mod.delConnection(con)
        elif isinstance(con, QGraphicsConnectionItem):
            self.connectingModules[0].delConnection(con)
            self.connectingModules[1].delConnection(con)
            # source should has more destinations...
            con.connection.source.setEmpty(True)
            con.connection.destination.setEmpty(True)
## Processing Framework ##
class QModuleTreeView(QTreeView):
    """
        QTreeView for processing manager.
    """
    def __init__(self, parent=None):
        super(QModuleTreeView, self).__init__(parent)
        
    def mouseMoveEvent(self, event):
        '''
            We accept just Left Button of mouse. Then we check if we moved.
        '''
        if not (event.buttons() & Qt.LeftButton):
            return

        index = self.indexAt(event.pos())
        
        if not index.isValid():
            return

        # Keep position of index. After drop on scene we'll use it to obtain item from list of modules.
        point = event.pos()
        drag = QDrag(self)
        mime = QMimeData()        
        bstream = cPickle.dumps(point)
        mime.setData( "application/x-pf", bstream )
        drag.setMimeData(mime)

        drag.start(Qt.MoveAction)

