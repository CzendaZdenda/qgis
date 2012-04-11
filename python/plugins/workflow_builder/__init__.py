# -*- coding: utf-8 -*-

#   Plugin for reading workflows for Quantum GIS Processing Framework stored as XML files
#
#   __init__.py (C) Zdenek Ruzicka
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

def name():
    return "Workflow for Processing Framework Manager"
def description():
    return "Makes workflows as Processing Framework Modules from files stored in ~/.qgis/workflow/ as XML file."
def version():
    return "Version 0.1"
def qgisMinimumVersion(): 
    return "1.0"
def authorName():
    return "Zdenek Ruzicka"
def classFactory(iface):
    import workflow_builder
    return workflow_builder.Plugin(iface)

