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
def nvdicalc(b4, b8):

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
    upscale_factor = .25

    ##with rio.open("static/uploads/NDVI.tif") as dataset:
        # resample data to target shape
    data = dataset.read(out_shape=(dataset.count,int(dataset.height * upscale_factor),
    int(dataset.width * upscale_factor)), resampling=Resampling.bilinear)
        
    with rio.open('static/uploads/resample.jpg', 'w', driver='GTiff', height=data.shape[1], width = data.shape[2], count = 1, dtype=rio.float32) as dst:
        dst.write(data.astype(rio.float32))


def testfunction():
    return "Hello"
#%%
##from PIL import Image
##import PIL


##image = Image.open('static/uploads/sample.jpg')
##base_width = 360
##width_percent = (base_width / float(image.size[0]))
##hsize = int((float(image.size[1]) * float(width_percent)))
##image2 = image.resize((base_width, hsize), PIL.Image.ANTIALIAS)
##image2 = image2.convert('RGB')
##image2.save('resized_compressed_image.jpg')

#%%

##import matplotlib.pyplot as plt
##fig = plt.figure()
##grid = axes_grid1.AxesGrid(
##fig, 111, nrows_ncols=(1, 2), axes_pad = 0.5, cbar_location = "right",
##cbar_mode="each", cbar_size="15%", cbar_pad="5%",)
##ndvi=ndvi.squeeze()
##im0 = grid[0].imshow(ndvi, cmap='pink', interpolation='nearest')
##grid.cbar_axes[0].colorbar(im0)


#%%

##retrieveimg(shpfile)
#%%
##nvdicalc(b4, b8)
##resizeimg(ndvi)
#%%
##from rasterio.enums import Resampling
##upscale_factor = .25

##with rio.open("static/uploads/ndvi.tif") as dataset:

    # resample data to target shape
    ##data = dataset.read(out_shape=(dataset.count,int(dataset.height * upscale_factor),
    ##int(dataset.width * upscale_factor)), resampling=Resampling.bilinear)
    
    
#%%
    # scale image transform
##transform = dataset.transform * dataset.transform.scale((dataset.width / data.shape[-1]),
##(dataset.height / data.shape[-2]))




