# -*- coding: utf-8 -*-
# aboutdialog.py
# modified from DockableMirrorMap's DlgAbout.py


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ui_aboutdialog import Ui_aboutDialog
from processingplugin import name, description, version
import platform

class AboutDialog(QDialog, Ui_aboutDialog):

	def __init__(self, parent=None):
		QDialog.__init__(self, parent)
		self.setupUi(self)
		self.logo.setPixmap(QPixmap("processing.png"))
