# -*- coding: utf-8 -*-

#	 Plugin for reading workflows for Quantum GIS Processing Framework stored as XML files
#
#	 workflow_builder.py (C) Zdenek Ruzicka
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
#   MA 02110-1301, USA.import os

from random import randint
from xml.dom import minidom

from qgis.core import *

import processing
from processing.parameters import *
from processingplugin import core

from PyQt4.QtCore import *

from osgeo import gdal, ogr
from gdalconst import *

class Plugin:
    def __init__(self, iface):
        # save reference to the QGIS interface
        self.iface = iface
    def unload(self):
        pass
    def modules(self):
        return self.mods
    def getModules(self):
        mods = []
        pathXML = QFileInfo( QgsApplication.qgisUserDbFilePath() ).path() + "/python/workflows"
        dir = QDir(pathXML)
        dir.setNameFilters(QStringList( ["*.xml"] ) )
        for f in dir.entryInfoList():
            # take file, make Module
            try:
                mods.append( Module(f.absoluteFilePath()) )
            except:
                print "I can't read this file: {0}".format(f.absoluteFilePath())
                
        return mods
    def initGui(self):
        self.mods = self.getModules()
        processing.framework.registerModuleProvider(self)

class Module(processing.Module):
    def __init__(self, path):
        """
            Rebuild Graph from .xml file.
        """
        fileXML = minidom.parse( str(path) )
        graphDOM = fileXML.getElementsByTagName("Graph")[0] # should be just one
        self.graph = core.Graph()
        self.graph.name = str( graphDOM.getAttribute("name") )
        self.graph.description = str( graphDOM.childNodes[0].nodeValue )
        tags = ["workflow"]
        # looking if there are defined some tags
        if graphDOM.hasAttribute("tags"):
            for tag in str( graphDOM.getAttribute("tags") )[1:-1].split(', '):
                tag = tag[1:-1].strip()
                if tag:
                    tags.append(tag)

        processing.Module.__init__(self, self.graph.name, description = self.graph.description, tags = tags)
        self._blockSignals = False
        self._parameters = []
        self._instance = ModuleInstance(self)

        # rebuild SubGraphs
        for subDOM in graphDOM.getElementsByTagName("SubGraph"):
            sub = core.SubGraph()
            # add SubGraph to the Graph
            sub.id = int( subDOM.getAttribute("id") )
            self.graph.addSubGraph(sub)
            # rebuild Models
            for modDOM in subDOM.getElementsByTagName("Module"):
                mod = core.Module()
                # add Module to the Graph                
                mod.label = modDOM.getAttribute("name")
                mod.id = int( modDOM.getAttribute("id") )
                self.graph.addModule(mod)
                mod.description = modDOM.childNodes[0].nodeValue
                for portDOM in modDOM.getElementsByTagName("Port"):
                    port = core.Port( dValue = portDOM.getAttribute("default_value"),  portType=int( portDOM.getAttribute("porttype") ), type = portDOM.getAttribute("type"), 
                                     moduleId = int( portDOM.getAttribute("moduleID") ),  name = portDOM.getAttribute("name"),  optional = self.returnBoolean( portDOM.getAttribute("optional") ) )

                    port.shouldBeSet = self.returnBoolean( portDOM.getAttribute("should_be_set") )
                    port.connected = self.returnBoolean( portDOM.getAttribute("connected") )
                    port.setEmpty(port.connected == False)
                    port.id = int( portDOM.getAttribute("id") )
                    if portDOM.hasAttribute("alternative_name"):
                        port.alternativeName = str( portDOM.getAttribute("alternative_name") )
                    type = portDOM.getAttribute("type")
                    if  "VectorLayerParameter" in type:
                        port.type = VectorLayerParameter
                    elif "RasterLayerParameter" in type:
                        port.type = RasterLayerParameter
                    elif "NumericParameter" in type:
                        port.type = NumericParameter
                    elif "RangeParameter" in type:
                        port.type = RangeParameter
                    elif "BooleanParameter" in type:
                        port.type = BooleanParameter
                    elif "ChoiceParameter" in type:
                        port.type = ChoiceParameter
                        tmp = []
                        for ch in str( portDOM.getAttribute("choices") )[1:-1].split(', ') :
                            tmp.append(ch[1:-1])
                        port.setData( tmp)
                    elif "StringParameter" in type:
                        port.type = StringParameter
                    elif "PathParameter" in type:
                        port.type = PathParameter
                    else:
                        port.type = Parameter
                        
                    port.setValue( str( portDOM.getAttribute("value") ) )
                    port.defaultValue = port.getValue()
                    # if port is input layer or should be set, create Parameter of PFModule
                    if ( port.type in [VectorLayerParameter, RasterLayerParameter] or port.shouldBeSet ):
                        if port.connected:
                            pass
                        else:
                            self.addParameter(port)
                    mod.addPort(port)
                sub.addModule(mod)
            
            # rebuild Connestions
            conns = []
            for conDOM in subDOM.getElementsByTagName("Connection"):
                sourceModule = sub.getModuleByID( int( conDOM.getAttribute( "source_module_id")  )  )
                destinationModule = sub.getModuleByID( int( conDOM.getAttribute( "destination_module_id") ) )
                sourcePort = sourceModule.getPortByID( int( conDOM.getAttribute( "source_port_id") ) )
                destinationPort = destinationModule.getPortByID( int( conDOM.getAttribute( "destination_port_id") ) )
                con = core.Connection(sourcePort, destinationPort,  sourceModule, destinationModule)
                con.id = conDOM.getAttribute("id")
                conns.append(con)
                self.graph.addConnection(con)
            sub.setConnections(conns)
                
    def addParameter(self, par):
        try:
            qgisParam = par.type( "{0}".format(par.alternativeName) )
        except:
            qgisParam = par.type( "{0}".format(par.name) )
        qgisParam.portId = par.id
        qgisParam.moduleId = par.moduleId
        if par.portType == core.PortType.Destination:
            qgisParam.setRole(Parameter.Role.input)
        elif par.portType == core.PortType.Source:
            qgisParam.setRole(Parameter.Role.output)
        qgisParam.setDefaultValue( par.getValue() )
        if par.type is ChoiceParameter:
            qgisParam._choices = par.getData()
        if par.optional:
            qgisParam.setMandatory(False)
        # to keep Module and Port ID
        qgisParam.ids = [par.moduleId, par.id]
        self._parameters.append(qgisParam)
        
        # register callback to instance for parameter
        QObject.connect(self._instance,
            self._instance.valueChangedSignal(qgisParam),
            lambda x: self.onParameterChanged(qgisParam, x))

    def onParameterChanged(self, qgisParam, value):
        if self._blockSignals == True:
            return

        self._blockSignals = True

        mod = self.graph.modules[qgisParam.ids[0]]
        port = mod.getPortByID( qgisParam.ids[1] )
        port.setValue(value)
        
        self._blockSignals = False
    
    def instance(self):
        return self._instance

    def returnBoolean(self, tf):
        if tf == "True":
            return True
        else:
            return False
            
class ModuleInstance(processing.ModuleInstance):
    def __init__(self, module):
        processing.ModuleInstance.__init__(self, module)
        self.graph = module.graph
        QObject.connect(self, self.valueChangedSignal(self.stateParameter), self.stateParameterValueChanged)
        
    def stateParameterValueChanged(self, state):
        if state == StateParameter.State.running:
            self.graph.executeGraph()
            # set outputs of graph.modules into Module self parameters
            for mod in self.graph.modules.values():
                for port in mod.getPorts(2): # PortType.Source ~ 2
                    if not port.connected:
                        for par in self.parameters().keys():
                            if par.role() == 2:
                                self.setValue( par, port.outputData() )
