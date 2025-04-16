# utility functions needed for project

import numpy as np
import geopandas as gp
import shapely as sp
import matplotlib.pyplot as plt
import cartopy as cp
from datetime import datetime as dt
from datetime import timedelta
import xarray as xr
import pandas as pd
import re
import os
from utils_datetime import *


def identify_dates_above_threshold(outlooks, threshold):
    # returns list of dates where there was ever a forecast at threshold in dataframe outlooks
    # later: do by hazard type?
    filtered = outlooks[outlooks['THRESHOLD'] == threshold]
    return filtered['DATE'].unique()



def filter_reports(reports, columns, event_types):
    # returns only storm reports from reports dataset with given event type and only the specified columns
    reports = reports[reports['EVENT_TYPE'].isin(event_types)]
    return reports[columns]



def read_datasets(data_location, mod_string = 'all'):
    # reads in either full, moderate, or labelled pre-processed datasets

    if mod_string == 'all':
        print('reading outlooks 1')
        outlook1 = gp.read_file(f"{data_location}/outlooks/{mod_string}_outlooks_1.shp", engine="pyogrio")
        print('reading outlooks 2')
        outlook2 = gp.read_file(f"{data_location}/outlooks/{mod_string}_outlooks_2.shp", engine="pyogrio")
        outlooks = gp.GeoDataFrame(pd.concat([outlook1, outlook2], ignore_index=True), crs=outlook1.crs)


    else:
        print('reading outlooks')
        outlooks = gp.read_file(data_location + '/outlooks/' + mod_string + '_outlooks.shp', engine="pyogrio")

    print('reading pph')
    pph = xr.open_dataset(data_location + '/pph/' + mod_string + '_pph.nc')

    print('reading storm reports')
    reports = gp.read_file(data_location + '/storm_reports/' + mod_string + '_reports.csv')
    return outlooks, pph, reports


def select_days_outlooks(outlooks, dates):
    # filters outlooks to only those with DATE in dates, assuming dates is in datetime format
    dates = revert_datetimes(dates)
    return outlooks[outlooks['DATE'].isin(dates)]

def select_days_pph(pph, dates):
    return pph.sel(time=pph.time.dt.date.isin(dates))

def select_days_reports(reports, dates):
    dates = revert_datetimes_reports(dates)
    return reports[reports['DATE'].isin(dates)]

def add_significant_column(reports):
    # adds column to storm report dataframe with whether or not event was significant
    significant = [False for i in range(len(reports))]
    i = 0
    for x, row in reports.iterrows():
        if row['EVENT_TYPE'] == 'Hail' and row['MAGNITUDE'] != '':
            if float(row['MAGNITUDE']) >= 2:
                significant[i] = True
        if row['EVENT_TYPE'] == 'Thunderstorm Wind' and row['MAGNITUDE'] != '':
            if float(row['MAGNITUDE']) >= 74:
                significant[i] = True
        if row['EVENT_TYPE'] == 'Tornado' and row['TOR_F_SCALE'] != '':
            if row['TOR_F_SCALE'] in (['F2', 'F3', 'F4', 'F5', 'EF2', 'EF3', 'EF4', 'EF5']):
                significant[i] = True
        i = i+1
    reports['significant'] = significant
    return reports

def create_ramp_lists(outlooks, category_dict):

    ramp_ups = {
        0: [],
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: []
    }

    ramp_downs = {
        0: [],
        -1: [],
        -2: [],
        -3: [],
        -4: [],
        -5: [],
        -6: []
    }

    ramp_categories = {
        'up': [],
        'down': [],
        'both': [],
        'neither': []
    }

    old_date = '0'
    old_do = '0'
    first = True

    for index, row in outlooks.iterrows(): #iterrating through each polygon in the outlook dataset
        cat = category_dict[row['THRESHOLD']]
        do = row['DATE_ORDER']
        date = row['DATE']

        if date != old_date: # New date, save ramp up and ramp down and save alongside old date, then reset ramps, max and min categories seen, and do threshold
            
            
            if first == True:
                first = False
            else:
                ramp_ups[ramp_up].append(old_date)
                ramp_downs[ramp_down].append(old_date)
                if ramp_up > 0 and ramp_down < 0:
                    ramp_categories['both'].append(old_date)
                elif ramp_up > 0:
                    ramp_categories['up'].append(old_date)
                elif ramp_down < 0:
                    ramp_categories['down'].append(old_date)
                else:
                    ramp_categories['neither'].append(old_date)

            old_date = date
            old_do = do
            
            ramp_down = 0
            ramp_up = 0
            max_cat_date = -1
            
            if do[-1] == '1': 
                min_cat_date = 5 
            else: # First outlook for this date is not day 3, so day 3 had no outlook.
                min_cat_date = -1

            max_cat_do = cat


        elif do != old_do: # new outlook, update min and max categories seen, ramp value
            if max_cat_do - min_cat_date > ramp_up:
                ramp_up = max_cat_do - min_cat_date
            if max_cat_do - max_cat_date < ramp_down:
                ramp_down = max_cat_do - max_cat_date

            if max_cat_do > max_cat_date:
                max_cat_date = max_cat_do
            if max_cat_do < min_cat_date:
                min_cat_date = max_cat_do

            old_do = do

            max_cat_do = cat

        else: # Just another threshold within the same polygon
            if cat > max_cat_do:
                max_cat_do = cat
        
    # for last iteration
    ramp_ups[ramp_up].append(old_date)
    ramp_downs[ramp_down].append(old_date)
    if ramp_up > 0 and ramp_down < 0:
        ramp_categories['both'].append(old_date)
    elif ramp_up > 0:
        ramp_categories['up'].append(old_date)
    elif ramp_down < 0:
        ramp_categories['down'].append(old_date)
    else:
        ramp_categories['neither'].append(old_date)

    return(ramp_ups, ramp_downs, ramp_categories)

