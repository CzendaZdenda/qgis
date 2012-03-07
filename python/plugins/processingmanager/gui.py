# inspired by VisTrails

import copy
import math
import cPickle
import pickle

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.Qt import *

from core import PortType,  Connection,  Module,  Port
import processingplugin
import processing

# some graphics parameters...
PORT_WIDTH = 10
PORT_HEIGHT = 10
MODULE_SELECTED_PEN = QPen( QBrush( QColor(Qt.darkYellow) ), 3 )
MODULE_LABEL_SELECTED_PEN = QPen( QBrush( QColor(Qt.black)),  2 )
BREAKPOINT_MODULE_BRUSH = QPen( QBrush( QColor(Qt.black)),  2 )
MODULE_LABEL_MARGIN = (20, 20, 20, 15)
MODULE_PORT_MARGIN = (4, 4, 4, 4)
MODULE_PORT_SPACE = 4
MODULE_PORT_PADDED_SPACE = 20
CONNECTION_PEN = QPen( QBrush( QColor(Qt.black), 2 ) )
CONNECTION_SELECTED_PEN = QPen( QBrush( QColor(Qt.yellow ), 3 ) )

class Mode(object):
   MoveItem,  InsertLine = range(2)

        
class GraphicsView(QGraphicsView):
    '''
        QGraphicsView.
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
            # Get modul from QModuleTreeView.
            d = event.mimeData()
            b = d.retrieveData("application/x-pf", QVariant.ByteArray)
            pfM = pickle.loads(b.toByteArray())
        
            index2 = event.source().indexAt(pfM)
            module = event.source().model().data(index2,Qt.UserRole+1).toPyObject()        
            self.insertModule(module, event.pos())
        
    def insertModule(self, mod, pos):
        '''
            Insert module into the scene.
            mod: processing.framework.Module
            pos:   QPoint
        '''
        ports = mod.parameters()
        # create workflow builder module
        module = Module()
        module.label = mod.name()
        module.description = mod.description()
        module.tags = mod.tags()
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
                tmpPort = Port(PType,  i.type(),  module.id, i.name())
            else:
                tmpPort = Port(PType,  i.type(),  module.id, i.name(),  True)
            tmpPort.description = i.description()
            module.addPort(tmpPort)
            
        # add Module into DiagramScene
        self.scene().addModule(module, pos)
        
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
        #self._old_module_ids = set()
        #self._old_connection_ids = set()
        self.justClick = False
        
    # VisTrails
    def addModule(self, module, position = QPointF(100, 100), moduleBrush=None):
        """ 
        module: Module
        position: QPointF
        moduleBrush: QBrush
        -> QGraphicsModuleItem
        Add a module to the scene 
        """
        moduleItem = QGraphicsModuleItem(None)
        moduleItem.setupModule(module)
        moduleItem.setPos(QPointF(position))
        if moduleBrush:
            moduleItem.moduleBrush = moduleBrush
        self.addItem(moduleItem)
        self.modules[module.id] = moduleItem
        #self._old_module_ids.add(module.id)
        return moduleItem

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
        connectionItem = QGraphicsConnectionItem(srcPoint, dstPoint,
                                                 srcModule, dstModule,
                                                 connection)
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
        # clear information previous about module's ports and module/port's description
        self.parent().modelInput.clear()
        self.parent().modelOutput.clear()
        self.parent().textEditDesc.clear()
        
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
                            # test if startPoint is really source point of connection, otherwise swith them
                            if startPort.portType != PortType.Source:
                                tmp = endPort
                                endPort = startPort
                                startPort = tmp
                                tmp = endModule
                                endModule = startModule
                                startModule = tmp
                            # connect ports/modules by Connection
                            con = Connection(startPort, endPort, startModule,  endModule)
                            self.addConnection(con)
                            
                            startPort.setEmpty(False)
                            endPort.setEmpty(False)
                            
                if self.line:
                    self.removeItem(self.line)
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
                        port = tmpPort.port
                        self.parent().item.setText(QString("Port - {0}".format(port.name)))
                        self.parent().textEditDesc.setText(QString("{1} --> {0}".format(port.description, port.type)))

                    elif (tmpModule):
                        module = tmpModule.module
                        #TODO: look at models from MVC
                        self.parent().item.setText(QString("Module - {0}".format(module.label)))
                        self.parent().textEditDesc.setText(module.description)
                        for port in module.ports:
                            item = QStandardItem(QString("{0}({1})".format(port.name,  port.type)))
                            item.setData(port)
                            item.setEditable(False)
                            item.setSelectable(True)
                            if port.portType is PortType.Destination:                                
                                self.parent().modelInput.appendRow(item)
                            elif port.portType is PortType.Source:
                                self.parent().modelOutput.appendRow(item)
                        self.parent().treeViewIn.resizeColumnToContents(0)
                        self.parent().treeViewOut.resizeColumnToContents(0)

            self.justClick = False

  
    
class QGraphicsPortItem(QGraphicsRectItem):
    '''
        Port - input/output of the module.
    '''
    def __init__(self, x, y, parent = None,  optional = False):
        _rect = QRectF(0, 0, PORT_WIDTH, PORT_HEIGHT)
        QGraphicsRectItem.__init__(self,  _rect.translated(x, y), parent)
        # super(QGraphicsPortItem,  self).__init__(_rect.translated(x, y), parent)
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
        # TODO: rect
        self.paddedRect = QRectF(0, 0, 100, 60)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(0)
        self.labelFont = QFont("Arial", 14, QFont.Bold)
        self.labelFontMetric = QFontMetrics(self.labelFont)
        self.descFont = QFont("Arial", 12)
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
        #
        self.connections = []
        
    def addConnection(self, con, tf):
        self.connections.append((con, tf))

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
            self.module.tags = '(' + tmp + ')'
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
        sc = self.scene()
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
        Peform actual painting of the connection

        """
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
