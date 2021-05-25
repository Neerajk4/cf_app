# -*- coding: utf-8 -*-
"""
Created on Thu May 13 15:29:33 2021

@author: Neerajk4
"""
import requests
import fiona
import geopandas as gp
from satsearch import Search
import rasterio as rio
from rasterio.plot import show

#Used to generate zonal statistics from the union between polygons and raster data
from rasterstats import zonal_stats
from datetime import datetime
import pandas as pd
import numpy as np
import os
from google.cloud import storage
import zipfile
import glob
import warnings
import ee
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
    gdf = gdf.iloc[[4]]

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


