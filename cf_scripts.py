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


os.chdir(".spyder-py3/flask/cf")
shpfile = "shape\KMLtoShape.shp"
#%%

b4 = rio.open('static/uploads/_B04.tif')
b8 = rio.open('static/uploads/_B08.tif')

#%%

def retrieveimg(shpfile):
    data = gp.read_file(shpfile)
    boundary = data.bounds.values.tolist()


    search = Search(bbox=boundary[0], datetime='2020-05-01/2020-07-30', url='https://earth-search.aws.element84.com/v0',
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
#ndvi = ndvi.squeeze()
    print(np.shape(ndvi))

# Write the NDVI image
    meta = b4.meta
    meta.update(driver='GTiff')
    meta.update(dtype=rio.float32)

    with rio.open('NDVI.tif', 'w', **meta) as dst:
        dst.write(ndvi.astype(rio.float32))
#%%

import matplotlib as plt
fig = plt.figure()
grid = axes_grid1.AxesGrid(
fig, 111, nrows_ncols=(1, 2), axes_pad = 0.5, cbar_location = "right",
cbar_mode="each", cbar_size="15%", cbar_pad="5%",)
ndvi=ndvi.squeeze()
im0 = grid[0].imshow(ndvi, cmap='pink', interpolation='nearest')
grid.cbar_axes[0].colorbar(im0)


#%%

retrieveimg(shpfile)




