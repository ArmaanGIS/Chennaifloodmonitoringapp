# -*- coding: utf-8 -*-

"""
Created on Fri Jul  1 10:36:49 2022
This is a wrapper function for the validation algorithm algorithm 
@author: 10853401
"""

from rasterio import open as rio_open #importing open to open Digital Elevation Models
from rasterio.mask import mask #importing mask to mask the DEM layer
from geopandas import GeoSeries, clip #importing geoseries and clip to clip the raster
from shapely.geometry import Point #importing shapely geometry
from shapely.geometry import Polygon 
from shapely.geometry import LineString
from shapely.geometry import box

def validationaglorithm(latcoord1, longcoord1):

    """
    writing all the code within a larger function validationalgorithm to be called within the flask application.
    This function takes the lat and long of the VGI input point, checking if a 200m area around contains satellite 
    flooding data from the 2015 and 2021 floods. 
    This function checks NDWI and SAR data of the 2015 and 2021 floods
    """
    LOCATION = (latcoord1,longcoord1) #converting lat and long of input point to tuple
    pointtobuffer = GeoSeries(Point((LOCATION[1], LOCATION[0]))) #creating a geoseries with point geometry
    buf = pointtobuffer.buffer(0.001, cap_style=3) #creating a 200m buffer around point geometry

    #function validatefloodfill checks if the area around the point was previously flooded by taking the buffer as input
    def validatefloodfill(buf):
        
        #creating an empty list validation list to hold strings of values if the buffer contains previously flooded area.
        validationlist = []

        #appending a thank you message to the user.
        validationlist.append("Thank you for contributing to this project by reporting flooded areas.Please note that flooding here is not indicative of actual flooding and actual flood risk. It is a very simple algorithm that determines flooding using a Digital Elevation Model (DEM). ")

        #opening flooded areas identified within NDWI satellite data of 2015 floods
        with rio_open("validationdata/Con_outputndwi2021.tif") as dem:  # 50m resolution
                #croping the dem using the buffer created around the user input point using rasterio.mask. 
                #Setting crop as true to crop the DEM 
                out_image, out_transform = mask(dem, buf, crop = True)  

                #checking if the cropped raster contains the value 1 (denoting flooded area)
                if (1 in out_image) == True:

                #if the clipped raster contains flooding, add a response to the user
                    validationlist.append('A survey of NDWI (Normalised Difference Wetness Index) data suggests that your area was flooded during the 2021 floods.')
                dem.close()


        #opening flooded areas identified within NDWI satellite data of 2021 floods
        with rio_open("validationdata/Con_outputndwi2015.tif") as dem1:  # 50m resolution
                #cropping the dem using the buffer created around the user input point using rasterio.mask. 
                #Setting crop as true to crop the DEM 
                out_image1, out_transform1 = mask(dem1, buf, crop = True)

                #checking if the cropped raster contains the value 1 (denoting flooded area)
                if (1 in out_image1) == True:

                #if the clipped raster contains flooding, add a response to the user                  
                    validationlist.append('A survey of NDWI (Normalised Difference Wetness Index) data suggests that your area was flooded during the 2015 floods. ')
                dem1.close()

                
        #opening flooded areas identified within SAR satellite data of 2021 floods
        #opening the flooded areas in the top of Chennai (North)
        with rio_open("validationdata/2021topcon.tif") as dem2:  # 50m resolution

                #creating bounds of dem to check if user input is in north or south chennai
                dem2bounds = dem2.bounds
                geom = GeoSeries(box(*dem2bounds))

                #checking if buffer around user input is in the raster
                if buf.geometry.within(geom.geometry.any())[0] == True:
                #croping the dem using the buffer created around the user input point using rasterio.mask. 
                #Setting crop as true to crop the DEM 
                    out_image2, out_transform2 = mask(dem2, buf, crop = True)

                #checking if the cropped raster contains the value 1 (denoting flooded area)
                    if (1 in out_image2) == True:

                #if the clipped raster contains flooding, add a response to the user                  
                        validationlist.append('A survey of SAR (Synethic Aperture Radar) data suggests that your area was flooded during the 2021 floods.')
                    dem2.close()  


                #check if the user input is in South Chennai    
                else:
                    #opening the flooded areas in the South of Chennai 
                    with rio_open("validationdata/botcon2021.tif") as dem3:
                #croping the dem using the buffer created around the user input point using rasterio.mask. 
                #Setting crop as true to crop the DEM 
                            out_image3, out_transform3 = mask(dem3, buf, crop = True)

                            #checking if the cropped raster contains the value 1 (denoting flooded area)
                            if (1 in out_image3) == True:

                            #if the clipped raster contains flooding, add a response to the user                  
                                    validationlist.append('A survey of SAR (Synethic Aperture Radar) data during the floods suggests that your area was flooded during the 2021 floods.')
                                        
                            dem3.close()

        #opening flooded areas identified within SAR satellite data of 2015 floods
        with rio_open("validationdata/sar2015confinal.tif") as dem4:  # 50m resolution
                #croping the dem using the buffer created around the user input point using rasterio.mask. 
                #Setting crop as true to crop the DEM 
 
                out_image4, out_transform4 = mask(dem4, buf, crop = True)

                #checking if the cropped raster contains the value 1 (denoting flooded area)
                if (1 in out_image1) == True:

                                    #if the clipped raster contains flooding, add a response to the user                  

                    validationlist.append('A survey of SAR (S ynethic Aperture Radar) data suggests that your area was flooded during the 2015 floods.')
                dem1.close()

        #if the area contains no previous flooding data, append a sentence intimating the user that there was no flooding        
        if len(validationlist) <= 1:
            validationlist.append('A survey of Satellite Data of the previous floods did not find previous flooding in your area')
        else:
            pass
        return validationlist
        
    #passing the validatefloodfill function to variable list1
    list1 = validatefloodfill(buf)
    return list1 