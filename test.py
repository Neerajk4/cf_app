
import os
os.chdir("Documents/projects/cf_app")

#%%
import rasterio as rio
from rasterio.plot import show
from cf_scripts import readShapeFile, g_authenticate,getSentinelImages
from cf_scripts import addNDVI, addNDTI, addVRESTI, addNITI, add_ee_layer
import ee
import zipfile
import folium

#%%#%%
filepath = "shape\shape_file.zip"
test = open(filepath, "r")

#%%
g_authenticate()

#%%
file_extension = os.path.splitext(filepath)[1]
if file_extension == ".zip":
   file = zipfile.ZipFile(filepath, 'r') 
   shape = readShapeFile(file)
else:
    pass

#%%
lat_dobimar = 53.701366188784476
lon_dobimar = 11.539508101477306

lat_martin = 47.88735304545457
lon_martin = 13.755339409090896
#%%
startDate = '2020-05-01'
endDate = '2021-05-01'
sentinelCollection = getSentinelImages(shape, startDate, endDate)
clippedCollection = sentinelCollection.map(lambda image: image.clip(shape))
image = sentinelCollection.limit(1, 'system:time_start', False).first()
clippedImage = clippedCollection.limit(1, 'system:time_start', False).first()
#%%

# defining and adding the various index bands to the passed image

ndviBand = addNDVI(clippedImage).select("NDVI")
ndtiBand = addNDTI(clippedImage).select('NDTI')
vrestiBand = addVRESTI(clippedImage).select("VRESTI")
nitiBand = addNITI(clippedImage).select('NITI')

#%%
visParams = {'min': 0, 'max': 1000, 'bands': ['B4', 'B3', 'B2']}
ndviParams = {min: -1, max: 1, 'palette': ['blue', 'white', 'green']}
ndtiParams = {min: 0, max: 1, 'palette': ['blue','white','yellow','brown','red']}
vrestiParams = {min: -1, max: 1, 'palette': ['white', 'blue', 'purple','white', 'red']}
nitiParams = {min: 0, max: 1, 'palette': ['yellow','white','brown']}
vretiParams = {min: -1, max: 1, 'palette': ['blue', 'white', 'green']}
rsdiParams = {min: 0, max: 1, 'palette': ['yellow','white','brown']}

#%%

# use the control button in the top right corner to visualize the different indices against the map

# adjust the location parameter according to the desired farm
map = folium.Map(location=[lat_dobimar,lon_dobimar], zoom_start=14)

folium.Map.add_ee_layer = add_ee_layer


# Add the image layer to the map and display it.
map.add_ee_layer(ndviBand, ndviParams, 'NDVI')
map.add_ee_layer(vrestiBand, vrestiParams, 'VRESTI')
map.add_ee_layer(ndtiBand, ndtiParams, 'NDTI')
map.add_ee_layer(nitiBand, nitiParams, 'NITI')

map.add_ee_layer(image, visParams, 'VIS')
map.add_child(folium.LayerControl())

#%%
map.save("templates/map2.html")







