
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


# functions for dealing with datetimes
def parse_datetime(date_strings):
    # convertes list of datetime strings (format used for outlooks, %Y%m%d%H%M) to list of datetime objects
    for date_string, i in zip(date_strings, range(len(date_strings))):
        if i == 0:
            ret = [dt.strptime(date_string, "%Y%m%d%H%M")]
        else:
            ret.append(dt.strptime(date_string, "%Y%m%d%H%M"))
        #if np.mod(i, 10000) == 0:
        #    print(i)
        #    print(dt.strptime(date_string, "%Y%m%d%H%M"))
    return ret

def revert_datetimes(datetimes):
    # convert list of datetime objects back to strings
    for datetime, i in zip(datetimes, range(len(datetimes))):
        string = datetime.strftime("%Y%m%d%H%M")
        if i == 0:
            ret = [string]
        else:
            ret.append(string)
    return ret

def revert_datetimes_reports(datetimes):
    # convert list of datetime objects back to strings in format used in reports
    for datetime, i in zip(datetimes, range(len(datetimes))):
        string = datetime.strftime("%Y-%m-%d")
        if i == 0:
            ret = [string]
        else:
            ret.append(string)
    return ret

def revert_all_datetimes(outlooks):
    # reverts all datetimes in outlooks to string format
    datetime_columns = outlooks.select_dtypes(include=['datetime64[ns]']).columns
    for column in datetime_columns:
        outlooks[column] = revert_datetimes(outlooks[column])
    #print(outlooks['DATE'])
    outlooks['DATE'] = revert_datetimes(outlooks['DATE']) # assumes DATE column exists and needs to be converted too
    return outlooks

def create_dates(datetimes, shift):
    # converts list of datetime object to list of dates (YMD)
    # TODO: does this cause end of month issue? But only sometimes????
    for datetime, i in zip(datetimes, range(len(datetimes))):
        days = timedelta(shift)
        if i == 0:
            ret = [datetime.date() + days]
        else:
            ret.append(datetime.date() + days)
    return ret

def get_years(dates):
    # turns a list of dates into a list of years
    for date, i in zip(dates, range(len(dates))):
        if i == 0:
            years = [date.year]
        else:
            years.append(date.year)
    return years

def parse_datetime_reports(date_strings):
    # convertes list of datetime strings (outlook format) to list of dates
    for date_string, i in zip(date_strings, range(len(date_strings))):
        # strip time, add tzinfo, convert to UTC, get correct date
        val = dt.strptime(date_string, "%d-%b-%y %H:%M:%S").date()
        if i == 0:
            ret = [val]
        else:
            ret.append(val)
        #if np.mod(i, 10000) == 0:
        #    print(i)
        #    print(dt.strptime(date_string, "%Y%m%d%H%M"))
    return ret

def fix_month_issue(outlooks):
    # fixes issue where many day 3 outlooks issed on last day of a month wrongly have issue and expire times the second of the same month rather than the following month
    d = None
    for i, row in outlooks.iterrows():
        if row['PRODISS'] > row['EXPIRE'] and row['DAY'] == 3:
            if row['EXPIRE'] != d:
                d = row['EXPIRE']
                print('Fixing for ' + str(d))
            # add one month to issue and expire
            issuedate = row['ISSUE'] + pd.DateOffset(months=1)
            expiredate = row['EXPIRE'] + pd.DateOffset(months=1)
            outlooks.at[i, 'ISSUE'] = issuedate
            outlooks.at[i, 'EXPIRE'] = expiredate  
    return outlooks
