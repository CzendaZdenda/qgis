# -*- coding: utf-8 -*-

#	QGIS Processing Framework
#
#	moduleinstance.py (C) Camilo Polymeris
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
import PyQt4.QtCore as QtCore
from parameters import StateParameter, FeedbackParameter

class ModuleInstance(QtCore.QObject):
    """ Represents a single setup and execution of a module.
    """
    def __init__(self, module):
        """ Module.instance() calls this constructor.
        If you need to provide custom functionality, you can instantiate
        a derived class there.
        TODO: that's a very unelegant way to do this. Correct.
        """
        QtCore.QObject.__init__(self)
        self._module = module
        self._parameters = None
        self.value = self.__getitem__
        self.setValue = self.__setitem__
        self.stateParameter = StateParameter()
        self.feedbackParameter = FeedbackParameter()
        self.progressParameter = FeedbackParameter("Progress", int)
    def module(self):
        return self._module
    def parameters(self):
        """ Returns a dict of parameters to (default) values.
        """
        if self._parameters is None:
            p = [(p, p.defaultValue()) for p in
                self.module().parameters()]
            p += [(self.stateParameter, StateParameter.State.stopped),
                (self.feedbackParameter, None),
                (self.progressParameter, None)]
            self._parameters = dict(p)
        return self._parameters
    def feedback(self):
        return self[self.feedbackParameter]
    def setFeedback(self, fb = None, critical = False, progress = None):
        if fb != self.feedback():
            self[self.feedbackParameter] = fb
        if critical:
            self.setState(StateParameter.State.stopped)
        self[self.progressParameter] = progress
    def state(self):
        return self[self.stateParameter]
    def setState(self, state):
        self[self.stateParameter] = state
    def __getitem__(self, key):
        return self.parameters()[key]
    def __setitem__(self, key, value):
        validator = key.validator()
        #if validator is not None:
        #    state, _ = validator.validate(QtCore.QString(value), 0)
        #    if state != QtGui.QValidator.Acceptable:
        #        return
        self.emit(self.valueChangedSignal(key), value)
        self._parameters[key] = value
    def valueChangedSignal(self, param = None):
        """ Returns the signal emited when a parameter's value changes.
        (Doesn't emit it)
        The value is passed to the slot, not so the parameter.
        If no parameter is specified, a "parametersChanged" signal is
        returned which should be emitted when the parameter structure
        changes, e.g. parameters are added, renamed or removed.
        """
        if param is None:
            return QtCore.SIGNAL("parametersChanged")
        return QtCore.SIGNAL("valueChanged%s" % id(param))
