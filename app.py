# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 10:36:49 2022
This is the flask file that runs the application. It can be called from the terminal using "flask run" 
@author: 10853401
"""

#importing all required libraries
import sqlite3 #importing sqplite which is our database
from json import dumps #importing dumps to send json to the client
import geopandas as gpd #importing geopandas as gpd to use in clippingalgorithm3
from werkzeug.exceptions import BadRequestKeyError #for handling bad requests
from flask import Flask, render_template, request, g #importing flask, render template, request and g
from clippingalgorithm import floodfillalgorithm #calling the flood fill algorithm from clippingalgorithm3
from validationalgorithm import validationaglorithm
import matplotlib #importing matplotlib to export and save the image
matplotlib.use('Agg') #directing matplotlib to run on the backend and not the front end 
import matplotlib.pyplot as plt #importing plot 
from shapely.geometry import Point , mapping, Polygon, LineString #importing point and mapping to add input points and convert geoseries to geojson
from rasterio.mask import mask #importing mask to mask the DEM layer
from rasterio import open as rio_open #importing open to open Digital Elevation Models
from math import floor, ceil #importing floor and ceil to use in the flood fill algorithm
from numpy import zeros, linspace  #importing use in the flood fill algorithm
from matplotlib.colors import Normalize #importing normalise for color scheme 
from rasterio.plot import show as rio_show #importing show to add the raster to matplotlib
from matplotlib.colors import LinearSegmentedColormap #imported for coloring the output map 
from matplotlib.pyplot import subplots, savefig, get_cmap # importing for geting colormap, saving figure and using subplots
import sys #imported to open the image 
import io #imported to convert png image to bit64
from base64 import encodebytes #imported to encode image as bit64 
from PIL import Image #importing the Image module from Pillow
from flask import jsonify #converting output to json to dump to client
import datetime


#instantiating Flask by assigning app to class __name

app = Flask(__name__)

# set the path to the database
DATABASE = './VGIdata.db'

#defining some helper connections to reach and connect with the database test.db

def get_db():
    '''
    * This is a helper function to connect to database VGIdata.db
    '''
    # see if the database connnection exists
    db = getattr(g, '_database', None)
    
    # if not, connect
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    # set it to return data as `Row` objects
    db.row_factory = sqlite3.Row

    # return the database connection 
    return db

@app.teardown_appcontext
def close_connection(exception):
    '''
    * This is a helper function to close the current database connection (VGIdata.db)
    '''
    # see if a database connection exists
    db = getattr(g, '_database', None)
    
    # if so, close it
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    '''
    * This is a helper function to query the current database connection (VGIdata.db)
    '''
    # open a database cursor and execute the query
    cur = get_db().execute(query, args)
    
    # fetch all results
    rv = cur.fetchall()
    
    # close the cursor
    cur.close()

    # return the results
    return (rv[0] if rv else None) if one else rv


def insert_db(query, args=()):
    '''
    * This is a helper function to query the current database connection (VGIdata.db)
    '''
    # get ref to the database
    db = get_db()
    
    # open a database cursor and execute the query
    cur = db.execute(query, args)
    
    # commit the changes
    db.commit()
    
    # close the cursor
    cur.close()

    # return the results
    return cur.lastrowid

def last_db(query, args=()):
    '''
    * This is a helper function to query the current database connection (VGIdata.db)
    '''
    # get ref to the database
    db = get_db()
    
    # open a database cursor and execute the query
    cur = db.execute(query, args)
    
    # commit the changes
    db.commit()
    
    # close the cursor
    cur.close()

    # return the results
    return cur.lastrowid

def get_response_image(image_path):
    '''
    * This is a function that returns the flood fill image as a base64 string. It takes the image path (out/floodfill.png) as input
    '''
    pil_img = Image.open(image_path, mode='r') # reads the PIL image
    byte_arr = io.BytesIO() #creating a byte array
    pil_img.save(byte_arr, format='PNG') # convert the PIL image to byte array
    encoded_img = encodebytes(byte_arr.getvalue()).decode('ascii') # encode as base64
    return encoded_img #returns image encoded in base64

#############################################################################defining app routes #################################################

#route select all selects all entries in the database and returns all values 
@app.route("/selectall")
def select_all():
    '''
    * This flask route returns all entries in the database to the user interface
    *

    '''
    
    # output all of the rows in the database to a dictionary output containing all the lat and longs
    output = []

    #querying all rows using the query_db function
    for row in query_db('select * from locations'):
        
        #querying lat, long, description and date / time submitted
        output.append({'lng': row['lng'], 'lat': row['lat'], 'description': row['description'], 'time_submitted' : row['DATETIME']})
    
    # dump all input points(rows) to JSON and return
    return dumps(output)


@app.route("/select")
def select_one():
    '''
    * This is the flask route that lets users check details of submitted VGI points
    *
    * An example call to this service would be:
    *   http://127.0.0.1:5000/select?lng=-2.807007&lat=54.065836
    '''
    # only works if both lng and lat have been passed and can be converted to floats
    try:

        #getting input from the user
        lng = float(request.args['lng'])
        lat = float(request.args['lat'])

        #checking for exception if the values entered are not float
    except (BadRequestKeyError, ValueError):
        return dumps({'success': False})

    # query the database for a single row with values lat and long 
    row = query_db('select * from locations where lat = ? and lng = ?', [lat, lng], one=True)
    #if the values are not in the database return dumps of success: False
    if row is None:
            return dumps({'success': False})
    else:
            #if the values are valid get the buffer of the clipped raster calling the callingclip function in clippingalgorithm3 
            #the function takes lat and long as input and creates the flood fill 
            bufferforimage =floodfillalgorithm(lat, lng, 1)

            #once the function is done setting imagepath to the newest version of the png file        
            image_path = 'out/floodfill.png' 

            #calling the get_response_image function with the image_path as an argument to get the base64string of the Png Image
            #assigning it to a string so it can be merged with its datastructure 
            encoded_img = str(get_response_image(image_path))

            #creating a variable called frontofpng that specifies the data type and image type          
            frontofpng = "data:image/png;base64,"

             #using F Strings to merge frontofpng and encoded_img
            imgstringtosend = f"{frontofpng}{encoded_img}"

            validationreturn = validationaglorithm(lat, lng)
            print(validationreturn)
            listformarker =[lat,lng]
            #creating a dictionary with two variables - geojson and image         
            dictionary = {
                "geojson": mapping(bufferforimage), #creating an object in the dictionary corresponding to the geojson of the clipped raster
                "image" : imgstringtosend, #creating an object in the dictionary corresponding to the image in byte64 format
                'validationlist' : ' '.join(validationreturn),
                'markerpoint' : listformarker
            }
            #converting the dictionary to a json
            jsondict = jsonify(dictionary)
            #returning it to the user 
            return jsondict



@app.route("/insert")
def insert():


    """
    * This flask route that inserts new data into the database and returns a flood fill algorithm and flood history of the area
    """

    # only works if both lng and lat have been passed and can be converted to floats
    try:
        #getting input from the user
        lng = float(request.args['lng'])
        lat = float(request.args['lat'])
        floodhazard = request.args['flood depth'] 
        description = request.args['description']
    except (BadRequestKeyError, ValueError):
        return dumps({'success': False})

    # insert the data into the database
    datetime_object = datetime.datetime.now()
    datetime_object_str = str(datetime_object)
    rowid = insert_db('insert into locations values (?, ?, ?, ?, ?)',[lat, lng,floodhazard,description,datetime_object_str])


    # respond the user (encoded as JSON)
    if rowid is None:
        return dumps({'success': False})
    else:

    #if the values are valid get the buffer of the clipped raster calling the floodfillalgorithm function in clippingalgorithm3 
    #the function takes lat and long as input and creates the flood fill 
            bufferforimage =floodfillalgorithm(lat, lng, floodhazard)

    #once the function is done setting imagepath to the newest version of the png file        
            image_path = 'out/floodfill.png' 

    #calling the get_response_image function with the image_path as an argument to get the base64string of the Png Image
    #assigning it to a string so it can be merged with its datastructure 
            encoded_img = str(get_response_image(image_path))

    #creating a variable called frontofpng that specifies the data type and image type          
            frontofpng = "data:image/png;base64,"

    #using F Strings to merge frontofpng and encoded_img
            imgstringtosend = f"{frontofpng}{encoded_img}"

    #calling the validation algorithm
            validationreturn = validationaglorithm(lat, lng)

    #creating a dictionary with three variables - geojson and image and validation list       
            dictionary = {
                "geojson": mapping(bufferforimage), #creating an object in the dictionary corresponding to the geojson of the clipped raster
                "image" : imgstringtosend, #creating an object in the dictionary corresponding to the image in byte64 format
                'validationlist' : ' '.join(validationreturn)
            }
            #converting the dictionary to a json
            jsondict = jsonify(dictionary)
            #returning it to the user 
            return jsondict
   

@app.route("/")


#this is the route to the english html map 
@app.route("/map")
def map():

# this flask route uses render template to call the map html file 
    return render_template('./map.html')

#this is the route to the tamil html map 

@app.route("/tamil")
def tamil():
#using render template to call the tamil html file 

    return render_template('./tamil.html')
    




