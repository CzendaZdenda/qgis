import processing
from processing.parameters import VectorLayerParameter, NumericParameter

class BasicModule:
    def __init__(self, iface):
        # save reference to the QGIS interface
        self.iface = iface
    def unload(self):
        pass
    def modules(self):
        return [self.module]
    def initGui(self):
        inputLayerParameter = VectorLayerParameter("Input layer")
        inputLayerParameter.setRole(VectorLayerParameter.Role.input)
        self.module = processing.Module("A basic module", parameters = [inputLayerParameter])
        processing.framework.registerModuleProvider(self)
