# utilities needed for plotting data


import numpy as np
import geopandas as gp
import shapely as sp
import matplotlib.pyplot as plt
import contextily as cx
import cartopy as cp
from datetime import datetime as dt
from datetime import timedelta
import xarray as xr
import pandas as pd
import re
from shapely.geometry import Point
import os
from utils_filter import *
from utils_datetime import *

def plot_outlooks_day(outlooks_date, output_location, categories, show=False):
    # plots day 1, 2, and 3 outlooks for a day of given categories (hail, wind, tornado, categorical)
    outlooks_date['PRODISS'] = parse_datetime(outlooks_date['PRODISS'])
    for category in categories:
        outlooks_category = outlooks_date[outlooks_date['CATEGORY'] == category]
        for day in [1, 2, 3]:
            outlooks_category_day = outlooks_category[outlooks_category['DAY'] == day]
            latest_issue_time = np.max(outlooks_category_day['PRODISS'])
            outlooks_category_day = outlooks_category_day[outlooks_category_day['PRODISS'] == latest_issue_time]
            if outlooks_category_day.empty == False:
                ax = outlooks_category_day.plot('THRESHOLD', legend = True)
                plt.title('Day ' + str(day) + ' ' + category + ' outlook for ' + str(outlooks_category_day['DATE'].iloc[0]))
                cx.add_basemap(ax, crs=outlooks_category_day.crs)
                plt.savefig(output_location + '/day' + str(day) + '_' + category + '_' + str(outlooks_category_day['DATE'].iloc[0]) + '.png')
                if not show:
                   plt.close()

def plot_pph_day(pph_date, output_location, categories, show = False, sig = True):
    for category in categories:
        pph_date_category = pph_date[['p_perfect_' + category, 'lat', 'lon']]
        if sig:
            pph_date_category_sig = pph_date[['p_perfect_sig_' + category, 'lat', 'lon']]

        
        # credit: https://atlas.niu.edu/pperfect/BAMS/notebook_sample.html
        fig=plt.figure(figsize=(9,6))
        plt.style.use('dark_background')
        ax = plt.axes(projection = cp.crs.LambertConformal())
        ax.add_feature(cp.feature.LAND,facecolor='grey')
        ax.add_feature(cp.feature.OCEAN, alpha = 0.5)
        ax.add_feature(cp.feature.COASTLINE,linewidth=0.5)
        ax.add_feature(cp.feature.LAKES, alpha = 0.5)
        ax.add_feature(cp.feature.STATES,linewidth=0.5)

        plt.contourf(pph_date_category.lon.values, pph_date_category.lat.values, pph_date_category['p_perfect_' + category].values[:,:],
                    levels=[0,2], colors=['#FFFFFF'],
                    transform=cp.crs.PlateCarree(), alpha=0.)
        try:
            c = plt.contourf(pph_date_category.lon.values, pph_date_category.lat.values, pph_date_category['p_perfect_' + category].values[:,:],
                    levels=[2,5,10,15,30,45,60,100], colors=['#008b00','#8b4726','#ffc800', '#ff0000', '#ff00ff', '#912cee', '#104e8b'],
                    transform=cp.crs.PlateCarree())
            plt.annotate('PPER Max\n'+str(pph_date_category['p_perfect_' + category].values[:,:].max().round(1))+'%', xy=(0.88, 0.3), xycoords="figure fraction",
                        va="center", ha="center", color='white',fontsize=12,
                        bbox=dict(boxstyle="round", fc="k"))
        except:
            plt.annotate("No Reports", xy=(0.5, 0.5), xycoords="figure fraction",
                        va="center", ha="center", color='white',
                        bbox=dict(boxstyle="round", fc="k"))
            
        if sig:    
            try:
                plt.contourf(pph_date_category_sig.lon.values, pph_date_category_sig.lat.values, pph_date_category_sig['p_perfect_sig_' + category].values[0,:,:],
                        levels=[10,100], colors='none', hatches=['////'],
                        transform=cp.crs.PlateCarree())
                plt.contour(pph_date_category_sig.lon.values, pph_date_category_sig.lat.values, pph_date_category_sig['p_perfect_sig_' + category].values[0,:,:],
                        levels=[10,100], colors=['k'],
                        transform=cp.crs.PlateCarree())
            except:
                pass

        if category == 'tor':
            cat_title = 'Tornado'
        elif category == 'hail':
            cat_title = 'Hail'
        else:
            cat_title = 'Wind'

        ax.set_extent([-121, -71, 23, 50])
        plt.title('24 Hour Practically Perfect Hindcast for ' + cat_title)
        plt.colorbar(c,orientation="horizontal", pad=0.01, aspect=50,fraction=.1)
        plt.savefig(output_location + '/pph_' + category + '.png')
        if not show:
            plt.close()

def plot_reports(reports, output_location, categories, show = False):
    # plots all storm reports in reports
    for category in categories:
        reports_category = reports[reports['EVENT_TYPE'] == category]
        reports_category = reports_category[reports_category['BEGIN_LAT'] != '']
        reports_category = reports_category[reports_category['BEGIN_LON'] != '']
        reports_category['geometry'] = [Point(xy) for xy in zip(reports_category["BEGIN_LON"], reports_category["BEGIN_LAT"])]
        print(reports_category)
        ax = reports_category.plot(column = 'geometry', markersize = 1)
        #ax.legend(title="Significant")
        plt.title('All ' + category + ' Storm Reports')
        cx.add_basemap(ax, crs = {'init':'epsg:4326'})
        plt.savefig(output_location + '/report_' + category + '.png')
        if not show:
            plt.close()


# For MCA notebook:
def make_submap(pph, ax, data, title, day_colors):
    ax.add_feature(cp.feature.LAND,facecolor='grey')
    ax.add_feature(cp.feature.OCEAN, alpha = 0.5)
    ax.add_feature(cp.feature.COASTLINE,linewidth=0.5)
    ax.add_feature(cp.feature.LAKES, alpha = 0.5)
    ax.add_feature(cp.feature.STATES,linewidth=0.5)
    if day_colors:
        c = ax.contourf(pph.lon.values, pph.lat.values, data, transform=cp.crs.PlateCarree(), levels=[.02,.05,.10,.15,.30,.45,.60,1.00], colors=['#008b00','#8b4726','#ffc800', '#ff0000', '#ff00ff', '#912cee', '#104e8b'])
        plt.colorbar(c)
    else:
        vmax = max(-data.min(), data.max()).values
        c = ax.contourf(pph.lon.values, pph.lat.values, data, transform=cp.crs.PlateCarree(), levels=np.linspace(-vmax, vmax, 40), cmap = 'PuOr')
        plt.colorbar(c, ax = ax) 
    ax.set_title(title)
    return ax

def plot_day(date_investigate, outlook_dataset_renamed, pph_renamed, hazardstring, pcs, pc_nmodes, hazard, plot_pcs, pph):
    date_investiagate_string = date_investigate[:10]
    fig, axs = plt.subplots(ncols= 2, subplot_kw=dict(projection = cp.crs.PlateCarree()), figsize = (15, 4))
    axs[0] = make_submap(pph, axs[0], outlook_dataset_renamed['p_'+hazard].sel(time = date_investigate), hazardstring + ' Outlook for ' + date_investiagate_string, True)
    axs[1] = make_submap(pph, axs[1], pph_renamed['p_perfect_'+hazard].sel(time = date_investigate), hazardstring + ' PPH for ' + date_investiagate_string, True)
    plt.show()
    plt.clf()

    if plot_pcs:
        fig, axs = plt.subplots(ncols= 2, figsize = (15, 4))
        axs[0].plot(pcs['left'].sel(time = date_investigate)[:pc_nmodes])
        axs[0].set_ylabel('PC Value')
        axs[0].set_xlabel('Mode')
        axs[0].set_xticks(range(pc_nmodes))
        axs[0].set_title(hazardstring + ' Outlook PC Values for ' + date_investiagate_string)
        axs[1].plot(pcs['right'].sel(time = date_investigate)[:pc_nmodes])
        axs[1].set_ylabel('PC Value')
        axs[1].set_xlabel('Mode')
        axs[1].set_xticks(range(pc_nmodes))
        axs[1].set_title(hazardstring + ' PPH PC Values for ' + date_investiagate_string)
        plt.show()
        plt.clf()






