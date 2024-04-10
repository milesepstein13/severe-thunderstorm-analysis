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
from utils_plotting import *

def analyze_variance(expvar, variance_nmodes, hazardstring):
    # make plot of decreasing explained variance
    
    plt.plot(expvar[:variance_nmodes]/100)
    plt.ylim(0, .3)
    xint = range(variance_nmodes)
    plt.xticks(xint)
    plt.xlabel('Mode')
    plt.ylabel('Fraction of Variance Explained')
    plt.title('Variance Explained by MCA Mode for ' + hazardstring + ' Outlooks and PPH')
    plt.show()
    plt.clf()

def analyze_eofs(eofs, pph, nmodes, hazardstring):
    # make plots of eofs for each of first few modes. In particular, look for where the left and right plots vary. Those are modes where forecast is usually different from results
    # and explain physical phenomena occuring
    fig, axs = plt.subplots(nrows = nmodes, ncols= 2, subplot_kw=dict(projection = cp.crs.PlateCarree()), figsize = (15, nmodes*4))
    
    for i in range(nmodes):
        for side, j in zip(['left', 'right'], range(2)):
            if side == 'left':
                sidestring = 'Outlooks'
            else:
                sidestring = 'PPH'
            axs[i, j] = make_submap(pph, axs[i, j], eofs[side][:, :, i], hazardstring + ' ' + sidestring + ' Mode ' + str(i), False)

    plt.show()
    plt.clf()


def analyze_pcs(pcs, hazardstring):
    # make plots of pcs for first few modes, but may be less interesting.
    plt.plot(pcs['left'][:, 0])
    plt.xlabel('Day of Study')
    plt.ylabel('PC Value')
    plt.title(hazardstring + ' Outlook PC Value Across Days for Mode 0')
    plt.show() 
    plt.clf()

def analyze_protopypical_days(pcs, outlook_dataset_renamed, pph_renamed, hazardstring, pc_nmodes, hazard, pph):
    # for each of first n modes, plot the outlook/pph that maximizes and minimizes that mode. i.e. what is prototypical day that that mode representing
    outlook_max_dates = pcs['left'].argmax(dim = 'time')
    outlook_min_dates = pcs['left'].argmin(dim = 'time')
    pph_max_dates = pcs['right'].argmax(dim = 'time')
    pph_min_dates = pcs['right'].argmin(dim = 'time')
    for i in range(pc_nmodes):
        date_investigate = str(pcs['left'].time[outlook_max_dates[i]].values)[:19]
        print('Day Maximixing Outlooks PC ' + str(i) + ', ' + date_investigate)
        plot_day(date_investigate, outlook_dataset_renamed, pph_renamed, hazardstring, pcs, pc_nmodes, hazard, True, pph)

        date_investigate = str(pcs['left'].time[outlook_min_dates[i]].values)[:19]
        print('Day Minimizing Outlooks PC ' + str(i) + ', ' + date_investigate)
        plot_day(date_investigate, outlook_dataset_renamed, pph_renamed, hazardstring, pcs, pc_nmodes, hazard, True, pph)

def analyze_mca(expvar, eofs, pcs, variance_nmodes, hazardstring, nmodes, pph, date_investigate, outlook_dataset_renamed, pph_renamed, pc_nmodes, hazard):
    analyze_variance(expvar, variance_nmodes, hazardstring)
    analyze_eofs(eofs, pph, nmodes, hazardstring)
    analyze_pcs(pcs, hazardstring)
    plot_day(date_investigate, outlook_dataset_renamed, pph_renamed, hazardstring, pcs, pc_nmodes, hazard, True, pph)
    analyze_protopypical_days(pcs, outlook_dataset_renamed, pph_renamed, hazardstring, pc_nmodes, hazard, pph)