# -*- coding: utf-8 -*-

#	 Plugin for adding some parameters like raster or vector layer as modules to Quantum GIS Processing Framework.
#
#	 inputparameters.py (C) Zdenek Ruzicka
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

from qgis.core import *
from PyQt4.QtCore import *

import processing
from processing.parameters import *
from processingplugin import core

class Plugin:
    def __init__(self, iface):
        # save reference to the QGIS interface
        self.iface = iface
    def unload(self):
        pass
    def modules(self):
        return [self.rasterInputLayer, self.rasterInputLayerFromPath, self.vectorInputLayer, self.vectorInputLayerFromPath]
    def initGui(self):
        self.rasterInputLayer = RasterInputLayer(self.iface)
        self.rasterInputLayerFromPath = RasterInputLayerFromPath(self.iface)
        self.vectorInputLayer = VectorInputLayer(self.iface)
        self.vectorInputLayerFromPath = VectorInputLayerFromPath(self.iface)
        processing.framework.registerModuleProvider(self)

class RasterInputLayer(processing.Module):
    def __init__(self, iface = None):
        self.iface = iface
        self.inParam = RasterLayerParameter("Input raster")
        self.inParam.setRole(Parameter.Role.input)
        self.outParam = RasterLayerParameter("Output raster")
        self.outParam.setRole(Parameter.Role.output)
        self.outParam.setMandatory(False)
        processing.Module.__init__(self, "Raster", 
            description = "Module is using in Wrokflow Builder for define raster layer just once, if someone wants.",
            parameters = [self.inParam, self.outParam], tags = ["workflow builder" ,"raster", "path"])
    def instance(self):
        return RasterInputLayerInstance(self, self.inParam, self.outParam)
            
class RasterInputLayerInstance(processing.ModuleInstance):
    def __init__(self, module, inParam, outParam):
        self.inParam = inParam
        self.outParam = outParam
        processing.ModuleInstance.__init__(self, module)
        QObject.connect(self,
            self.valueChangedSignal(self.stateParameter),
            self.onStateParameterChanged)
    def onStateParameterChanged(self, state):
        if state == StateParameter.State.running:
            self.setValue(self.outParam, self[self.inParam])
            self.setState(StateParameter.State.stopped)
class RasterInputLayerFromPath(processing.Module):
    def __init__(self, iface = None):
        self.iface = iface
        self.inParam = PathParameter("Path to input raster")
        self.inParam.setRole(Parameter.Role.input)
        self.outParam = RasterLayerParameter("Output raster")
        self.outParam.setRole(Parameter.Role.output)
        self.outParam.setMandatory(False)
        processing.Module.__init__(self, "Input raster by path", 
            description = "You can register raster to QGIS by giving the path.",
            parameters = [self.inParam, self.outParam], tags = ["workflow builder" ,"raster", "input", "path"])
    def instance(self):
        return RasterInputLayerFromPathInstance(self, self.inParam, self.outParam)
            
class RasterInputLayerFromPathInstance(processing.ModuleInstance):
    def __init__(self, module, inParam, outParam):
        self.inParam = inParam
        self.outParam = outParam
        processing.ModuleInstance.__init__(self, module)
        QObject.connect(self,
            self.valueChangedSignal(self.stateParameter),
            self.onStateParameterChanged)
    def onStateParameterChanged(self, state):
        if state == StateParameter.State.running:            
            path = self[self.inParam]
            name, ext = path.split('/')[-1].split('.')
            # create qgis rater layer
            raster = QgsRasterLayer(path)
            raster.setLayerName( "{0}{1}".format(name, ext) )
            # register layer to qgis - hmm, maybe it is not necessary...
            mreg = QgsMapLayerRegistry().instance()
            mreg.addMapLayer(raster)
            self.setValue(self.outParam, raster)
            self.setState(StateParameter.State.stopped)

class VectorInputLayer(processing.Module):
    def __init__(self, iface = None):
        self.iface = iface
        self.inParam = VectorLayerParameter("Input vector")
        self.inParam.setRole(Parameter.Role.input)
        self.outParam = VectorLayerParameter("Output vector")
        self.outParam.setRole(Parameter.Role.output)
        self.outParam.setMandatory(False)
        processing.Module.__init__(self, "Vector", 
            description = "Module is using in Wrokflow Builder for define vector layer just once, if someone wants.",
            parameters = [self.inParam, self.outParam], tags = ["workflow builder" ,"vector", "path"])
    def instance(self):
        return VectorInputLayerInstance(self, self.inParam, self.outParam)
            
class VectorInputLayerInstance(processing.ModuleInstance):
    def __init__(self, module, inParam, outParam):
        self.inParam = inParam
        self.outParam = outParam
        processing.ModuleInstance.__init__(self, module)
        QObject.connect(self,
            self.valueChangedSignal(self.stateParameter),
            self.onStateParameterChanged)
    def onStateParameterChanged(self, state):
        if state == StateParameter.State.running:
            self.setValue(self.outParam, self[self.inParam])
            self.setState(StateParameter.State.stopped)
            
class VectorInputLayerFromPath(processing.Module):
    def __init__(self, iface = None):
        self.iface = iface
        self.inParam = PathParameter("Path to input vector")
        self.inParam.setRole(Parameter.Role.input)
        self.outParam = VectorLayerParameter("Output vector")
        self.outParam.setRole(Parameter.Role.output)
        self.outParam.setMandatory(False)
        processing.Module.__init__(self, "Input vector by path", 
            description = "You can register vector to QGIS by giving the path.",
            parameters = [self.inParam, self.outParam], tags = ["workflow builder" ,"vector", "input", "path"])
    def instance(self):
        return VectorInputLayerFromPathInstance(self, self.inParam, self.outParam)
            
class VectorInputLayerFromPathInstance(processing.ModuleInstance):
    def __init__(self, module, inParam, outParam):
        self.inParam = inParam
        self.outParam = outParam
        processing.ModuleInstance.__init__(self, module)
        QObject.connect(self,
            self.valueChangedSignal(self.stateParameter),
            self.onStateParameterChanged)
    def onStateParameterChanged(self, state):
        if state == StateParameter.State.running:            
            path = self[self.inParam]
            name, ext = path.split('/')[-1].split('.')
            # create qgis vector layer
            vector = QgsVectorLayer(path,  name,  "ogr")
            #vector.setLayerName( "{0}{1}".format(name, ext) )
            # register layer to qgis - hmm, maybe it is not necessary...
            mreg = QgsMapLayerRegistry().instance()
            mreg.addMapLayer(vector)
            self.setValue(self.outParam, vector)
            self.setState(StateParameter.State.stopped)
