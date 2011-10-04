# -*- coding: utf-8 -*-

#	SAGA Modules plugin for Quantum GIS
#
#	plugin.py (C) Camilo Polymeris
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
#   MA 02110-1301, USA.

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from sys import float_info

from osgeo import gdal

import os
import processing
from processing.parameters import *
from processingmanager.dialog import RangeBox
from blacklist import libraryIsBlackListed, moduleIsBlackListed
from blacklist import tagIsBlackListed
import saga_api as saga

def getLibraryPaths(userPath = None):
    try:
        paths = os.environ['MLB_PATH'].split(':')
    except KeyError:
        paths = ['/usr/lib/saga/', '/usr/local/lib/saga/']
        noMLBpath = True
    if userPath:
        paths = [userPath] + paths
    for p in paths:
        if os.path.exists(p):
            return [os.path.join(p, fn) for fn in os.listdir(p) if
                not libraryIsBlackListed(fn)]
    if noMLBpath:
        print "Warning: MLB_PATH not set."
    return []
    
def qgisizeString(s):
    try:
        s = str(s)
        s = str.replace(s, "Gridd", "Raster")
        s = str.replace(s, "Grid", "Raster")
        s = str.replace(s, "gridd", "raster")
        s = str.replace(s, "grid", "raster")
    except:
        # Some unicode characters seem to produce exceptions.
        # Just ignore those cases.
        pass
    return s

def qgisTempFilename(basename, extension):
    dir = tempfile.gettempdir()
    return os.path.join(dir, basename + "." + extension)
    
def sagaTempFilename(basename, extension):
    return CSG_String(qgisTempFilename(basename, extension))

class SAGAPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.window = iface.mainWindow()
    def initGui(self):
        self.libraries = list()
        self._modules = None
        keepSearching = True
        userPath = None
        while keepSearching:
            for p in getLibraryPaths(userPath):
                try:
                    self.libraries.append(Library(p, self.iface))
                except InvalidLibrary:
                    pass
            if self.libraries:
                keepSeaching = False
            else:
                userPath, keepSearching = QInputDialog.getText(
                    self.window,
                    self.window.tr("SAGA modules not found."),
                    self.window.tr("Please enter path to SAGA libraries:"));
    def unload(self):
        for l in self.libraries:
            processing.framework.unregisterModuleProvider(l)
            del l

class InvalidLibrary(RuntimeError):
    def __init__(self, name):
        RuntimeError.__init__(self, "Library invalid " + name + ".")
        
class Library:
    def __init__(self, filename, iface = None):
        self.sagalib = saga.CSG_Module_Library(
            saga.CSG_String(str(filename)))
        if not self.sagalib.is_Valid():
            raise InvalidLibrary(filename)
        self._modules = None
        self.iface = iface
        processing.framework.registerModuleProvider(self)
    def modules(self):
        if self._modules is not None:
            return self._modules
        self._modules = set()
        for i in range(self.sagalib.Get_Count()):
            try:
                self._modules.add(Module(self.sagalib, i, self.iface))
            except InvalidModule:
                pass
        return self._modules
    def __del__(self):
        self.sagalib.Destroy()

class InvalidModule(RuntimeError):
    def __init__(self, name):
        RuntimeError.__init__(self, "Module invalid " + name + ".")
            
class Module(processing.Module):
    def __init__(self, lib, i, iface = None):
        self.module = lib.Get_Module(i)
        if not self.module:
            raise InvalidModule("Module #%i is invalid" % i)
        self._name = qgisizeString(self.module.Get_Name())
        if moduleIsBlackListed(self._name):
            raise InvalidModule("Module %s is blacklisted" % self._name)
        self.iface = iface
        self.interactive = self.module.is_Interactive()
        self.grid = self.module.is_Grid()
        if self.interactive and self.grid:
            self.module = lib.Get_Module_Grid_I(i)
        elif self.grid:
            self.module = lib.Get_Module_Grid(i)
        elif self.interactive:
            self.module = lib.Get_Module_I(i)
        self._parameters = None
        libTags = set([processing.Tag(qgisizeString(s.lower())) for
            s in lib.Get_Menu().c_str().split("|") if
            not tagIsBlackListed(s.lower())])
        # tag to be added to the programatically generated ones.
        self.sagaTag = set([processing.Tag('saga')]) | libTags 
        self.layerRegistry = QgsMapLayerRegistry.instance()
        # only one instance per SAGA module
        self._instance = ModuleInstance(self)
        processing.Module.__init__(self,
            self._name,
            qgisizeString(self.module.Get_Description()))
            
    def instance(self):
        return self._instance
        
    def addParameter(self, sagaParam):
        sagaToQGisParam = {
            #saga.PARAMETER_TYPE_Node:  ParameterList,
            saga.PARAMETER_TYPE_Int:    NumericParameter,
            saga.PARAMETER_TYPE_Double: NumericParameter,
            saga.PARAMETER_TYPE_Degree: NumericParameter,
            saga.PARAMETER_TYPE_Bool:   BooleanParameter,
            saga.PARAMETER_TYPE_String: StringParameter,
            saga.PARAMETER_TYPE_Text:   StringParameter,
            saga.PARAMETER_TYPE_FilePath: PathParameter,
            saga.PARAMETER_TYPE_Choice: ChoiceParameter,
            saga.PARAMETER_TYPE_Shapes: VectorLayerParameter,
            saga.PARAMETER_TYPE_Grid:   RasterLayerParameter,
            saga.PARAMETER_TYPE_Range:  RangeParameter,
            #saga.PARAMETER_TYPE_Grid_System: GridSystemParameter
            # Taking grid system from output grid, for now.
            # TODO: allow resampling?
            saga.PARAMETER_TYPE_Grid_System: None
        }
        name = qgisizeString(sagaParam.Get_Name())
        descr = qgisizeString(sagaParam.Get_Description())
        typ = sagaParam.Get_Type()
        if sagaParam.is_Output():
            role = Parameter.Role.output
        else:
            role = Parameter.Role.input
        mandatory = not sagaParam.is_Optional()
        
        try:
            pc = sagaToQGisParam[typ]
            if not pc: # We are ignoring certain types of parameters
                return            
            qgisParam = pc(name, descr, role=role)
            if pc == NumericParameter:
                qgisParam.setDefaultValue(sagaParam.asDouble())
            if pc == ChoiceParameter:
                choiceParam = sagaParam.asChoice()
                choices = [qgisizeString(choiceParam.Get_Item(i)) for i
                    in range(choiceParam.Get_Count())]
                qgisParam.setChoices(choices)
                qgisParam.setDefaultValue(sagaParam.asInt())
                
            elif (pc == VectorLayerParameter or
                pc == RasterLayerParameter):
                if role == Parameter.Role.output:
                    self._instance.outLayer.append(qgisParam)
                else:
                    self._instance.inLayer.append(qgisParam)
                # force update of layer
                qgisParam.sagaParameter = sagaParam
                self.onParameterChanged(qgisParam, None)
            
            elif pc == NumericParameter:
                vp = sagaParam.asValue()
                if vp.has_Minimum():
                    bottom = vp.Get_Minimum()
                else:
                    bottom = float_info.min
                if vp.has_Maximum():
                    top = vp.Get_Maximum()
                else:
                    top = float_info.max
                val = QDoubleValidator(None)
                val.setRange(bottom, top)
                qgisParam.setValidator(val)
                
        except KeyError: # Parameter types not in the above dict.
            typeName = saga.SG_Parameter_Type_Get_Name(typ)
            qgisParam = Parameter(name, str, descr,
                "Unsupported parameter of type %s." % typeName,
                role=role)
                
        qgisParam.sagaParameter = sagaParam
        
        qgisParam.setMandatory(mandatory)
        self._parameters.add(qgisParam)
        
        # register callback to instance for parameter
        QObject.connect(self._instance,
            self._instance.valueChangedSignal(qgisParam),
            lambda x: self.onParameterChanged(qgisParam, x))
            
    def onParameterChanged(self, qgisParam, value):
        sagaParam = qgisParam.sagaParameter
        typ = sagaParam.Get_Type()
        pc = qgisParam.__class__
        # special cases - layers, choices, files, etc.
        # for layers we only set the saga param on excecution
        if (pc == LayerParameter or
            pc == VectorLayerParameter or
            pc == RasterLayerParameter):
                qgisParam.layer = value
        elif pc == RangeParameter:
            low, high = value
            sagaParam.asRange().Set_Range(low, high)
        elif pc == GridSystemParameter:
            cellsize = value.cellsize
            xMin, xMax = value.xRange
            yMin, yMax = value.yRange
            self.module.Get_System().Assign(cellsize, xMin, yMin,
                xMax, yMax)
        elif pc == StringParameter:
            # convert QString to CSG_String
            string = saga.CSG_String(str(value))
            sagaParam.Get_Data().Set_Value(string)
        else:
            # generic case - numerics, booleans, etc.
            sagaParam.Set_Value(value)
            
    def parameters(self):
        if self._parameters is not None:
            return self._parameters
        self._parameters = set()
        paramsList = [self.module.Get_Parameters()]
        paramsList += [self.module.Get_Parameters(i) for i in
            range(self.module.Get_Parameters_Count())]
        for params in paramsList:
            for j in range(params.Get_Count()):
                self.addParameter(params.Get_Parameter(j))
        return self._parameters
        
    def tags(self):
        return processing.Module.tags(self) | self.sagaTag
        
    def __del__(self):
        if self.module:
            self.module.Destroy()
            self.module = None

class ModuleInstance(processing.ModuleInstance):
    def __init__(self, module):
        processing.ModuleInstance.__init__(self, module)
        QObject.connect(
            self, self.valueChangedSignal(self.stateParameter),
            self.stateParameterValueChanged)
        self.inLayer = list()
        self.outLayer = list()
        
    def stateParameterValueChanged(self, state):
        """ Only reacts to start running state, ignore others.
        """
        sm = self.module().module # the SAGA module
        if state != StateParameter.State.running:
            return
        modName = self.module().name()
        
        inputGrid = None
        # set values of saga parameters...
        # ...and in the case of input layers, 
        # also export from qgis to saga
        for param in self.inLayer:
            pc = param.__class__
            if not param.layer and param.isMandatory():
                msg = "Mandatory parameter %s not set." % param.name()
                self.setFeedback(msg, critical = True)
                return
            elif not param.layer:
                continue
            basename = "qgis-saga%s" % id(param.layer)
            dpUri = str(param.layer.dataProvider().dataSourceUri())
            dpDescription = param.layer.dataProvider().description()              
            if pc == VectorLayerParameter:
                isLocal = dpDescription.startsWith('OGR data provider')
                if isLocal:
                    fn = saga.CSG_String(dpUri)
                else:
                    fn = sagaTempFilename(basename, "shp")
                    QgsVectorFileWriter.writeAsVectorFormat(param.layer,
                        fn.c_str(), "CP1250", param.layer.crs())
                param.sagaParameter.Set_Value(saga.SG_Create_Shapes(fn))
            if pc == RasterLayerParameter:
                isLocal = dpDescription.startsWith('GDAL provider')
                if isLocal:
                    sagaFn = sagaTempFilename(basename, "sgrd")
                    # GDAL & QGIS use the sdat file as reference,
                    # unlike SAGA
                    qgisFn = qgisTempFilename(basename, "sdat")
                else:
                    msg = "Sorry. Only local raster layers supported."
                    self.setFeedback(msg, critical = True)
                    return
                self.setFeedback("Converting raster to SAGA format...")
                # convert input to saga grid file -- adapted from
                # GDAL tutorial
                driver = gdal.GetDriverByName("SAGA")
                source = gdal.Open(dpUri)
                destination = driver.CreateCopy(qgisFn, source, 0 )
                # Once we're done, close properly the dataset
                source = None
                destination = None
                grid = saga.SG_Create_Grid()
                if grid.Create(sagaFn) == 0:
                    self.setFeedback("Couldn't create SAGA input raster.",
                        critical = True)
                    return
                # Store first input grid for output.
                if not inputGrid:
                    inputGrid = grid
                param.sagaParameter.Set_Value(grid)
        
        for param in self.outLayer:
            pc = param.__class__
            if pc == VectorLayerParameter:
                param.sagaLayer = saga.SG_Create_Shapes()
                param.sagaParameter.Set_Value(param.sagaLayer)
            if pc == RasterLayerParameter:
                # use an input grid to get the grid system
                if not inputGrid:
                    self.setFeedback("No input raster specified.", True)
                    return
                param.sagaLayer = saga.SG_Create_Grid(inputGrid)
                sm.Get_System().Assign(inputGrid.Get_System())
                param.sagaParameter.Set_Value(param.sagaLayer)
        
        self.setFeedback("Module '%s' execution started." % modName)
        if sm.Execute() != 0:
            self.setFeedback("SAGA Module execution suceeded.")
            # umm- what if there is no iface?
            iface = self.module().iface
            # now import output layers
            for param in self.outLayer:
                basename = "saga-qgis%s" % id(param.sagaLayer)
                pc = param.__class__
                if pc == VectorLayerParameter:
                    # no implicit conversion!
                    fn = sagaTempFilename(basename, "shp")
                    # tell SAGA to save the layer
                    param.sagaLayer.Save(fn)
                    # load it into QGIS.
                    # TODO: where?
                    iface.addVectorLayer(fn.c_str(), basename, "ogr")
                elif pc == RasterLayerParameter:
                    # no implicit conversion!
                    sagaFn = sagaTempFilename(basename, "sgrd")
                    qgisFn = qgisTempFilename(basename, "sdat")
                    # tell SAGA to save the layer
                    param.sagaLayer.Save(sagaFn)
                    # load it into QGIS.
                    # TODO: where?
                    iface.addRasterLayer(qgisFn, basename)
        else:
            self.setFeedback("Module execution failed.")
        self.setState(StateParameter.State.stopped)

class GridSystem:
    def __init__(self, cellsize, xRange, yRange):
        self.cellsize = cellsize
        self.xRange = xRange
        self.yRange = yRange

class GridSystemParameter(Parameter):
    def __init__(self, name, description = None,
        defaultValue = GridSystem(1, (0, 100), (0, 100)), role = None):
        Parameter.__init__(self, name, GridSystem, description,
            defaultValue, role)
    def widget(self, gSystem):
        return GridSystemWidget(gSystem)
        
class GridSystemWidget(QGridLayout):
    def __init__(self, gSystem, parent = None):
        QGridLayout.__init__(self, parent)
        self.cellsizeWidget = QDoubleSpinBox(parent)
        self.cellsizeWidget.setValue(gSystem.cellsize)
        self.xRangeWidget = RangeBox(gSystem.xRange, parent)
        self.yRangeWidget = RangeBox(gSystem.yRange, parent)
        self.addWidget(QLabel(self.tr("Cellsize")), 0, 0, 1, 2)
        self.addWidget(self.cellsizeWidget, 0, 3)
        self.addWidget(QLabel(self.tr("X Range")), 1, 0)
        self.addItem(self.xRangeWidget, 1, 1, 1, 3)
        self.addWidget(QLabel(self.tr("Y Range")), 2, 0)
        self.addItem(self.yRangeWidget, 2, 1, 1, 3)
        QObject.connect(self.cellsizeWidget,
            SIGNAL("valueChanged(int)"), self.onValueChanged)
        QObject.connect(self.xRangeWidget,
            SIGNAL("valueChanged"), self.onValueChanged)
        QObject.connect(self.yRangeWidget,
            SIGNAL("valueChanged"), self.onValueChanged)
    def value(self):
        return GridSystem(self.cellsizeWidget.value(),
            self.xRangeWidget.value(),
            self.yRangeWidget.value())
    def setValue(self, v):
        self.cellsizeWidget.setValue(v.cellsize)
        self.xRangeWidget.setValue(v.xRange)
        self.yRangeWidget.setValue(v.yRange)
    def onValueChanged(self, _):
        self.emit(SIGNAL("valueChanged"), self.value())
        
