def name():
    return "Most basic module"
def description():
    return "This module has only didactic use."
def version():
    return "Version 0.1"
def qgisMinimumVersion(): 
    return "1.0"
def authorName():
    return "Developer"
def classFactory(iface):
    from basicmodule import BasicModule
    return BasicModule(iface)

