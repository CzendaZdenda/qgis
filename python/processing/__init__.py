# -*- coding: utf-8 -*-

#	QGIS Processing Framework
#
#	__init__.py (C) Camilo Polymeris
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

import moduleinstance
from itertools import chain
ModuleInstance = moduleinstance.ModuleInstance

class Tag(str):
    """ Case insensitive strings for tag usage. """
    def __cmp__(self, other):
        """ Case insensitive string comparison ignoring extra whitespace
        at the beggining or end of the tag.
        
        >>> Tag('ArArAt') == Tag('ararat')
        True
        >>> Tag('Kenya') == Tag('Kilimanjaro')
        False
        >>> Tag('ACONCAGUA') != Tag(' AcOnCaGuA ')
        False
        """
        return self.strip().upper() == other.strip().upper()

class Framework:
    """ The Framework is instantiated in a singleton:
    processing.framework.
    This is the centerpiece of the QGIS Processing Framework, which
    keeps track of all available modules through moduleproviders.
    (See registerModuleProvider method)
    It sorts these modules by tag and provides the model data for the
    Processing Panel Plugin, which handles the GUI side of things.
    """
    def __init__(self):
        self._moduleProviders = set()
    def moduleProviders(self):
        """ Module providers are returned in a python set.
        """
        return self._moduleProviders
    def registerModuleProvider(self, moduleprovider):
        """ Register module providers with the framework.
        moduleprovider must implement the modules() method,
        which returns a list of modules.
        """
        self._moduleProviders.add(moduleprovider)
    def unregisterModuleProvider(self, moduleprovider):
        """ Call this method to unregister a moduleprovider from your
        backend's deinitialization code, e.g. unload() method.
        It will return silently if the moduleprovider is not registered.
        """
        self._moduleProviders.discard(moduleprovider)
    def modules(self):
        """ Returns complete set of registered modules by all module
        providers.
        """
        moduleList = [set(mp.modules()) for mp in self._moduleProviders]
        return set(chain(*moduleList))
    def modulesByTag(self, tag):
        """ Returns all modules that match the tag specified.
        """
        tag = Tag(tag)
        return filter(lambda m: tag in m.tags(), self.modules())
    def tagFrequency(self):
        """ Return a dict of tag => relative tag frequency.
        Relative tag ranges from 0.0 to 1.0, the latter identifing tags
        that every module has.
        This is a measure of how relevant a tag is.
        """
        tags = dict()
        # perhaps standard tags could be given a bump?
        modules = self.modules()
        for m in modules:
            for t in m.tags():
                if t in tags: tags[t] += 1.0
                else: tags[t] = 1.0
        # divide by number of modules to get a list of
        # relative frequencies.
        tags = map(lambda (k, v): (k, v / len(modules)), tags.items())
        return dict(tags)
    def usedTags(self):
        """ Return a set of all tags used by at least 1 module.
        May contain standard tags and/or implementation-specific tags.
        """
        return set(self.tagFrequency().keys())
    def representativeTags(self):
        """ Returns list of tags that aren't too frequent or to infrequent
        to be representative.
        That is, cut tags that only apply to 2.5% of the modules or to
        more than 15%.
        In future, this criterion will be user-modifiable from the
        settings dialog.
        """
        criterion = lambda (_, v): v > 0.025 and v < 0.25
        tags = self.tagFrequency().items()
        if not tags: return tags
        tags, _ = zip(*filter(criterion, tags))
        return tags
    def __getitem__(self, name):
        """ Scripting convenience function.
        Get a module by name.
        """
        modules = filter(lambda m: m.name() == name, self.modules())
        if modules:
            return modules[0]
        return None
    """ Default set of tags. Not binding. It is recommended that
    backends provide their own tags in addition to these, including
    at least one describing the backend library, e.g. "saga".
    """
    standardTags = set([Tag(s) for s in ["2D", "3D", "analysis",
        "classification", "database", "display", "export", "filter",
        "imagery", "import", "interactive", "paint", "photo",
        "postscript", "projection", "raster", "simulation",
        "statistics", "vector"]])

""" Singleton framework.
See Framework class description.
"""
framework = Framework()

class Module:
    """ A processing module.
    As a backend developer you will most likely want to subclass this.
    As a user or script developer, get a module from the framework
    singleton, then one or more ModuleInstances.
    See ModuleInstace class for more information.
    
    Attributes:
    name -- this is the handle to the Module, and the name displayed
        in the GUI.
    description -- this is a longer description of the module's
        functionality, may be multi-line and HTML-formatted.
    tags -- this is a set of case-insensitive classificators of the
        module.
    parameters -- this is a set of input & ouput parameters of different
        types. Control and feedback is also handled through this
        mechanism. See parameters module for more information.
    """
    def __init__(self, name,
        description = "", tags = None, parameters = None):
            """ Module initialization.
            Most attributes of the object can be set at initialization.
            As a backend developer you may want to override the getters
            name(), description(), tags(), instead, if more complicated
            code is necessary.
            See the class' description for an explanation of the
            arguments.
            """
            self._name = name
            self._description = description
            self._tags = tags
            self._parameters = parameters
    def instance(self):
        """ Return a new module instance.
        Call this instead of the ModuleInstance constructor.
        Backend implementations may want to override only this method
        as an alternative to the whole class if your interface is simple
        enough.
        """
        return ModuleInstance(self)
    def name(self):
        return self._name
    def description(self):
        """ The modules description string.
        If no description is provided on construction, returns an empty
        string.
        """
        return self._description
    def tags(self):
        """ The modules tags.
        By default, this method searches for 'standard tags' in the
        module's name & description. Dumb method, so reimplement if
        possible.
        To customize this, either indicate tags on construction or
        override this method.
        """
        if self._tags:
            return set(self._tags)
        else:
            text = (self.name() + " " + self.description()).lower()
            tags = set([Tag(s.strip(" .-_()/,")) for s in text.split()])
            return Framework.standardTags & tags
    def parameters(self):
        """ The module's parameters.
        Specifiy on construction or override this method to provide your
        own. Else raises an NotImplementedError.
        """
        if self._parameters:
            return self._parameters
        else:
            raise NotImplementedError
    def execute(self, **kwargs):
        """ Scripting convenience function.
        Excecute a ModuleInstance of this Module, with specified
        parameters.
        """
        from PyQt4.QtCore import QObject
        instance = self.instance()
        #QObject.connect(instance, instance.valueChangedSignal(instance.feedbackParameter), print)
        for p in instance.parameters():
            if p.name() in kwargs:
                instance[p] = kwargs[p.name()]
        instance.setState(parameters.StateParameter.State.running)
