import os
from app import app
import urllib.request
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from cf_scripts import retrieveimg, nvdicalc, resizeimg, testfunction
import rasterio as rio

ALLOWED_EXTENSIONS = set(['kml', 'shp'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
@app.route('/')
def upload_form():
	return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_image():
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
		b4 = rio.open('static/uploads/_B04.tif')
		b8 = rio.open('static/uploads/_B08.tif')
		nvdicalc(b4, b8)
		ndvi = rio.open('static/uploads/NDVI.tif')
		resizeimg(ndvi)
		filename2 = 'static/uploads/resample.jpg'
		#print('upload_image filename: ' + filename)
		flash('Image successfully uploaded and displayed below')
		return render_template('upload.html', filename=filename2)
	else:
		flash('Allowed image types are -> png, jpg, jpeg, gif')
		return redirect(request.url)

@app.route('/display/<filename>')
def display_image(filename):
	#print('display_image filename: ' + filename)
	return redirect(url_for('static', filename='uploads/' + filename), code=301)

if __name__ == "__main__":
    app.run()