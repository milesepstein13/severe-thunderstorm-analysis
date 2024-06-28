

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