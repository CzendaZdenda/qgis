from PyQt4.QtCore import QPointF

from random import randint

class Module(object):
    def __init__(self):
        # TODO: validate id
        self.id = randint(2, 1000)
        self.label = ''
        self.center = QPointF(0, 0)
        self.description = ''
        self.ports = []
        self.tags = []
        
    def getPorts(self,  type = None):
        """
            type: PortType - Destination or Source
            Return list of Port according to the type if given, else return all ports.
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
        
class PortType(object):
    Destination,  Source = 1, 2

class Type(object):
    #TODO: think about this...
    Numeric, String, Bool, Path, Raster, Vector, Choice, Range = range(1,9)
class Port(object):
    def __init__(self, portType=None, type = None, moduleId = None,  name = None,  optional = False ):
        """
            portType: PortType - Destination, Source
            type: Type - Numeric, String, Bool, Path, Raster.....
            moduleId: int
            name: string/QString
            optional: bool - optional or mandatory
        """
        self.name = name
        self.optional = optional
        self.portType = portType
        self.type = type
        self.moduleId = moduleId
        self.description = ""
        self.empty = True
        
    def isEmpty(self):
        return self.empty
        
    def setEmpty(self, empty = True):
        self.empty = empty
        
class Connection(object):
    def __init__(self, sourcePort, destinationPort,  sourceModule, destinationModule):
        """
            Make connection between 2 modules.
            sourcePort, destinationPort: Port
            sourceModule. destinationModule: Module
        """
        # TODO: validate id
        self.id = randint(1, 20000)
        self.source = sourcePort
        self.destination = destinationPort
        self.sModule = sourceModule
        self.dModule = destinationModule
