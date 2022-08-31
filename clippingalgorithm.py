# -*- coding: utf-8 -*-
"""
Created on Fri Jul  1 10:36:49 2022
This is a wrapper function for the flood fill algorithm 
@author: 10853401
"""
#calling inputs 
import geopandas as gpd #importing geopandas as gpd to save as geojson
from math import floor, ceil #importing floor and ceil to use in the flood fill algorithm
from numpy import zeros, linspace  #importing use in the flood fill algorithm
from shapely.geometry import Point , mapping #importing point and mapping to add input points and convert geoseries to geojson
from rasterio import open as rio_open #importing open to open Digital Elevation Models
from rasterio.mask import mask #importing mask to mask the DEM layer
from matplotlib.colors import Normalize #importing normalise for color scheme 
from rasterio.plot import show as rio_show #importing show to add the raster to matplotlib
from matplotlib.colors import LinearSegmentedColormap #imported for coloring the output map 
from matplotlib.pyplot import subplots, savefig, get_cmap # importing for geting colormap, saving figure and using subplots



############################################## Defining the flood fill algorithm #####################################################################


def floodfillalgorithm(latcoord1, longcoord1, flooddepth1):
    """writing all the code within a larger function floodfillaglorithm to be called within the flask application

    
    The function takes the depth, latitude, longitude of the Input VGI Point after it is sent to the database
    The function returns a 200m buffer around the point used to perform the L.ImageOverlay function using leaflet on the front-end
    The function first clips a DEM of Chennai  
    """
    



    #depth 
    def flood_fill(depth, x0, y0, d, dem_data1):
    
            """
            function flood_fill() calculates the flood fill of a 200m area around the user input taking the lat and long of point as input
            depth - flood depth sent by user
            x0 & y0 - coordinates of point
            d - DEM raster array
            dem_data1 - Digital Elevation Model opened with rasterio
            the function returns a flood fill of the clipped DEM
            """
    
            # create output array at the same dimensions as the d
            flood_layer = zeros(dem_data1.shape)
    
            # convert from coordinate space to image space
            r0, c0 = d.index(x0, y0)
    
            # set for cells already assessed
            assessed = set()
    
            # set for cells to be assessed
            to_assess = set()
    
            # start with the origin cell
            to_assess.add((r0, c0))
    
            # calculate the maximum elevation of the flood
            flood_extent = dem_data1[(r0, c0)] + depth
    
            # keep looping as long as there are cells left to be checked
            while to_assess:
    
                # get the next cell to be assessed (removing it from the to_assess set)
                r, c = to_assess.pop()
    
                # add it to the register of those already assessed
                assessed.add((r, c))
    
                # is the elevation low enough for this cell to be flooded?
                if dem_data1[(r, c)] <= flood_extent:
    
                    # mark the current cell as flooded
                    flood_layer[(r, c)] = 1
                    
                    # loop through all neighbouring cells
                    for r_adj, c_adj in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
    
                        # get current neighbour
                        neighbour = (r + r_adj, c + c_adj)
    
                        # make sure that the location is wihin the bounds of the dataset and has not been assessed previously...
                        if 0 <= neighbour[0] < dem1.height and 0 <= neighbour[1] < dem1.width and neighbour not in assessed:
    
                                # ...then add to the set for assessment
                                to_assess.add(neighbour)
            print('done with flood fill')

            # when complete, return the result
            return flood_layer  

    
    # set origin for the flood as a tuple
    LOCATION = (latcoord1,longcoord1)
    pointtobuffer = gpd.GeoSeries(Point((LOCATION[1], LOCATION[0])))
    buf = pointtobuffer.buffer(0.001, cap_style=3)


    FLOOD_DEPTH = float(flooddepth1)
    #changing crs of buffer
    buf = buf.set_crs('epsg:3857')

    bbox = buf.bounds

    print('done')
    #coverting buf to geodataframe and writing to geojson
    envgdf = gpd.GeoDataFrame(geometry=buf)
    #writing bug to geojson called bounds
    with open("static/bounds.geojson","w") as f:
        f.write(envgdf.to_json())
    
    # open the SRTM 30m raster dataset for the city of Chennai
    with rio_open("./demfinalvoidfilled.tif") as dem:  # 50m resolution

        #copying the metadata of the dem 
        out_meta = dem.meta

        #croping the dem using the buffer created around the user input point using rasterio.mask. 
        #Setting crop as true to crop the DEM 
        out_image, out_transform = mask(dem, buf, crop = True)

        #coyping the profile of the SRTM raster

        profile = dem.profile

        #setting the shape of the output raster to out image created above 

        profile["height"] = out_image.shape[1] 
        profile["width"] = out_image.shape[2]
        profile["transform"] = out_transform
        
        # copying metadata to new tif 
        out_meta.update({"driver": "GTiff",
                          "height": out_image.shape[1],
                          "width": out_image.shape[2],
                          "transform": out_transform})

    # writing the masked tif to masked.tif
    with rio_open("out/masked.tif", "w", **out_meta) as dest:
        dest.write(out_image)
        print('done with clip')
        dest.close()
    

    #opening the masked raster to perform flood fill 
    with rio_open("out/masked.tif") as dem1:  # 50m resolution
        dem_data1 = dem1.read(1)
        
        # calculate the flood layer using the flood fill function defined above providing the flood depth & lat &long of user point and  as input 

        output = flood_fill(FLOOD_DEPTH, longcoord1, latcoord1, dem1, dem_data1)

        #writing output to new dataset called new.tif
        new_dataset = rio_open(
        'out/floodfill.tif',
        'w',
        driver='GTiff',
        height=output.shape[0],
        width=output.shape[1],
        count=1,
        dtype=output.dtype,
        crs=dem1.crs,
        transform = dem1.transform,

        )

        #writing the new dataset and closing datasets
        new_dataset.write(output, 1)
        new_dataset.close()
        dem1.close()


# plotting the flood fill and saving it as a a PNG 

    #setting axes to the matplotlib plot
    fig, my_ax = subplots(1, 1, figsize=(16, 10))

    # add flooding
    rio_show(
        output,
        ax=my_ax,
        transform=dem1.transform,
        cmap = LinearSegmentedColormap.from_list('binary', [(0, 0, 0, 0), (0, 0, 1, 1)], N=2)
        )
    my_ax.axis("off")

    # save the result
    savefig('out/floodfill.png', bbox_inches='tight',transparent=True, pad_inches=0)
    print('done with plot')

    #returning the buffer around the point to the flask application
    return(buf)





















