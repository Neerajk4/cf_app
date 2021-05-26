# -*- coding: utf-8 -*-
"""
Created on Thu May 13 15:29:33 2021

@author: Neerajk4
"""
## geo libraries
import geopandas as gp
from satsearch import Search
import fiona
import rasterio as rio
from rasterio.plot import show
from rasterstats import zonal_stats
import folium
import ee

##parsing and formatting packages
import requests
from datetime import datetime

##other important libraries
import pandas as pd
import numpy as np
import os
from google.cloud import storage
import zipfile
import glob
import warnings

#%%


##os.chdir(".spyder-py3/flask/cf")
##shpfile = "shape\KMLtoShape.shp"
shpfile = "shape\Ackerpulco.kml"
#%%

##b4 = rio.open('static/uploads/_B04.tif')
##b8 = rio.open('static/uploads/_B08.tif')
##ndvi = rio.open('static/uploads/NDVI.tif')
#%%

def retrieveimg(shpfile):
    gp.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
    data = gp.read_file(shpfile, driver='KML')
    boundary = data.bounds.values.tolist()


    search = Search(bbox=boundary[0], datetime='2020-05-01/2020-12-30', url='https://earth-search.aws.element84.com/v0',
               collections=['sentinel-s2-l2a-cogs'],query={'eo:cloud_cover': {'lt': 1}})

    items = search.items() 

    data = list()
    chunks = items.summary().split('\n')
    chunks = chunks[2:]
    for chunk in chunks:
        data.append(chunk.split())

    df = pd.DataFrame(data, columns = ['date', 'id'])
    df.reset_index(inplace=True)
    df = df.sort_values(by='date', ascending=False)
    id1 = df.index[0]
    item = items[id1]

    item.download('B04', filename_template='static/uploads/')
    item.download('B08', filename_template='static/uploads/')


#%%
def ndvicalc(b4, b8):
# read Red(b4) and NIR(b8) as arrays
    red = b4.read()
    nir = b8.read()


# Calculate ndvi
    ndvi = (nir.astype(float)-red.astype(float))/(nir+red)

# Write the NDVI image
    meta = b4.meta
    meta.update(driver='GTiff')
    meta.update(dtype=rio.float32)

    with rio.open('static/uploads/NDVI.tif', 'w', **meta) as dst:
        dst.write(ndvi.astype(rio.float32))
        
    with rio.open('static/uploads/test.jpg', 'w', **meta) as dst:
        dst.write(ndvi.astype(rio.float32))
        
#%%
def resizeimg(dataset):
    from rasterio.enums import Resampling
    upscale_factor = .01

    ##with rio.open("static/uploads/NDVI.tif") as dataset:
        # resample data to target shape
    data = dataset.read(out_shape=(dataset.count,int(dataset.height * upscale_factor),
    int(dataset.width * upscale_factor)), resampling=Resampling.bilinear)
        
    with rio.open('static/uploads/resample.jpg', 'w', driver='GTiff', height=data.shape[1], width = data.shape[2], count = 1, dtype=rio.float32) as dst:
        dst.write(data.astype(rio.float32))


def testfunction():
    return "Hello"

def upload_to_bucket(blob_name, file_path, bucket_name):
    try:
        fp = os.path.abspath("C:/Users/Neerajk4/Documents/projects/project2-297804-93907eda4ec1.json")
        storage_client = storage.Client.from_service_account_json(fp)
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_path)
        return True
    except Exception as e:
        print(e)
        return False

def readShapeFile(file):
    file.extractall("shape/extracted_files")
    
    ## gets new filepath
    for name in glob.glob('shape/extracted_files/*.shp'):
        filepath_new = name
        
    gdf = gp.read_file(filepath_new)
    gdf = gdf.iloc[[0]]

    farmBoundaries = gdf['geometry']
    warnMessage = "warning message for points"
    allCoordinates = []
    for b in farmBoundaries.boundary:

        if b.geom_type == 'Point' or b.geom_type == 'MultiPoint':
            warnings.warn(warnMessage)
      
        elif b.geom_type == 'MultiLineString':
            for geom in range(len(b.geoms)):
        # extract the x and y coordinates and form a list of tuples [(x-coord, y-coord)]
                x,y = b[geom].coords.xy
                xy = list(zip(x,y))
                allCoordinates.append(xy)
        else:
            x,y = b.coords.xy
            xy = list(zip(x,y))
            allCoordinates.append(xy) 

    return ee.Geometry.Polygon(allCoordinates)


def g_authenticate():
    service_account = " cf-cloud@project2-297804.iam.gserviceaccount.com"
##service_account = 'my-service-account@...gserviceaccount.com'
    json_file = "../project2-297804-93907eda4ec1.json"
    credentials = ee.ServiceAccountCredentials(service_account, json_file)
    ee.Initialize(credentials)

def getSentinelImages(roi: ee.geometry.Geometry, startDate: str, endDate: str, **kwargs) -> ee.ImageCollection:
  '''
  startDate and endDate must be in the form "YYYY-MM-DD"

  The current state of the function will only return images in which less than 20% of pixels
  are labeled as cloudy pixels.
  '''
  return ee.ImageCollection('COPERNICUS/S2_SR').filterBounds(roi).filterDate(startDate, endDate)\
.filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 20))

def addNDVI(image: ee.image.Image) -> ee.image.Image:
  ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI');
  return image.addBands(ndvi)

def addNDTI(image: ee.image.Image) -> ee.image.Image:
  ndti = image.normalizedDifference(['B11', 'B12']).rename('NDTI')
  return image.addBands(ndti)

def addVRESTI(image: ee.image.Image) -> ee.image.Image:
  vresti = image.normalizedDifference(['B7', 'B12']).rename('VRESTI')
  return image.addBands(vresti)

def addNITI(image: ee.image.Image) -> ee.image.Image:
  niti = image.normalizedDifference(['B8A', 'B12']).rename('NITI')
  return image.addBands(niti)

def addVRETI(image: ee.image.Image) -> ee.image.Image:
  vreti = image.normalizedDifference(['B6', 'B12']).rename('VRETI')
  return image.addBands(vreti)

def addRSDI(image: ee.image.Image) -> ee.image.Image:
  rsdi = image.normalizedDifference(['B5', 'B12']).rename('RSDI')
  return image.addBands(rsdi)

# Define a method for displaying Earth Engine image tiles to folium map.
def add_ee_layer(self, ee_image_object, vis_params, name):
  map_id_dict = ee.Image(ee_image_object).getMapId(vis_params)
  folium.raster_layers.TileLayer(
    tiles = map_id_dict['tile_fetcher'].url_format,
    attr = "Map Data © Google Earth Engine",
    name = name,
    overlay = True,
    control = True
  ).add_to(self)

def gen_folium(shape):
    lat_dobimar = 53.701366188784476
    lon_dobimar = 11.539508101477306
    startDate = '2020-05-01'
    endDate = '2021-05-01'
    sentinelCollection = getSentinelImages(shape, startDate, endDate)
    clippedCollection = sentinelCollection.map(lambda image: image.clip(shape))
    clippedImage = clippedCollection.limit(1, 'system:time_start', False).first()

    ndviBand = addNDVI(clippedImage).select("NDVI")
    ndtiBand = addNDTI(clippedImage).select('NDTI')
    vrestiBand = addVRESTI(clippedImage).select("VRESTI")
    nitiBand = addNITI(clippedImage).select('NITI')

    visParams = {'min': 0, 'max': 1000, 'bands': ['B4', 'B3', 'B2']}
    ndviParams = {min: -1, max: 1, 'palette': ['blue', 'white', 'green']}
    ndtiParams = {min: 0, max: 1, 'palette': ['blue', 'white', 'yellow', 'brown', 'red']}
    vrestiParams = {min: -1, max: 1, 'palette': ['white', 'blue', 'purple', 'white', 'red']}
    nitiParams = {min: 0, max: 1, 'palette': ['yellow', 'white', 'brown']}
    vretiParams = {min: -1, max: 1, 'palette': ['blue', 'white', 'green']}
    rsdiParams = {min: 0, max: 1, 'palette': ['yellow', 'white', 'brown']}
    map = folium.Map(location=[lat_dobimar,lon_dobimar], zoom_start=14)

    folium.Map.add_ee_layer = add_ee_layer

    # Add the image layer to the map and display it.
    map.add_ee_layer(ndviBand, ndviParams, 'NDVI')
    map.add_ee_layer(vrestiBand, vrestiParams, 'VRESTI')
    map.add_ee_layer(ndtiBand, ndtiParams, 'NDTI')
    map.add_ee_layer(nitiBand, nitiParams, 'NITI')

    map.add_ee_layer(clippedImage, visParams, 'VIS')
    map.add_child(folium.LayerControl())

    # %%
    map.save("templates/map.html")