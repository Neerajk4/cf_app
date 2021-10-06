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
import altair as alt
import os
from google.cloud import storage
import zipfile
import glob
import warnings
from celery import Celery
celery = Celery('example')
celery.conf.update(BROKER_URL=os.environ['REDIS_URL'],CELERY_RESULT_BACKEND=os.environ['REDIS_URL'])

def deleteFolder():
    dir_path = 'shape/extracted_files'
    files = glob.glob(os.path.join(dir_path, "*"))
    for f in files:
        os.remove(f)
    os.rmdir(dir_path)

def readShapeFile(file: zipfile.ZipFile) -> ee.geometry.Geometry:
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
            middle = b.centroid.coords
            latitude = middle[0][1]
            longitude = middle[0][0]
            x,y = b.coords.xy
            xy = list(zip(x,y))
            allCoordinates.append(xy) 

    return ee.Geometry.Polygon(allCoordinates)


def g_authenticate():
    service_account = " cf-cloud@project2-297804.iam.gserviceaccount.com"
    json_file = "google-credentials.json"
    ##json_file = os.environ['gkey1']
    ##json_file = os.environ['gkey2']
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

def getCollection(shape: ee.geometry.Geometry) -> ee.imagecollection.ImageCollection:
    startDate = '2020-05-01'
    endDate = '2021-05-01'
    sentinelCollection = getSentinelImages(shape, startDate, endDate)
    clippedCollection = sentinelCollection.map(lambda image: image.clip(shape))
    return clippedCollection

def gen_folium(clippedCollection: ee.imagecollection.ImageCollection, latitude: str, longitude: str):
    latitude = float(latitude)
    longitude = float(longitude)
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
    map = folium.Map(location=[latitude,longitude], zoom_start=14)

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

def collectionMeans(image: ee.image.Image, index: str, geometry: ee.geometry.Geometry) -> ee.ImageCollection:
  # Compute the mean of the passed index over the passed image
  # the value is a dictionary, so get the index value from the dictionary
  value = image.reduceRegion(**{'geometry': geometry,'reducer': ee.Reducer.mean(),
  }).get(index)

  # Adding computed index value
  newFeature = ee.Feature(None, {index : value
  }).copyProperties(image, ['system:time_start','SUN_ELEVATION'])
  return newFeature

def getDataframe(shape:ee.geometry.Geometry, clippedCollection: ee.imagecollection.ImageCollection) -> pd.core.frame.DataFrame:
    it_dict = {"NDVI": addNDVI, "NDTI": addNDTI, "VRESTI": addVRESTI, "NITI": addNITI}
    dict_values = {"date": [], "NDVI": [], "NDTI": [], "VRESTI": [], "NITI": []}

    for key, value_func in it_dict.items():
        print(key, value_func)
        collection2 = clippedCollection.map(lambda clippedImage: value_func(clippedImage)).select(key)
        meanscollection2 = collection2.map(lambda clippedImage: collectionMeans(clippedImage, key, shape))

        for i in range(len(meanscollection2.getInfo()['features'])):
            dict_values[key].append(meanscollection2.getInfo()['features'][i]['properties'][key])
            if key == "NDVI":
                dict_values["date"].append(meanscollection2.getInfo()['features'][i]['properties']['system:time_start'])

    df3 = pd.DataFrame(dict_values)
    df3['date'] = pd.to_datetime(df3['date'], unit='ms')
    df3['date'] = df3['date'].dt.strftime('%Y-%m-%d')
    df3.to_csv("static/uploads/data.csv", index=False)
    return df3

def gen_Charts(df3: pd.core.frame.DataFrame, index_type: str, start_date: datetime, end_date: datetime):
    df4 = df3[df3['date'].between(start_date, end_date)]
    chart_val = index_type + ':Q'

    basechart = alt.Chart(df4).mark_circle(size=100).encode(x='date:T', y=chart_val,color=alt.Color(chart_val,
                    scale=alt.Scale(scheme='pinkyellowgreen',domain=(-1, 1))),tooltip=[alt.Tooltip('Datetime:T', title='Date'),
                    alt.Tooltip(chart_val,title=index_type)]).properties(width=600, height=300)

    basechart.save('templates/altair.html')



@celery.task
def long_task(filepath, latitude, longitude):
    file = zipfile.ZipFile(filepath, 'r')
    shape = readShapeFile(file)
    clippedCollection = getCollection(shape)
    gen_folium(clippedCollection, latitude, longitude)
    df3 = getDataframe(shape, clippedCollection)
    gen_Charts(df3, 'NDVI', '2020-05-01', '2021-05-01')

    ##baseNDTI = alt.Chart(df3).mark_circle(size=100).encode(x='date:T', y='NDTI:Q',
                ##color=alt.Color('NDTI:Q', scale=alt.Scale(scheme='redblue',domain=(-1, 1))),
                ##tooltip=[alt.Tooltip('Datetime:T', title='Date'),alt.Tooltip('NDTI:Q', title='NDTI')]).properties(width=600, height=300)

    ##ndti_comparison = alt.layer(baseNDTI, baseNDVI).resolve_scale(color='independent')

    ##NDVIvsNDTI_histogram = alt.Chart(df3).transform_fold(['NDVI', 'NDTI'],as_=['Index', 'Index score']).mark_area(opacity=0.3,
                            ##interpolate='step').encode(alt.X('Index score:Q', bin=alt.Bin(maxbins=40)),alt.Y('count()', stack=None),
                            ##alt.Color('Index:N'))

    ##display1 = alt.hconcat(ndti_comparison, NDVIvsNDTI_histogram)

    ##display1.save('templates/altair.html')
