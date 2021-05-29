import os
from os import path
from app import app
import urllib.request
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from cf_scripts import readShapeFile, g_authenticate,getSentinelImages, getCollection, gen_folium, getDataframe, gen_Charts
import zipfile
import folium
import rasterio as rio
import pandas as pd
import time

ALLOWED_EXTENSIONS = set(['kml', 'shp', 'zip'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods = ['GET', 'POST'])
def upload_form():
	return render_template('upload.html')

@app.route('/uploader',methods = ['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No image selected for uploading')
            return redirect(request.url)

        ##if file and allowed_file(file.filename):
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filepath = os.path.join("shape", filename)
            g_authenticate()
            file_extension = os.path.splitext(filepath)[1]
            if file_extension == ".zip":
                file = zipfile.ZipFile(filepath, 'r')
                shape = readShapeFile(file)
                clippedCollection = getCollection(shape)
                gen_folium(clippedCollection)
                df3 = getDataframe(shape, clippedCollection)
                gen_Charts(df3)

            else:
                pass

            filename2 = 'static/uploads/sample.jpg'
            # print('upload_image filename: ' + filename)
            flash('Shape File successfully uploaded')
            return render_template('upload.html', filename=filename2)
        else:
            flash('Allowed image types are -> png, jpg, jpeg, gif')
            return redirect(request.url)
    else:
        return render_template('upload.html')

@app.route('/display/<filename>')
def display_image(filename):
	#print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route('/mappage')
def get_map():
    file_exist = path.exists("shape/extracted_files")
    return render_template('mappage.html', file_exist = file_exist)

@app.route('/stats')
def stats_render():
    file_exist = path.exists("shape/extracted_files")
    return render_template('stats.html', file_exist = file_exist)


if __name__ == "__main__":
    app.run()