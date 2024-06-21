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
from geopy.geocoders import Nominatim

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

def get_season_dates(outlooks, seasons):
    dates = outlooks['DATE'].unique()
    season_dates = [[], [], [], []]
    for date in dates:
        month = int(date[4:6])
        if month == 12 or month < 3:
            season_dates[0].append(date)
        elif month < 6:
            season_dates[1].append(date)
        elif month < 9:
            season_dates[2].append(date)
        else:
            season_dates[3].append(date)
    return season_dates

def get_state(lat, lon, geolocator):
    location = geolocator.reverse(str(lat)+","+str(lon))
    if location == None:
        return None
    address = location.raw['address']
    state = address.get('state', '')
    return state

def get_region(lat, lon, west_threshold_co_nm, regions_dict, geolocator):
    state = get_state(lat, lon, geolocator)
    if state == 'Colorado' or state == 'New Mexico':
        if lon < west_threshold_co_nm:
            return('West')
        else:
            return('Great Plains')
    for region in regions_dict:
        if state in regions_dict[region]:
            return region
    return('NONE')


def create_regions(pph):
    regions = {
        'West': [],
        'Midwest': [],
        'Great Plains': [],
        'Northeast': [],
        'South': [],
        'NONE': []
    }

    geolocator = Nominatim(user_agent="severe_thunderstorm_miles")
    west_threshold_co_nm = -105
    regions_dict = { # list of states fully within each region (doesn't include AK, HI, CO, NM)
        'West': ['Washington', 'Oregon', 'California', 'Idaho', 'Montana', 'Wyoming', 'Utah', 'Arizona'],
        'Midwest': ['North Dakota', 'South Dakota', 'Minnesota', 'Iowa', 'Wisconsin', 'Illinois', 'Michigan', 'Indiana', 'Ohio', 'Kentucky'],
        'Great Plains': ['Nebraska', 'Kansas', 'Oklahoma', 'Texas', 'Missouri'],
        'Northeast': ['Maine', 'Vermont', 'New Hampshire', 'Massachusetts', 'Rhode Island', 'Connecticut', 'New York', 'Pennsylvania', 'New Jersey', 'Delaware', 'Maryland', 'District of Columbia', 'West Virginia'],
        'South': ['Virginia', 'Arkansas', 'Louisiana', 'Tennessee', 'Mississippi', 'Alabama', 'Georgia', 'North Carolina', 'South Carolina', 'Florida']
    }

    old_year = ''
    for date, date_pph in pph.groupby('time'):
        if date_pph['p_perfect_total'].max() > 0:
            year = date[0:4]
            if year != old_year:
                print("Finding regions for " + year)
                old_year = year
            max_coords = date_pph['p_perfect_total'].argmax(dim = ['x', 'y'])
            max_x_coord = max_coords['x'].values
            max_y_coord = max_coords['y'].values
            lat = date_pph['lat'].loc[dict(x = max_x_coord, y = max_y_coord)].values
            lon = date_pph['lon'].loc[dict(x = max_x_coord, y = max_y_coord)].values
            region = get_region(lat, lon, west_threshold_co_nm, regions_dict, geolocator)
            regions[region].append(date)
            
    return(regions)