
import os
os.chdir("Documents/projects/cf_app")

#%%
import rasterio as rio
from rasterio.plot import show
from cf_scripts import readShapeFile, g_authenticate,getSentinelImages, getCollection, gen_folium
from cf_scripts import addNDVI, addNDTI, addVRESTI, addNITI, add_ee_layer
from cf_scripts import collectionMeans, getDataframe
import ee
import zipfile
import folium
import pandas as pd
import geopandas as gp
import altair as alt

#%%#%%
filepath = "shape\KMLtoShape.zip"
file = zipfile.ZipFile(filepath, 'r')

#%%
g_authenticate()
shape = readShapeFile(file)

clippedCollection = getCollection(shape)
gen_folium(clippedCollection)
df3 = getDataframe(shape, clippedCollection)
#%%
##df3 = pd.read_csv('static/uploads/data.csv')

#%%
baseNDVI = alt.Chart(df3).mark_circle(size=100).encode(x='date:T',y='NDVI:Q',
    color=alt.Color('NDVI:Q', scale=alt.Scale(scheme='pinkyellowgreen', domain=(-1, 1))),
    tooltip=[alt.Tooltip('Datetime:T', title='Date'),alt.Tooltip('NDVI:Q', title='NDVI')
    ]).properties(width=600, height=300)

baseNDTI = alt.Chart(df3).mark_circle(size=100).encode(x='date:T',y='NDTI:Q',
    color=alt.Color('NDTI:Q', scale=alt.Scale(scheme='redblue', domain=(-1, 1))),
    tooltip=[alt.Tooltip('Datetime:T', title='Date'),alt.Tooltip('NDTI:Q', title='NDTI')
    ]).properties(width=600, height=300)

ndti_comparison = alt.layer(baseNDTI, baseNDVI).resolve_scale(color='independent')

NDVIvsNDTI_histogram = alt.Chart(df3).transform_fold(['NDVI', 'NDTI'],
    as_=['Index', 'Index score']).mark_area(opacity=0.3,interpolate='step').encode(
    alt.X('Index score:Q', bin=alt.Bin(maxbins=40)),
    alt.Y('count()', stack=None),
    alt.Color('Index:N'))

display1 = alt.hconcat(ndti_comparison, NDVIvsNDTI_histogram)


display1.save('templates/altair.html')

#%%

def getDataframe(shape, clippedCollection):
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


#%%

filepath = 'test/result.shp'

gdf = gp.read_file(filepath)
gdf = gdf.iloc[[0]]
allCoordinates = []

farmBoundaries = gdf['geometry']

#%%
for b in farmBoundaries.boundary:
    middle = b.centroid.coords
    latitude = middle[0][1]
    longitude = middle[0][0]
    
    ##x,y = b.coords.xy
    ##xy = list(zip(x,y))
    ##allCoordinates.append(xy)

#%%
df3 = pd.read_csv('static/uploads/data.csv')

index_type = 'NITI'
chart_val = index_type + ':Q'
start_date = '2021-02-02'
end_date = '2021-05-29'


#%%
def gen_Charts(df3):
    baseNDVI = alt.Chart(df3).mark_circle(size=100).encode(x='date:T', y='NDVI:Q',
                color=alt.Color('NDVI:Q',scale=alt.Scale(scheme='pinkyellowgreen',domain=(-1, 1))),
                tooltip=[alt.Tooltip('Datetime:T', title='Date'),alt.Tooltip('NDVI:Q', title='NDVI')]).properties(width=600, height=300)

    baseNDTI = alt.Chart(df3).mark_circle(size=100).encode(x='date:T', y='NDTI:Q',
                color=alt.Color('NDTI:Q', scale=alt.Scale(scheme='redblue',domain=(-1, 1))),
                tooltip=[alt.Tooltip('Datetime:T', title='Date'),alt.Tooltip('NDTI:Q', title='NDTI')]).properties(width=600, height=300)

    ndti_comparison = alt.layer(baseNDTI, baseNDVI).resolve_scale(color='independent')

    NDVIvsNDTI_histogram = alt.Chart(df3).transform_fold(['NDVI', 'NDTI'],as_=['Index', 'Index score']).mark_area(opacity=0.3,
                            interpolate='step').encode(alt.X('Index score:Q', bin=alt.Bin(maxbins=40)),alt.Y('count()', stack=None),
                            alt.Color('Index:N'))

    display1 = alt.hconcat(ndti_comparison, NDVIvsNDTI_histogram)

    display1.save('templates/altair.html')




#%%
baseNDVI = alt.Chart(df3).mark_circle(size=100).encode(x='date:T', y= chart_val,
                color=alt.Color(chart_val,scale=alt.Scale(scheme='pinkyellowgreen',domain=(-1, 1))),
                tooltip=[alt.Tooltip('Datetime:T', title='Date'),alt.Tooltip(chart_val, title=index_type)]).properties(width=600, height=300)


#%%

baseNDVI.save('test.html')

#%%


aaa = pd.to_datetime(start_date, format='%Y-%m-%d')

df4 = df3[df3['date']> start_date]
    
df4 = df3[df3['date'].between(start_date, end_date)]



#%%
import glob
dir_path = 'shape/extracted_files'
files = glob.glob('shape/extracted_files')
for f in files:
    os.remove(f)

os.rmdir(dir_path)


