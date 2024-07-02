import metpy as mp
import metpy.calc as mpcalc
from metpy.units import units
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def request_era5_day(client, area, single_variable, pressure_variable, pressure_level, datestring, times, save_location):
    
    # download single level
    if single_variable != []:
        print('Requesting Single Level')
        client.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'area': area,
                'variable': single_variable,
                'year': datestring[0:4],
                'month': datestring[4:6],
                'day': datestring[6:8],
                'time': times,
            },
            save_location + '/single/' + datestring + '_single.nc')
    
    # download pressure levels
    if pressure_variable != []:
        print('Requesting Pressure Levels')
        client.retrieve(
            'reanalysis-era5-pressure-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': pressure_variable,
                'pressure_level': pressure_level,
                'area': area,
                'year': datestring[0:4],
                'month': datestring[4:6],
                'day': datestring[6:8],
                'time': times,
            },
            save_location + '/pressure/' + datestring + '_pressure.nc')
    return

def calculate_cape(ds_single, ds_pressure):
    # ERA5 CAPE is MUCAPE
    # Adds metpy calculated cape and cin and difference between metpy and ERA5 capes to ds_single
    # add empty cape_mp and cin_mp to ds_single
    ds_single['cape_mp'] = xr.zeros_like(ds_single['cape'])
    ds_single['cin_mp'] =  xr.zeros_like(ds_single['cape'])

    # plot with reports/outlooks/pph?
    for time in ds_pressure['time']:
        for lon in ds_pressure['longitude']:
            for lat in ds_pressure['latitude']:
                profile = ds_pressure.sel(time = time, longitude = lon, latitude = lat)
                surface = ds_single.sel(time = time, longitude = lon, latitude = lat)


                surface_pressure = (surface['sp'].values * units.Pa).to(units.hPa)
                original_pressure_levels = profile.level.values * units.hPa
                pressure_levels = original_pressure_levels[original_pressure_levels<surface_pressure]
                pressure = np.append(pressure_levels, surface_pressure)[::-1]

                surface_temperature = (surface['t2m'].values * units.kelvin)
                temperature_levels = profile.t.values * units.kelvin
                temperature_levels = temperature_levels[original_pressure_levels<surface_pressure]
                temperature = np.append(temperature_levels, surface_temperature)[::-1]

                surface_dewpoint = (surface['d2m'].values * units.kelvin)
                dewpoint_levels = mpcalc.dewpoint_from_specific_humidity(pressure_levels, temperature_levels, (profile.q.values * units.dimensionless)[original_pressure_levels<surface_pressure])
                dewpoint = np.append(dewpoint_levels, surface_dewpoint)[::-1]

                parcel_profile = mpcalc.parcel_profile(pressure, temperature[0], dewpoint[0]).to('degC')

                (cape, cin) = mpcalc.cape_cin(pressure, temperature, dewpoint, parcel_profile)

                ds_single['cape_mp'].loc[dict(time=time, longitude = lon, latitude = lat)] = cape.magnitude
                ds_single['cin_mp'].loc[dict(time=time, longitude = lon, latitude = lat)] = cin.magnitude
    ds_single['cape_dif'] = ds_single['cape'] - ds_single['cape_mp']
    ds_single['cape_dif'] = ds_single['cape_dif'] * units.J / units.kg
    return ds_single



def plot_era5_variable(data, time, var, varname, min = None, max = None, num_levels = 21, cmap = 'YlOrBr', extent = None):
    plot_data = data.sel(time=time)[var].metpy.quantify()

    fig = plt.figure(figsize=(16, 12))
    ax = fig.add_subplot(111, projection=ccrs.LambertConformal())
    if extent:
        ax.set_extent(extent)
    else:
        ax.set_extent([plot_data.longitude.min(), plot_data.longitude.max(), plot_data.latitude.min(), plot_data.latitude.max()])

    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=1)
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.5, edgecolor='black')
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=1, edgecolor='black')

    if not max:
        max = np.round(plot_data.data.max().magnitude)

    if not min:
        min = np.round(plot_data.data.min().magnitude)

    levels = np.linspace(min, max, num_levels)

    plot = ax.contourf(plot_data['longitude'], plot_data['latitude'], plot_data.data, levels=levels, cmap = cmap, transform=ccrs.PlateCarree())
    cb = fig.colorbar(plot, ax=ax, orientation='horizontal', pad=0.05, aspect=30)
    cb.set_ticks(np.linspace(min, max, num_levels))
    ax.set_title('ERA5 ' + str(time.data)[0:19] + ' ' + varname + ' (' + str(plot_data.data.units) + ')', fontsize=14, loc='left')
    plt.show()
    plt.clf()
    # TODO: add save functionality, make show and save both functional

    return