# -*- coding: utf-8 -*-

#	QGIS Processing Framework
#
#	parameters.py (C) Camilo Polymeris
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

class Framework:
    def __init__(self):
        self._modules = dict()
    """ Register library with the framework.
        Adds the libraries modules to the framework's list.
    """
    def registerLibrary(self, library):
        for m in library.modules():
            self._modules[m.name()] = m
    """ Returns complete list of registered modules.
    """
    def modules(self):
        return self._modules
    """ Returns modules that match the tag specified.
    """
    def modulesByTag(self, tag):
        tag = Tag(tag)
        return filter(lambda m: tag in m.tags(), self.modules())

framework = Framework()

""" Processing plugin baseclass.
    Partially overrides the QGIS plugin interface.
    Subclass this when implementing your own processing plugin.
"""
class Plugin:
    def __init__(self, iface, libraries):
        self._iface = iface
        self._libraries = libraries
    def initGui(self):
        pass
    def unload(self):
        pass

# is this class necessary/useful? Perhaps move this functionality to
# plugin.
class Library:
    def __init__(self, name, description = None, modules = None):
        self._name = name
        self._description = description
        self._modules = modules
        print "Loading library " + name
        framework.registerLibrary(self)
    def name(self):
        return self._name
    def description(self):
        return self._description
    def modules(self):
        return self._modules

""" Case insensitive strings for tag usage.
"""
class Tag(str):
    """ Case insensitive string comparison ignoring extra whitespace
        at the beggining or end of the tag.
        
        >>> Tag('ArArAt') == Tag('ararat')
        True
        >>> Tag('Kenya') == Tag('Kilimanjaro')
        False
        >>> Tag('ACONCAGUA') != Tag(' AcOnCaGuA ')
        False
    """
    def __cmp__(self, other):
        return self.strip().upper() == other.strip().upper()

""" Default list of tags.
    Not binding.
"""
standardTags = [Tag(s) for s in ["2D", "3D", "analysis",
            "classification", "database", "display", "export", "filter",
            "imagery", "import", "interactive", "paint", "photo",
            "postscript", "projection", "raster", "simulation",
            "statistics", "vector"]]

""" A processing module.
"""
class Module:
    def __init__(self, name,
        description = None, tags = None, parameters = None):
            self._name = name
            self._description = description
            self._tags = tags
            self._parameters = parameters
            print "Loading module " + name
    def name(self):
        return self._name
    def description(self):
        return self._description
    def tags(self):
        if self._tags:
            return self._tags
        else:
            return [Tag(s.strip(" .-_()/,")) for s in
                self.name().lower().split()]
    def parameters(self):
        return self._parameters
