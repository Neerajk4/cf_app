
import rasterio as rio
from rasterio.plot import show
from cf_scripts import retrieveimg, nvdicalc, resizeimg, testfunction

shpfile = "shape\Ackerpulco.kml"
retrieveimg(shpfile)
aaa = testfunction()
b4 = rio.open('static/uploads/_B04.tif')
b8 = rio.open('static/uploads/_B08.tif')
nvdicalc(b4, b8)
ndvi = rio.open('static/uploads/NDVI.tif')
resizeimg(ndvi)
print(aaa)