# -*- coding: utf-8 -*-

#	QGIS Processing panel plugin.
#
#	checkmodulesupport.py (C) Camilo Polymeris
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

from processing import framework
from processing.parameters import *
import saga_api


def unsupportedParametersByModule(module):
    parameters = list()
    for parameter in module.parameters():
        if parameter.__class__ == Parameter:
            parameters.append(parameter)
    return parameters
    
def printModuleSupportSummary():
    supportedStrings = list()
    unsupportedStrings = list()
    unsupportedParameterCountByType = dict()
    interactiveModuleCount = 0
    for module in framework.modules():
        moduleUnsupportedParameterTypes = set()
        unsup = unsupportedParametersByModule(module)
        try:
            # SAGA specific
            isInteractive = module.interactive
        except AttributeError:
            isInteractive = False
        if isInteractive:
            interactiveModuleCount += 1
        if not unsup and not isInteractive:
            tagsString = ', '.join(module.tags())
            supportedStrings.append("**%s** (_%s_)" % (module.name(), tagsString))
        elif not unsup and isInteractive:
            unsupportedStrings.append("**%s** is _interactive_." % module.name())
        else:
            if len(unsup) == 1:
                unsupString = "parameter " + unsup[0].name()
            else:
                unsupNames = [p.name()  for p in unsup]
                unsupString = ', '.join(unsupNames[:-1])
                unsupString = "parameters " + unsupString + ' & ' + unsupNames[-1]
            if not isInteractive:
                unsupportedStrings.append("**%s** is missing support for %s." % (module.name(), unsupString))
            else:
                unsupportedStrings.append("**%s** is _interactive_ and missing support for %s." % (module.name(), unsupString))
        try:
            for p in unsup: #this is SAGA specific
                typeName = saga_api.SG_Parameter_Type_Get_Name(p.sagaParameter.Get_Type())
                moduleUnsupportedParameterTypes.add(typeName)
            for typeName in moduleUnsupportedParameterTypes:
                if typeName in unsupportedParameterCountByType:
                    unsupportedParameterCountByType[typeName] += 1
                else:
                    unsupportedParameterCountByType[typeName] = 1
        except AttributeError:
            pass
    print """
        This is a programatically generated list of modules that should be supported.
        Not all of these modules have been tested and some may only work under some
        circumstances.
        """
    sN = len(supportedStrings)
    uN = len(unsupportedStrings) 
    tN = sN + uN
    sP = sN * 100 / tN
    print "###Status"
    print "Supported modules: %i (**%i%%**)\n" % (sN, sP)
    print "Non supported modules: %i\n" % uN
    print "Total registered modules: %i\n" % tN
    print
    print "##Supported modules"
    for s in sorted(supportedStrings):
        print "  * ", s
    print
    print "##Unsupported modules"
    for s in sorted(unsupportedStrings):
        print "  * ", s
    print
    print "##Number of modules by unsupported SAGA parameter type"
    for typ, n in sorted(unsupportedParameterCountByType.iteritems(), key = lambda (k,v): (v,k), reverse = True):
        if n == 1:
            print "  * One unsupported module depends on type *%s*" % typ
        else:
            print "  * %i unsupported modules depend on type *%s*" % (n, typ)
    print
    print "%i modules are not supported because they are interactive." % interactiveModuleCount

