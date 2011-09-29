import processing
from processing.parameters import *

from PyQt4.QtCore import QObject

from osgeo import gdal

class Plugin:
    def __init__(self, iface):
        # save reference to the QGIS interface
        self.iface = iface
    def unload(self):
        pass
    def modules(self):
        return [self.contourModule]
    def initGui(self):
        self.contourModule = ContourModule()
        processing.framework.registerModuleProvider(self)

class ContourModule(processing.Module):
    def __init__(self):
        self.inParam = RasterLayerParameter("Input raster")
        self.inParam.setRole(Parameter.Role.input)
        self.outParam = VectorLayerParameter("Output layer")
        self.outParam.setRole(Parameter.Role.output)
        processing.Module.__init__(self, "Contour", 
            description = "GDAL demo module",
            parameters = [self.inParam, self.outParam], tags = ["gdal"])
    def instance(self):
        return ContourModuleInstance(self, self.inParam, self.outParam)
		
class ContourModuleInstance(processing.ModuleInstance):
    def __init__(self, module, inParam, outParam):
        self.inParam = inParam
        self.outParam = outParam
        processing.ModuleInstance.__init__(self, module)
        QObject.connect(self,
            self.valueChangedSignal(self.stateParameter),
            self.onStateParameterChanged)
    def onStateParameterChanged(self, state):
        if state == StateParameter.State.running:
            inLayer = self[self.inParam]
            outLayer = self[self.outParam]
            self.contour(inLayer, outLayer)
            self.setState(StateParameter.State.stopped)
    def contour(self, inLayer, outLayer):
        ds = 
        ogr_ds = ogr.GetDriverByName('ESRI Shapefile').CreateDataSource('tmp/contour.shp')
        ogr_lyr = ogr_ds.CreateLayer('contour')
        field_defn = ogr.FieldDefn('ID', ogr.OFTInteger)
        ogr_lyr.CreateField(field_defn)
        field_defn = ogr.FieldDefn('elev', ogr.OFTReal)
        ogr_lyr.CreateField(field_defn)

        gdal.ContourGenerate(ds.GetRasterBand(1), 10, 0, [], 0, 0, ogr_lyr, 0, 1)

        ds = None
