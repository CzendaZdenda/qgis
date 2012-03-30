from random import randint

from PyQt4.QtCore import QPointF
from qgis.core import *

import processing

class Graph(object):
    """
        Graph of workflows. It keeps list of subgraphs (SubGraph).
        methods:
            addSGraph(SubGraph)         - to add SubGraph to Graph
            getSGraphs()                        - to get list of SubGraphs          TODO: Do we really use this method?
            isValid()                                - whether Graph is valid
            setValid(boolean)                  - set if Graph is valid
            executeGraph()                    - to execute Graph -> execute all SubGraphs -> execute all Modules in SubGraph
            TODO:
            save()                                  - to save Graph/Workflow - probably as XML file?
    """
    def __init__(self):
        self._sGraphs = []
        self._isValid = False
        
    def addSGraph(self, sub):
        """
            To add SubGraph to Graph
            sub: SubGraph
        """
        self._sGraphs.append(sub)
    
    def getSGraphs(self):
        """
            Return list of subgraphs of workflow's graph.
        """
        return self._sGraphs
        
    def isValid(self):
        """
            Return if graph is valid. It means, that all subgraphs are valid, that means that all modules of those subgraphs are valid, 
            values of ports are set or ports are conencted. 
        """
        return self._isValid

    def setValid(self, valid):
        """
            valid: bool
        """
        self._isValid = valid

    def save(self):
        pass
    def executeGraph(self):
        """
            To execute Graph -> execute all SubGraphs -> execute all Modules in SubGraphs.
        """
        for sub in self._sGraphs:
            sub.prepareToExecute()
            if sub.isValid():
                sub.executeSGraph()

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
    """
    def __init__(self):
        self._modules = []
        self._connections = []
        self._isValid = False
        
    def prepareToExecute(self):
        """
            We are looking if every Module is valid. It means that every input is set or connected with the output of another Module.
            TODO: 
                If some input is not set or not connected, the dialog should apear to ask user for setting inputs.
        """
        # for keeping inputs and outputs, that are not set
        inputs = []
        outputs = []
        for mod in self._modules:
            # go through all modules in subgraph
            if not mod.isValid():
                # if module is not valid go through all ports/parameters and look for not set ports and add them to relevant list
                for port in mod.getPorts():
                    if not port.optional:
                        if not port.isSet():
                            if port.portType == PortType.Destination:
                                if not port.isValid():
                                    inputs.append(port)
                            elif port.portType == PortType.Source:
                                outputs.append(port)

            # TODO: create dialog for setting in/outputs 
            # self.createIODialog(inputs, outputs)

        if not len(inputs):
            # for now, if there aren't not set inputs, we can say, that subgraph is valid
            self.setValid(True)
            
    def addModule(self, mod):
        """
            mod: Module
        """
        self._modules.append(mod)
        mod.setSGraph(self)
    
    def getModules(self):
        """
            Return list modules (Module) of subgraph.
        """
        return self._modules


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
        modules = self._modules[:]
        
        def setModule(mod):
            for p in mod.getPorts():
                if not p.isSet():
                    if p.portType == PortType.Destination:
                        sModule = p.findSourceModule(self._connections)
                        setModule(sModule)
            mod.execute()
        
        while modules:
            mod = modules.pop()
            if mod in self._modules:
                setModule(mod)
                    
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
        TODO:
            Do better execute() method.
    """
    def __init__(self):
        self.id = randint(2, 1000)
        self.label = ''
        self.center = QPointF(0, 0)
        self.description = ''
        self.ports = []
        self.tags = []
        # to keep instance of PF's module
        self._instance = None
        self._sGraph = None

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
        return self._instance
    def isValid(self):
        """
            Modul is valid if all mandatory inputs are given (as destination of some connection or as user set thru dock panel).
        """
        for port in self.ports:
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
            ports = self.ports
        else:
            for p in self.ports:
                if p.portType is type:
                    ports.append(p)
        return ports

    def addPort(self,  port):
        """
            Add port.
            port: Port
        """
        self.ports.append(port)
    def isSet(self):
        """
            Modul is set if all mandatory inputs are set.
        """
        for port in self.ports:
            if port.portType == PortType.Destination:
                if not port.optional:
                    if not port.isSet():
                        return False
        return True
    def execute(self):
        """
            Set Modules's Ports' Values to Parameters of instance of PFModule.
            TODO: 
                There are some warnings when creating qgis layers.
                Support setting values of all parameters, not just layers (raster, vector) and not just saga.
                Metadata.
        """
        if self.isSet():
            self.getInstancePF()
            for p in self.getPorts():
                # maybe just inputs
                for par in self._instance.parameters().keys():
                    if par.name() == p.name and par.role() == p.portType and par.__class__ == p.type:
                        self._instance.setValue(par, p.getValue())
            self._instance.setState(2)
            # get module from list of modules in SubGraph
            if self in self._sGraph._modules:
                self._sGraph._modules.pop( self._sGraph._modules.index(self) )
            for p in self.getPorts(PortType.Source):
                # for now it set just set value to layer parameters/ports
                if p.type == processing.parameters.RasterLayerParameter:
                    lyr = str(p.parameterInstance.sagaLayer.Get_File_Name().split('.')[0]) + ".sdat"
                    # b = QgsRasterLayer(lyr,  str(p.parameterInstance.sagaLayer.Get_Name() ) )
                    b = QgsRasterLayer(lyr)
                    p.setOutputData(b)
                    p.setValue(b)
                elif p.type == processing.parameters.VectorLayerParameter:
                    # b = QgsVectorLayer( str( p.parameterInstance.sagaLayer.Get_File_Name() ),  str( p.parameterInstance.sagaLayer.Get_Name() ), "ogr" )
                    b = QgsVectorLayer( str( p.parameterInstance.sagaLayer.Get_File_Name() ) )
                    p.setOutputData(b)
                    p.setValue(b)
                
                # set value to connected Port
                if p.type in [processing.parameters.RasterLayerParameter, processing.parameters.VectorLayerParameter]:
                    for pp in p.destinationPorts(self._sGraph.getConnections()):
                        pp.setValue(p.outputData())
        else:  
            pass
        
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

    def destinationPorts(self, conns):
        """
            It return list of Ports that are connected with that Port.
        """
        tmp = []
        for con in conns:
            if con.source == self:
                tmp.append(con.destination)
                con.destination.setValue(self._outputData)
        return tmp

    def findSourceModule(self, conns):
        """
            If Connection exist return source Module.
        """
        for con in conns:
            if con.destination == self:
                return con.sModule
        return False

class Connection(object):
    """
        Connection between source and destination Ports. We also keep references to source and destination Modules.
    """
    
    def __init__(self, sourcePort, destinationPort,  sourceModule, destinationModule):
        """
            Make connection between 2 Modules through source and destination Port.
            sourcePort, destinationPort: Port
            sourceModule. destinationModule: Module
        """
        # TODO: validate id
        self.id = randint(1, 20000)
        self.source = sourcePort
        self.destination = destinationPort
        self.sModule = sourceModule
        self.dModule = destinationModule
