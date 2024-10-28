# -*- coding: utf-8 -*-
"""==============================================================================
  
Title          :CFS_climateForecastSystemData.py
Description    :This download data from the CFS based on an admin boundary
Author         :LF Velasquez - MapAction - lvelasquez@mapaction.org
Date           :06/02/2023
Version        :1.0
Usage          :CFS_climateForecastSystemData.py --clim_var=<precipitation or temparature> --bndr=<boundary file name>
Notes          :The serialization warning has been muted - line 32. This might
                need looking at again, at the moment no errors have been identified
python version :Python 3.8.17
 
=============================================================================="""


# =============================================================================
# Modules - Libraries
# =============================================================================

import os
import xarray as xr
import os
os.environ['USE_PYGEOS'] = '0'
import geopandas as gpd
import numpy as np
import datetime as dt
from pathlib import Path
import logging
import click

import warnings
warnings.simplefilter("ignore") 


# =============================================================================
# Settign the path variabless
# =============================================================================
src_path = Path().absolute()

#############################################################
# FUNCTIONS
#############################################################
def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Set up a simple logger -
    https://engineeringfordatascience.com/posts/python_logging/"""
    log = logging.getLogger(__name__)
    console = logging.StreamHandler()
    log.addHandler(console)
    log.setLevel(level)
    return log

def url(resolution, forecast):
    """set up URL for data download

    Args:
        resolution (_str_): data resolution as per CRS
        forecast (_str_): variables to look at in CFS

    Returns:
        _str_: _data download URL
    """
    res = resolution
    date = (dt.date.today()).strftime("%Y%m%d")

    if forecast == 'temperature':
        # this is the daily temperature
        step = '_1hr'
        hour = 6
        gfs = f'https://nomads.ncep.noaa.gov/dods/gfs_{res}{step}'
        url = f'{gfs}/gfs{date}/gfs_{res}{step}_{hour:02d}z'
    
    if forecast == 'precipitation':
        # this is for daily precipitation
        hour = 0
        gfs = f'https://nomads.ncep.noaa.gov/dods/gfs_{res}'
        url = f'{gfs}/gfs{date}/gfs_{res}_{hour:02d}z'

    log.info(f"\n --- \n Here is the URL for the data download\n --- \n {url}")
    log.info(f"\n --- \n Here is the URL for the data information\n --- \n {url}.info")
    return url

def fetch_data(forecast, main_path, shp_name, url_add):
    """retrieves data from URL and creates nc file

    Args:
        forecast (_str_): variables to look at in CFS
        main_path (_str_): working path
        shp_name (_str_): name of file including extension
        url_add (_str_): url end point

    Returns:
        _xarray_: downloaded data as an xarray
    """
    
    if forecast == 'temperature':
        var = 'tmp2m' # temperature at 2m
    if forecast == 'precipitation':
        var = 'apcpsfc' # surface precipitation 
        
    # read bbox from shapefile
    _shp = gpd.read_file(Path(main_path / f'boundary_data/{shp_name}'))
    xmin, ymin, xmax, ymax = _shp.total_bounds
    
    # get data as xarray
    lat = (ymin,ymax)
    lon = (xmin,xmax)
    
    # # getting the data as an xarray
    log.info(f"\n --- \n Downloading and writing .nc file with the data\n --- \n")
    with xr.open_dataset(url_add) as ds:
        da = ds[var].sel(lat = slice(*lat), lon = slice(*lon)) 
    
    # save .nc file
    file_name = shp_name.split(".")[0] + '.nc'
    da.to_netcdf(Path(main_path / f'forecast_data/{file_name}'))
    
    return da

def data_tif(data_array, forecast, main_path, resolution):
    """create tif files from xarray

    Args:
        data_array (_type_): downloaded data as an xarray
        forecast (_type_): variables to look at in CFS
        main_path (_type_): working path
        resolution (_type_): data resolution as per CRS
    """
    
    log.info(f"\n --- \n Creating .tif files\n --- \n")
    
    if forecast == 'temperature':
        hour = 6
        da_daily = np.round(data_array.resample(time='24H')
                            .mean('time') - 273.1) # this is for temperature
        
    if forecast == 'precipitation':
        hour = 0
        da_daily = np.round(data_array.resample(time='24H')
                            .sum('time')) # this is for rainfall - 1 kg of rain water spread over 1 square meter of surface is 1 mm in thickness 
    
    # conver xarray to rioxarray - enable the creation of tif files
    da_daily.rio.write_crs("epsg:4326", inplace=True)

    # rename dimensions to avoid errors with rio
    da_daily = da_daily.rename({'lon': 'x','lat': 'y'})

    # Create list with the dates - this will be used to create .tif files
    lst_dates = da_daily.coords['time'].values
    
    print(lst_dates)
    
    # Create tif files with the forecast
    # It is one tif file per day
    for count, values in enumerate(lst_dates):
        print(f'Doing {np.datetime_as_string(values, unit="D")}')
        
        # select each day separately
        da_tif = da_daily.isel(time=slice(count, count + 1))
        
        print(da_tif)
        

        # # save xarray to .tif file
        # da_tif.rio.write_nodata(np.nan, inplace=True)
        da_tif.rio.to_raster(Path(main_path / f'forecast_data/{forecast}_gfs_{np.datetime_as_string(values, unit="D")}_{resolution}_{hour:02d}z.tif'))
        break

    log.info(f"\n --- \n The rasters have been created as expected \n --- \n")

    

#############################################################
# Logging to console
#############################################################
# Set log level to info
log = setup_logging()

# log.info("\n --- \n Downloading data from Climate Forecast System\n --- \n")

#############################################################
# COMMAND LINE UTILITIES
#############################################################
@click.command("Downloading data from Climate Forecast System")
@click.option("--res", 
              default='0p25', 
              help="The default value is 0p25 for more information look at"
              "https://climatedataguide.ucar.edu/climate-data/climate-forecast-system-reanalysis-cfsr")
@click.option("--clim_var", 
              default='precipitation', 
              help="If you need temperature then you need to specified it. Otherwise"
              "precipitation will be downloaded")
@click.option("--bndr", 
              help="Please enter the name of the boundary file including extension"
              "i.e. country_adm0.shp")


def cfs(res, clim_var, bndr):
    # build URL
    _url = url(res, clim_var)
    
    # # fetch data
    _data = fetch_data(clim_var, src_path, bndr, _url)
    
    # create .tif files
    data_tif(_data, clim_var, src_path, res)
    
    log.info(f"\n --- \n everything ran as expected!! \n --- \n {url}")
    
#############################################################
# PROCESS
#############################################################
    
if __name__ == "__main__":
    cfs()