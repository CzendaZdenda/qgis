from random import randint
from xml.dom.minidom import Document
        
from PyQt4.QtCore import QPointF,  QFileInfo,  QDir
from qgis.core import *

import processing

class Graph(object):
    """
        Graph of workflows. It keeps list of subgraphs (SubGraph).
        methods:
            addSubGraph(SubGraph)     - to add SubGraph to Graph
            getSubGraphByID(int)          - to get SubGraph according the int
            getModulesBySubGraphID(int) - return dic of Modules corresponding with given SubGraph.id
            addModule(Module)              - to add Module to Graph
            getModuleByID(int)              - 
            addConnection(Connection) - to add Connection to Graph
            getConnectionByID(int)        - 
            isValid()                                - whether Graph is valid
            setValid(boolean)                  - set if Graph is valid
            executeGraph()                    - to execute Graph -> execute all SubGraphs -> execute all Modules in SubGraph
            save()                                  - to save graph as XML (for now the directory is something like ~/,qgis/python/workflows")
            xml()                                   - to get xml.dom.minidom.Element representation of this Graph.
    """
    def __init__(self):
        self.name = "Graph"
        self.description = ""
        self.tags = []
        self._isValid = False
        self.modules = {}
        self.connections = {}
        self.subgraphs = {}
      
    def addModule(self, mod):
        """
            Add Module 'mod' to Graph.
        """
        while mod.id in self.modules:
            mod.id = randint(2, 1000)
        self.modules[mod.id] = mod
        # add reference to Graph to Module instance
        mod.graph = self
    def getModuleByID(self, id):
        """
            Return Module according the id.
        """
        return self.modules[id]
    def addConnection(self, con):  
        """
            Add Connection 'con' to Graph.
        """
        while con.id in self.connections:
            con.id = randint(1, 2000)
        self.connections[con.id] = con
        # add reference to Graph to Connection instance
        con.graph = self        
    def getConnectionByID(self, id):
        """
            Return Connection according the id.
        """
        return self.connections[id]
    def addSubGraph(self, sub):  
        """
            Add SubGraph 'sub' to Graph.
        """
        while sub.id in self.subgraphs:
            sub.id = randint(1, 200)
        self.subgraphs[sub.id] = sub
        # add reference to Graph to Connection instance
        sub.graph = self        

    def getSubGraphByID(self, id):
        """
            Return SubGraph according to id.
        """
        return self.subgraphs[id]        
        
    def isValid(self):
        """
            Return if graph is valid. It should means, that all subgraphs are valid, that means that all modules of those subgraphs are valid, 
            values of ports are set or ports are conencted. 
        """
        return self._isValid

    def setValid(self, valid):
        """
            valid: bool
        """
        self._isValid = valid

    def save(self):
        """
            Save graph as XML (for now the directory is something like ~/,qgis/python/workflows").
        """
        # create new directory if needed
        pathXML = QFileInfo( QgsApplication.qgisUserDbFilePath() ).path() + "/python/workflows"
        QDir().mkdir(pathXML)
        # create new xml document and save it
        doc = Document()
        doc.appendChild(self.xml())
        filename = self.name
        f = open( "{0}/{1}.xml".format(pathXML, filename) , "w")
        doc.writexml(f,  indent="\n",  addindent="\t", encoding="UTF-8")
        f.close()
            
    def xml(self):
        """
            It returns xml.dom.minidom.Element representation of this Graph.
        """
        graphXML = Document().createElement("Graph")
        graphXML.setAttribute("name", "{0}".format(self.name))
        graphXML.setAttribute("tags", "{0}".format(self.tags))
        graphXML.appendChild( Document().createTextNode("{0}".format(self.description)) )
        for sub in self.subgraphs.values():
            graphXML.appendChild(sub.xml())

        return graphXML
        
    def executeGraph(self):
        """
            To execute Graph -> execute all SubGraphs -> execute all Modules in SubGraphs.
            TODO: after executing - clean outputs and connected inputs
        """
        for sub in self.subgraphs.values():
            sub.prepareToExecute()
            if sub.isValid():
                sub.executeSGraph()
            else:
                self._invalidSubGraph = sub
                return False
                
        # alfter execution set all connected or output layers as default
        for mod in self.modules.values():
            for port in mod.getPorts():
                if port.isConnected() or port.portType == PortType.Source:
                    port.setValue(port.defaultValue)
                    mod.getInstancePF().setValue(port.parameterInstance, port.defaultValue)
                    port.setAddItToCanvas(False)
        return True
        
    def getModulesBySubGraphId(self, id):
        """
            Return dic of Modules corresponding with given SubGraph.id.
        """
        tmp = {}
        for mod in self.modules.values():
            if mod._sGraph.id == id:
                tmp[mod.id] = mod
        return tmp

class SubGraph(object):
    """
        SubGraph keeps list of modules (Module) and connections (Connection).
        methods:
            prepareToExecute()
            addModule(Module)
            getModules()
            setConnections(list<Connection>)
            getConnections()
            isValid()
            setValid(boolean)
            executeSGraph()
            getModuleByID(int)
    """
    def __init__(self):
        self.id = randint(1, 200)
        self.modules = {}
        self.connections = {}
        self._connections = []
        self._isValid = False
        
    def prepareToExecute(self):
        """
            We are looking if every Module is valid. It means that every input is set or connected with the output of another Module.
        """
        # for keeping inputs and outputs, that are not set
        outputs = []
        inputs = {}
        for mod in self.modules.values():
            # go through all modules in subgraph
            if not mod.isValid():
                # if module is not valid go through all ports/parameters and look for not set ports and add them to relevant list
                for port in mod.getPorts():
                    if not port.optional:
                        if not port.isSet():
                            if port.portType == PortType.Destination:
                                if not port.isValid():
                                    inputs[port] = mod
                            elif port.portType == PortType.Source:
                                outputs.append(port)

        if not len(inputs.keys()):
            # for now, if there aren't not set inputs, we can say, that subgraph is valid
            self.setValid(True)
        else:
            self._invalidInputs = inputs
            
    def addModule(self, mod):
        """
            mod: Module
        """
        self.modules[mod.id] = mod
        mod.setSGraph(self)
    
    def getModules(self):
        """
            Return list modules (Module) of subgraph.
        """
        return self.modules.values()

    def setConnections(self, cons):
        """
            cons: list of Connections
        """
        self._connections = cons
    
    def getConnections(self):
        """
            Return list connections (Connection) between modules that exist in the subgraph.
        """
        return self._connections

    def isValid(self):
        """
            Return if subgraph is valid. It means, that all modules of those subgraph are valid, same with ports of those modules.
        """
        return self._isValid

    def setValid(self, valid):
        """
            valid: bool
        """
        self._isValid = valid
    def executeSGraph(self):
        """
            Going through all modules and executing them. If some port/parameter of module is not set,
            looking for module with what is it connected and execute it.
        """
        # modules of subgraph

        if not self.modules.values():
            self.modules = self.graph.getModulesBySubGraphId(self.id) 
        modules = self.modules.values()[:]
        
        def setModule(mod):
            for p in mod.getPorts():
                if not p.isSet() and not p.optional:
                    if p.portType == PortType.Destination:
                        sModule = p.findSourceModule(self._connections)
                        setModule(sModule)
            mod.execute()
            
        while modules:
            mod = modules.pop()
            if mod.id in self.modules:
                setModule(mod)
        
    def xml(self):
        """
            It returns xml.dom.minidom.Element representation of this SubGraph.
        """        
        subXML = Document().createElement("SubGraph")
        subXML.setAttribute("id", "{0}".format(self.id))
        for mod in self.modules.values():
            subXML.appendChild(mod.xml())                    
        for con in self._connections:
            subXML.appendChild(con.xml())
        return subXML
        
    def getModuleByID(self, id):
        """
            Return Module corresponding to given id.
        """
        return self.modules[id]
        
class Module(object):
    """
        methods:
            setSGraph(SubGraph)
            getInstancePF()
            isValid()
            addPort(Port)
            getPorts(PortType=None)
            isSet()
            execute()
            xml()
            getPortBytID(int)
        TODO:
            better execute() method.
    """
    def __init__(self):
        self.id = randint(2, 1000)
        self.label = ''
        self.center = QPointF(0, 0)
        self.description = ''
        self.tags = []
        # to keep instance of PF's module
        self._instance = None
        self._sGraph = None
        self._ports = {}

    def setSGraph(self, sgraph):
        """
            To keep reference of SubGraph to which module is belong.
        """
        self._sGraph = sgraph
    def getInstancePF(self):
        """
            Return instance of PF Module according to label of Module, if exist, otherwise create and return it.
        """
        if self._instance is None:
            self._instance = processing.framework[self.label].instance()
        if self._ports.values()[0].parameterInstance is None:
            for par in self._instance.module().parameters():
                for port in self._ports.values():
                    if par.name() == port.name:
                        port.parameterInstance = par
#                        break
        return self._instance
    def isValid(self):
        """
            Modul is valid if all mandatory inputs are given (as destination of some connection or as user set thru dock panel).
        """
        for port in self._ports.values():
            if port.portType == PortType.Destination:
                if not port.optional:
                    if not port.isValid():
                        return False
        return True
            
    def getPorts(self,  type = None):
        """
            Return list of Port according to the type if given, else return all ports.
            type: PortType - Destination or Source            
        """
        ports = []
        if type is None:
            ports = self._ports.values()
        else:
            for p in self._ports.values():
                if p.portType is type:
                    ports.append(p)
        return ports

    def addPort(self,  port):
        """
            Add port.
            port: Port
        """
        while port.id in self._ports:
            port.id = self.id = randint(1, 2000)
        self._ports[port.id] = port
        port.graph = self.graph
    def isSet(self):
        """
            Modul is set if all mandatory inputs are set.
        """
        for port in self._ports.values():
            if port.portType == PortType.Destination:
                if not port.optional:
                    if not port.isSet():
                        return False
        return True
    def execute(self):
        """
            Set Modules's Ports' Values to Parameters of instance of PFModule.
        """
        print self.label
        if self.isSet():
            self.getInstancePF()
            for p in self.getPorts():
                # maybe just inputs
                for par in self._instance.parameters().keys():
                    if par.name() == p.name and par.role() == p.portType and par.__class__ == p.type:
                        self._instance.setValue(par, p.getValue())
            self._instance.setState(2)
            # get module from list of modules in SubGraph
            if self.id in self._sGraph.modules:
                del self._sGraph.modules[self.id]
            for p in self.getPorts(PortType.Source):
                # for now it just set value to layer parameters/ports
                # we keep information if this is module from SAGA Plugin, because there is the bug, that module don't  keep output data properly
                saga = "saga" in list( self._instance.module().tags () )
                if p.type == processing.parameters.RasterLayerParameter:
                    # to care about raster data
                    if saga:
                        # if module is from SAGA Plugin, we have to get output data from this parameter from sagalayer attribute
                        lyr = str(p.parameterInstance.sagaLayer.Get_File_Name().split('.')[0]) + ".sdat"
                        b = QgsRasterLayer(lyr)
                    else:
                        b = self._instance[p.parameterInstance]
                    # keep output data in this port and also it as current value
                    p.setOutputData(b)
                    p.setValue(b)
                    # if it is possible and user wants this, add new layer to QGIS
                    try:
                        if p.addItToCanvas():
                            mreg = QgsMapLayerRegistry().instance()
                            b.setLayerName(p.outputName())
                            mreg.addMapLayer(b)
                    except:
                        print "problem with add raster layer into canvas"
                elif p.type == processing.parameters.VectorLayerParameter:
                    if saga:
                        try:
                            b = QgsVectorLayer( str( p.parameterInstance.sagaLayer.Get_File_Name() ),  str( p.parameterInstance.sagaLayer.Get_Name() ), "ogr" )
                        except:
                            b = self._instance[p.parameterInstance]
                    else:
                        b = self._instance[p.parameterInstance]
                    p.setOutputData(b)
                    p.setValue(b)
                    try:
                        if p.addItToCanvas():
                            mreg = QgsMapLayerRegistry().instance()
                            b.setLayerName(p.outputName())
                            mreg.addMapLayer(b)
                    except:
                        print "problem with add vector layer into canvas"
                else:
                    try:
                        p.setOutputData(self._instance[p.parameterInstance])
                        p.setValue(self._instance[p.parameterInstance])
                    except :
                        pass
                # set value to connected Port
                if p.type in [processing.parameters.RasterLayerParameter, processing.parameters.VectorLayerParameter]:
                    for pp in p.destinationPorts(self._sGraph.getConnections()):
                        pp.setValue(p.outputData())
        else:  
            pass
    def xml(self):
        """
            It returns xml.dom.minidom.Element representation of this Module.
        """
        modXML = Document().createElement("Module")
        modXML.setAttribute("name", "{0}".format(self.label))
        modXML.setAttribute("id", "{0}".format(self.id))
        modXML.appendChild( Document().createTextNode("{0}".format(self.description)) )
        for tag in self.tags:
            t = Document().createElement("tag")
            t.appendChild( Document().createTextNode( "{0}".format(tag) ) )
            modXML.appendChild(t)            
        for port in self._ports.values():
            modXML.appendChild(port.xml())        
        return modXML
    def getPortByID(self, id):
        return self._ports[id]
        
class PortType(object):
    Destination,  Source = 1, 2

class Port(object):
    """
        methods:
            setOutputData(data)
            outputData()
            setData(data)
            getData()
            setValue(data)
            getValue()
            isEmpty()
            setEmpty(boolean)
            isSet()
            isValid()
            destinationPorts(list<Connection>)
            findSourceModule(list<Connection>)
            xml()                                                   - return xml.dom.minidom.Element representation of this Port
            setSetIt(boolean)                                 - 
            setAlternativeName(string)                  - 
    """
    def __init__(self, dValue = None,  portType=None, type = None, moduleId = None,  name = None,  optional = False ):
        """
            portType: PortType - Destination, Source
            type: Type - Numeric, String, Bool, Path, Raster.....
            moduleId: int
            name: string/QString
            optional: bool - optional or mandatory
        """
        self.name = name
        self.id = randint(1, 2000)
        self._data = None # for keeping choices, if there are
        self.optional = optional
        self.portType = portType
        self.type = type
        self.moduleId = moduleId
        self.description = ""
        self.empty = True
        self._value = dValue
        self.defaultValue = dValue
        self.parameterInstance = None
        self._outputData = None
        # whether user want to set its value if he/she will execute workflow as module from PF manager
        self.setIt = False
    
    def setOutputData(self, output):
        self._outputData = output
        
    def outputData(self):
        return self._outputData

    def setData(self, tmp):
        """
            Set data that are propposed by PF module - usually list of choices.
        """
        self._data = tmp
        
    def getData(self):
        return self._data
    
    def setValue(self, val):
        if type(val) == str:
            if self.type is processing.parameters.NumericParameter:
                self._value = float(val)
            elif self.type is processing.parameters.RangeParameter:
                range = val[1:-1].split(', ')
                self._value = [float(range[0]), float(range[1])] 
            elif self.type is processing.parameters.BooleanParameter:
                if val == "True":
                    self._value = True
                else:
                    self._value = False
            elif self.type is processing.parameters.ChoiceParameter:
                self._value = int(val)
            elif self.type in [ processing.parameters.VectorLayerParameter,  processing.parameters.RasterLayerParameter]:
                self._value = []
            else:
                #  self.type == processing.parameters.PathParameter a Parameter
                self._value = val
        else:
            self._value = val
        
    def getValue(self):
        return self._value
        
    def isEmpty(self):
        """
            If Port is empty it meens, that there is no connection between this Port and some other one.
        """
        return self.empty
        
    def setEmpty(self, empty = True):
        self.empty = empty
        
    def isSet(self):
        """
            If Value is set.
        """
        if self.type in [processing.parameters.BooleanParameter, processing.parameters.NumericParameter,  processing.parameters.ChoiceParameter] :
            return True
        if self._value:
            return True
        return False

        
    def isValid(self):
        """
            Input Port is valid if value is set or connection exist. Output Port is valid in general.
        """
        if self.portType == PortType.Source:
            return True
        if self.type in [processing.parameters.BooleanParameter, processing.parameters.NumericParameter,  processing.parameters.ChoiceParameter] :
            return True
        if not self.empty or self._value:
            return True
        return False

    def isConnected(self):
        """
            Return True if exists some connections between this Port and other one.
        """
        conns = self.graph.connections.values()
        for con in conns:
            if ( con.sModule.id == self.moduleId and con.source.id == self.id) or ( con.dModule.id == self.moduleId and con.destination.id == self.id): 
                return True
        return False

    def destinationPorts(self, conns = None):
        """
            It return list of Ports that are connected with that Port.
        """
        tmp = []
        if conns is None:
            conns = self.graph.connections.values()
        for con in conns:
            if con.sModule.id == self.moduleId and con.source.id == self.id: 
                tmp.append(con.destination)
        return tmp

    def findSourceModule(self, conns = None):
        """
            If Connection exist return source Module.
        """
        if conns is None:
            conns = self.graph.connections.values()
        for con in conns:
            if con.dModule.id == self.moduleId and con.destination.id == self.id: 
                return con.sModule
        return False
    def xml(self):
        """
            It returns xml.dom.minidom.Element representation of this Module.
        """
        portXML = Document().createElement("Port")
        portXML.setAttribute("name", self.name)
        portXML.setAttribute( "id", "{0}".format(self.id) )
        portXML.setAttribute("type", "{0}".format(self.type))
        portXML.setAttribute("should_be_set", "{0}".format(self.setIt))
        portXML.setAttribute("porttype", "{0}".format(self.portType))
        portXML.setAttribute("optional", "{0}".format(self.optional))
        portXML.setAttribute("default_value", "{0}".format(self.defaultValue))
        # according to type of parameter expression of value should changing?
        portXML.setAttribute("value", "{0}".format(self._value))
        portXML.setAttribute("moduleID", "{0}".format(self.moduleId))
        portXML.setAttribute("connected", "{0}".format(self.isConnected()))
        if self.type is processing.parameters.ChoiceParameter:
            portXML.setAttribute("choices", "{0}".format(self._data) )
        try:
            portXML.setAttribute("alternative_name", "{0}".format(self.alternativeName) )
        except:
            pass
        portXML.appendChild( Document().createTextNode("{0}".format(self.description)) )
        return portXML
    def setSetIt(self, value):
        self.setIt = value
    def setAlternativeName(self, name):
        self.alternativeName = name
    def setAddItToCanvas(self, bool = False):
        self.addIt = bool
    def addItToCanvas(self):
        try:
            return self.addIt
        except:
            return False
    def setOutputName(self, name):
        self._outputName = name
    def outputName(self):
        try:
            return self._outputName
        except:
            return self.name
    def getToolTip(self):
        """
            Generate tool tip for QGraphicsPortItem.
        """
        try:
            return self.tooltip
        except:
            self.tooltip = '<b>{0}</b> {1}'.format(self.name, str(self.type).split('.')[-1])
            return self.tooltip

class Connection(object):
    """
        Connection between source and destination Ports. We also keep references to source and destination Modules.
        methods:
            xml()
    """
    def __init__(self, sourcePort, destinationPort,  sourceModule, destinationModule):
        """
            Make connection between 2 Modules through source and destination Port.
            sourcePort, destinationPort: Port
            sourceModule. destinationModule: Module
        """
        self.id = randint(1, 2000)
        self.source = sourcePort
        self.destination = destinationPort
        self.sModule = sourceModule
        self.dModule = destinationModule
        
    def xml(self):
        """
            It returns xml.dom.minidom.Element representation of this Connection.
        """
        conXML = Document().createElement("Connection")
        conXML.setAttribute("id", "{0}".format(self.id))
        conXML.setAttribute("source_port_id", "{0}".format(self.source.id))
        conXML.setAttribute("destination_port_id", "{0}".format(self.destination.id))
        conXML.setAttribute("source_module_id", "{0}".format(self.sModule.id))
        conXML.setAttribute("destination_module_id", "{0}".format(self.dModule.id))
        return conXML

