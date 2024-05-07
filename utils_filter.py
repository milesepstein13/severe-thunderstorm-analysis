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



def read_datasets(data_location, moderate):
    # reads in either full or moderate only pre-processed datasets
    if moderate:
        mod_string = 'mdt'
    else:
        mod_string = 'all'

    if moderate:
        print('reading outlooks')
        outlooks = gp.read_file(data_location + '/outlooks/' + mod_string + '_outlooks.shp')

    else:
        print('reading outlooks 1')
        outlooks = gp.read_file(data_location + '/outlooks/' + mod_string + '_outlooks_1.shp')
        print('reading outlooks 2')
        outlooks = outlooks.append(gp.read_file(data_location + '/outlooks/' + mod_string + '_outlooks_2.shp'))

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