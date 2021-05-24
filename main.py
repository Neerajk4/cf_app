import os
from app import app
import urllib.request
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from cf_scripts import retrieveimg, ndvicalc, resizeimg, testfunction
import rasterio as rio
import time

ALLOWED_EXTENSIONS = set(['kml', 'shp'])

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
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			shpfile = os.path.join("shape", filename)
			retrieveimg(shpfile)
			time.sleep(10)
			b4 = rio.open('static/uploads/_B04.tif')
			b8 = rio.open('static/uploads/_B08.tif')
			ndvicalc(b4, b8)
			time.sleep(10)
			ndvi = rio.open('static/uploads/NDVI.tif')
			resizeimg(ndvi)
			filename2 = 'static/uploads/resample.jpg'
			#print('upload_image filename: ' + filename)
			flash('Shape File successfully uploaded')
			return render_template('upload.html', filename = filename2)
		else:
			flash('Allowed image types are -> png, jpg, jpeg, gif')
			return redirect(request.url)
	else:
		return render_template('upload.html')

@app.route('/display/<filename>')
def display_image(filename):
	#print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route('/stats')
def stats_render():
    return render_template('stats.html')


if __name__ == "__main__":
    app.run()