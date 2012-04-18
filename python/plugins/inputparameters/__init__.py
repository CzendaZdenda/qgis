# -*- coding: utf-8 -*-

#	 Plugin for adding some parameters like raster or vector layer as modules to Quantum GIS Processing Framework.
#
#	 __init__.py (C) Zdenek Ruzicka
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

def name():
    return "Inputs parameters for WB"
def description():
    return "Basic modules for input parameters in Workflow Builder for Processing Framework."
def version():
    return "Version 0.1"
def qgisMinimumVersion(): 
    return "1.0"
def authorName():
    return "Zdenek Ruzicka"
def classFactory(iface):
    import inputparameters 
    return inputparameters .Plugin(iface)
