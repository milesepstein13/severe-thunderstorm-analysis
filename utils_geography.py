import numpy as np
import geopandas as gp
import shapely as sp
import matplotlib.pyplot as plt
import contextily as cx
import cartopy as cp
from datetime import datetime as dt
import datetime
from datetime import timedelta
import xarray as xr
import pandas as pd
import re
import os
import cartopy.crs as ccrs
import utils
from xmca.xarray import xMCA
from matplotlib.ticker import MaxNLocator
from shapely.geometry import Point

def inside_polygon(lat_lon, geometry):
    lat_lon = (lat_lon[1], lat_lon[0])
    polygons = sp.polygonize([geometry])
    for i in range(len(polygons.geoms)):
        polygon = polygons.geoms[i]
        if Point(lat_lon).within(polygon):
            return True
    return False

def find_threshold(outlooks_date, lat, lon):
    # returns the threshold of the polygon that lat_lon is in, or zero if not in any
    #print(outlooks_date)
    outlooks_date = outlooks_date.sort_values(by = 'THRESHOLD', ascending = False)
    for row in outlooks_date.iterrows():
        #print(row)
        #print(lat_lon)
        #print(row)
        if inside_polygon((lat, lon), row[1]['geometry']):
            #if float(row[1]['THRESHOLD']) > .3:
            #    print('found at ' + str(row[1]['THRESHOLD']))
            return float(row[1]['THRESHOLD'])
    return 0

def create_gridded_outlook_dataset(outlooks, pph, hazards, save_location):
    # build gridded outlook dataset with dimension matching pph for given hazards. Saves as netCDF to save_location
    outlook_dataset = xr.Dataset(
        data_vars=dict(
            lat=(['y', 'x'], pph['lat'].data),
            lon=(['y', 'x'], pph['lon'].data)
        ),
        coords=dict(
            time=(['time'], pph['time'].data),
            x=(['x'], pph['x'].data),
            y=(['y'], pph['y'].data),
        ),
        attrs=dict(description="outlook as a percentage as a function of date, lat/lon, and which hazard type",
                grid = pph.grid),
    )

    # TODO: assign these from hazard names
    outlook_dataset = outlook_dataset.assign(p_hail = (('time', 'y', 'x'), np.full((len(outlook_dataset['time']), len(outlook_dataset['y']), len(outlook_dataset['x'])), 0.0)))
    outlook_dataset = outlook_dataset.assign(p_wind = (('time', 'y', 'x'), np.full((len(outlook_dataset['time']), len(outlook_dataset['y']), len(outlook_dataset['x'])), 0.0)))
    outlook_dataset = outlook_dataset.assign(p_tor = (('time', 'y', 'x'), np.full((len(outlook_dataset['time']), len(outlook_dataset['y']), len(outlook_dataset['x'])), 0.0)))
    
    for hazard in hazards:

        print(hazard)
        if hazard == 'hail':
            hazard_key = 'HAIL'
        elif hazard == 'wind':
            hazard_key = 'WIND'
        elif hazard == 'tor':
            hazard_key = 'TORNADO' 
        outlooks_cat = outlooks[outlooks['CATEGORY'] == hazard_key]

        oldyear = 0
        done = 0
        
        array = np.zeros((len(outlook_dataset.time.values), len(outlook_dataset.y.values), len(outlook_dataset.x.values)))

        for date, i in zip(outlook_dataset.time.values, range(len(outlook_dataset.time.values))):
            lats = outlook_dataset.sel(time = date).lat
            lons = outlook_dataset.sel(time = date).lon
            # pick only day 1 outlooks on that date from outlooks
            datestring = str(date)
            datestring = datestring[0:4] + datestring[5:7] + datestring[8:10] + '0000'
            
            # printing to track progress
            year = datestring[0:4]
            if year != oldyear:
                print(year)
                oldyear = year
                #print(ret_matrix)
            outlooks_date = outlooks_cat[outlooks_cat['DATE'] == datestring]
            if (len(outlooks_date) > 0): #there are outlooks on this date
                outlooks_date = outlooks_date[outlooks_date['PRODISS'] == max(outlooks_date['PRODISS'])] # latest outlook-- put in new subsetting code
                outlooks_date = outlooks_date[outlooks_date['THRESHOLD'] != 'SIGN']
                
                #array = np.zeros((len(outlook_dataset.y.values), len(outlook_dataset.x.values)))
                for x, j in zip(outlook_dataset.x.values, range(len(outlook_dataset.x.values))):
                    for y, k in zip(outlook_dataset.y.values, range(len(outlook_dataset.y.values))):
                        lat = lats.sel(x = x, y = y).values
                        lon = lons.sel(x = x, y = y).values
                        #outlook_dataset['p_' + hazard].loc[dict(time = date, y = y, x = x)] = find_threshold(outlooks_date, lat, lon)
                        array[i, k, j] = find_threshold(outlooks_date, lat, lon)
                #outlook_dataset['p_' + hazard]['time' == date] = array
                if done == 0:
                    savei = i
                done = done + 1
                savedate = date
        me = xr.DataArray(array, coords={'time': outlook_dataset.time.values, 'y': outlook_dataset.y.values, 'x': outlook_dataset.x.values},
                dims=['time', 'y', 'x'])
        outlook_dataset['p_' + hazard] = me
    outlook_dataset.to_netcdf(save_location)
    return outlook_dataset
