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
import saga_api as saga

def getLibraryPaths():
    try:
        paths = os.environ['MLB_PATH'].split(':')
    except KeyError:
        paths = ['/usr/lib/saga/', '/usr/local/lib/saga/']
        print "MLB_PATH not set."
    for p in paths:
        print "Seaching SAGA modules in " + p + "."
        if os.path.exists(p):
            return [p + fn for fn in os.listdir(p)]
    raise RuntimeError("No SAGA modules found.")

class SAGAPlugin(processing.Plugin):
    def __init__(self, iface):
		self.libraries = [Library(p) for p in getLibraryPaths()]
		processing.Plugin.__init__(self, iface, self.libraries)

class Library(processing.Library):
    def __init__(self, filename):
        print filename
        lib = saga.CSG_Module_Library(saga.CSG_String(filename))
        print lib.is_Valid()
        if not lib.is_Valid(): return
        modules = [Module(lib, i) for i in range(lib.Get_Count())]
        processing.Library.__init__(self,
            lib.Get_Name().c_str(), lib.Get_Description().c_str(),
            modules)
            
class Module(processing.Module):
    def __init__(self, lib, i):
        self.module = lib.Get_Module(i)
        if not self.module: return
        self.interactive = self.module.is_Interactive()
        self.grid = self.module.is_Grid()
        if self.interactive and self.grid:
            self.module = lib.Get_Module_Grid_I(i)
        elif self.grid:
            self.module = lib.Get_Module_Grid(i)
        elif self.interactive:
            self.module = lib.Get_Module_I(i)
        processing.Module.__init__(self,
            self.module.Get_Name(),
            self.module.Get_Description())
