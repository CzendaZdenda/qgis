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

""" This module is part of the QGIS Processing Framework.
"""

import PyQt4.QtGui as QtGui
from qgis.core import QgsMapLayer, QgsVectorLayer, QgsRasterLayer

class Parameter:
    """ Base class for processing parameters.
    Parameters may represent input or output values, including special
    cases control and feedback. The former is an interface to the
    module instance's internal state (stopped, setup, running,
    interaction, paused), while the latter is the means to provide
    feedback (messages, status indicators, errors) to the user or
    controlling code.
    Certain basic parameter types are implemented in the framework,
    but, of course, backend developers can implement their own by
    expanding this module's classes.
    
    For description of the argument's see their getter methods:
    name(), description(), type(), role(), userLevel(), isMandatory(),
    defaultValue(), validator(), widget()
    """
    class Role:
        """ Enumeration of possible parameter roles.
        """
        input, output, control, feedback = 1, 2, 3, 4
    class UserLevel:
        """ Enumeration of parameter user levels.
        This determines if parameters are shown depending on user
        preferences.
        """
        basic, advanced = 1, 2
    def __init__(self, name, pType, description = None,
                 defaultValue = None, role = None,
                 mandatory = True, validator = None):
        self._name = name
        self._description = description
        self._type = pType
        self._defaultValue = defaultValue
        self._role = role
        self._mandatory = mandatory
        self._validator = validator
    def name(self):
        """ The name displayed in the module instance's run dialog.
        """
        return self._name
    def description(self):
        """Longer, optional description of the parameter.
        Currently unused. May appear as a tool-tip in the future.
        """
        return self._description
    def type(self):
        """ Internal type representation.
        Typically a class or basic python type.
        """
        return self._type
    def setRole(self, role):
        self._role = role
    def role(self):
        """ See Parameter.Role and Parameter classes.
        """
        return self._role
    def userLevel(self):
        """ See Parameter.UserLevel class.
        """
        return Parameter.UserLevel.basic
    def setMandatory(self, mandatory):
        self._mandatory = mandatory
    def isMandatory(self):
        """ A mandatory parameter must be set when excecuting the
        module instance.
        If not set by the user it may still use its default value,
        if present.
        An optional parameter can be set or not, but will allways
        be set if a default value is provided.
        """
        return self._mandatory
    def defaultValue(self):
        """ The parameter's default value."""
        if self._defaultValue is not None:
            return self._defaultValue
        try:
            return self.type()()
        except:
            return ""
    def setDefaultValue(self, value):
        self._defaultValue = value
    def validator(self):
        """ The parameters validator.
        Uses QValidator's interface, but concrete behavior may change
        from one parameter to another.
        """
        return self._validator
    def setValidator(self, validator):
        self._validator = validator
    def widget(self, value):
        """ If this method is implemented by the backend developer,
        it should return a QWidget instance representing this
        parameter's value (not name or description).
        In the case of built-in parameters,
        no widget is provided, but instead this functionality is
        hard-coded in the Processing Panel, to keep this framework
        GUI-agnostic.
        """
        raise NotImplementedError

class ParameterList(Parameter):
    """ List of parameters with fixed type.
    """
    def __init__(self, name, itemType, description = None,
				 defaultValue = [], role = None):
        self._itemType = itemType
        Parameter.__init__(self, name, list, description,
            defaultValue, role)

class StateParameter(Parameter):
    """ This pseudo-parameter controls the internal state of the
    module instance.
    """
    class State:
        stopped, running = 1, 2
    def __init__(self, defaultValue = State.stopped):
        Parameter.__init__(self, "State", int, "",
            defaultValue, Parameter.Role.control)

class FeedbackParameter(Parameter):
    """ This parameter passes feedback to the user: be it messages,
    status indicators, errors, etc.
    """
    def __init__(self, name = "Feedback", pType = str):
        Parameter.__init__(self, name, pType,
            role = Parameter.Role.feedback)

class NumericParameter(Parameter):
    """ Parameter backed by a python float. Represents all kinds
    of numeric values the module instance may input or output.
    Per default, it is displayed as a spinbox.
    """
    def __init__(self, name, description = None,
				 defaultValue = 0.0, role = None):
        Parameter.__init__(self, name, float, description,
            defaultValue, role)

class RangeParameter(Parameter):
    """ A range is a pair of numeric values where top > bottom.
    Per default displayed as a pair of spinboxes.
    """
    def __init__(self, name, description = None,
				 defaultValue = (0.0, 100.0), role = None):
        Parameter.__init__(self, name, tuple, description,
            defaultValue, role)

class BooleanParameter(Parameter):
    """ A basic boolean (True/False) parameter.
    Per default displayed as a check box.
    """
    def __init__(self, name, description = None,
				 defaultValue = False, role = None):
        Parameter.__init__(self, name, bool, description,
            defaultValue, role)

class ChoiceParameter(Parameter):
    """ A int-backed choice among enumerated values.
    Per default displayed as a drop box.
    """
    def __init__(self, name, description = None,
				 defaultValue = -1, role = None, choices = []):
        Parameter.__init__(self, name, int, description,
            defaultValue, role)
        self._choices = choices
    def setChoices(self, choices):
        self._choices = choices
    def choices(self):
        return self._choices

class StringParameter(Parameter):
    """ A basic string parameter.
    Per default displayed as a line edit widget or label (in the case
    of output).
    """
    def __init__(self, name, description = None,
				 defaultValue = "", role = None):
        Parameter.__init__(self, name, int, description,
            defaultValue, role)
            
class PathParameter(StringParameter):
    """ A path to a file or directory.
    A widget containing a line edit and a 'Browse...' button that
    brings up a file selection dialog represents this parameter per
    default.
    """
    def __init__(self, name, description = None,
				 defaultValue = ".", role = None):
        StringParameter.__init__(self, name, description,
            defaultValue, role)

class LayerParameter(Parameter):
    """ Base to the different types of layers available thorugh QGIS.
    """
    def __init__(self, name, pType = QgsMapLayer, description = None,
				 defaultValue = [], role = None):
        Parameter.__init__(self, name, pType, description,
            defaultValue, role)

class VectorLayerParameter(LayerParameter):
    """ A QGIS Vector layer.
    It is the backend's responsability to convert data this into the
    required format.
    By default displayed as a drop box that allows selection of a
    vector layer (or none, if one is to be created on output or the
    parameter is optional).
    """
    def __init__(self, name, description = None,
				 defaultValue = [], role = None):
        LayerParameter.__init__(self, name, QgsVectorLayer, description,
            defaultValue, role)

class RasterLayerParameter(LayerParameter):
    """  A QGIS Raster layer.
    It is the backend's responsability to convert data this into the
    required format.
    By default displayed as a drop box that allows selection of a
    raster layer (or none, if one is to be created on output or the
    parameter is optional).
    """
    def __init__(self, name, description = None,
				 defaultValue = [], role = None):
        LayerParameter.__init__(self, name, QgsRasterLayer, description,
            defaultValue, role)

Validator = QtGui.QValidator
