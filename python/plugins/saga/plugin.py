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

import os
import processing
from processing.parameters import *
import saga_api as saga

def getLibraryPaths():
    try:
        paths = os.environ['MLB_PATH'].split(':')
    except KeyError:
        paths = ['/usr/lib/saga/', '/usr/local/lib/saga/']
        noMLBpath = True
    for p in paths:
        #print "Seaching SAGA modules in " + p + "."
        if os.path.exists(p):
            return [p + '/' + fn for fn in os.listdir(p)]
    if noMLBpath:
        print "Warning: MLB_PATH not set."
    raise RuntimeError("No SAGA modules found in %s." % paths)

class SAGAPlugin:
    def __init__(self, _):
        self.libraries = list()
        self._modules = None
        for p in getLibraryPaths():
            try:
                self.libraries.append(Library(p))
            except InvalidLibrary:
                pass
    def initGui(self):
        pass
    def unload(self):
        pass

class InvalidLibrary(RuntimeError):
    def __init__(self, name):
        RuntimeError.__init__(self, "Library invalid " + name + ".")
        
class Library:
    def __init__(self, filename):
        self.sagalib = saga.CSG_Module_Library(saga.CSG_String(filename))
        if not self.sagalib.is_Valid():
            raise InvalidLibrary(filename)
        self._modules = None
        processing.framework.registerModuleProvider(self)
    def modules(self):
        if self._modules is not None:
            return self._modules
        self._modules = set()
        for i in range(self.sagalib.Get_Count()):
            try:
                self._modules.add(Module(self.sagalib, i))
            except InvalidModule:
                pass
        return self._modules

class InvalidModule(RuntimeError):
    def __init__(self, name):
        RuntimeError.__init__(self, "Module invalid " + name + ".")
            
class Module(processing.Module):
    def __init__(self, lib, i):
        self.module = lib.Get_Module(i)
        if not self.module:
            raise InvalidModule("#" + str(i))
        self.interactive = self.module.is_Interactive()
        self.grid = self.module.is_Grid()
        if self.interactive and self.grid:
            self.module = lib.Get_Module_Grid_I(i)
        elif self.grid:
            self.module = lib.Get_Module_Grid(i)
        elif self.interactive:
            self.module = lib.Get_Module_I(i)
        self._parameters = None
        # only one instance per SAGA module
        self._instance = ModuleInstance(self)
        processing.Module.__init__(self,
            self.module.Get_Name(),
            self.module.Get_Description())
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
            saga.PARAMETER_TYPE_Grid:   RasterLayerParameter
        }
        name = sagaParam.Get_Name()
        descr = sagaParam.Get_Description()
        typ = sagaParam.Get_Type()
        if sagaParam.is_Output():
            role = Parameter.Role.output
        else:
            role = Parameter.Role.input
        mandatory = not sagaParam.is_Optional()
        try:
            qgisParamTyp = sagaToQGisParam[typ]            
            qgisParam = qgisParamTyp(name, descr)
            if qgisParamTyp == ChoiceParameter:
                sagaParam = sagaParam.asChoice()
                choices = [sagaParam.Get_Item(i) for i in
                    range(sagaParam.Get_Count())]
                qgisParam.setChoices(choices)
                qgisParam.setValue(0)
        except KeyError:
            qgisParam = Parameter(name, descr, str)
        qgisParam.setRole(role)
        qgisParam.setMandatory(mandatory)
        self._parameters.add(qgisParam)
        # register callback to instance for parameter
        QObject.connect(self._instance,
            self._instance.valueChangedSignal(qgisParam),
            lambda x: self.onParameterChanged(sagaParam, x))
    def onParameterChanged(self, sagaParam, value):
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
        return processing.Module.tags(self) | set([processing.Tag('saga')])

class ModuleInstance(processing.ModuleInstance):
    def __init__(self, module):
        processing.ModuleInstance.__init__(self, module)
        QObject.connect(
            self, self.valueChangedSignal(self.stateParameter),
            self.stateParameterValueChanged)
    def stateParameterValueChanged(self, state):
        """ Only reacts to start running state, ignore others.
        """
        sm = self.module().module # the SAGA module
        if state != self.stateParameter.State.running:
            return
        print "Module instance '%s' execution started." % self.module().name()
        if sm.Execute():
            print "Module execution suceeded."
        else:
            print "Module execution failed."
