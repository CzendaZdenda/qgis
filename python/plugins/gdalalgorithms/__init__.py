def name():
    return "GDAL algorithms demo"
def description():
    return "Makes a GDAL algorithm available through the processing framework."
def version():
    return "Version 0.1"
def qgisMinimumVersion(): 
    return "1.0"
def authorName():
    return "Camilo Polymeris"
def classFactory(iface):
    import gdalalgorithms
    return gdalalgorithms.Plugin(iface)

