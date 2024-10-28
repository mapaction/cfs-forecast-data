# Getting data from Global Forecast System - NOAA
This script is used to access data directly from the GFS system using the information stored in the GrADS Data Server.

The Global Forecast System (GFS) is a National Centers for Environmental Prediction (NCEP) weather forecast model that generates data for dozens of atmospheric and land-soil variables, including temperatures, winds, precipitation, soil moisture, and atmospheric ozone concentration. The system couples four separate models (atmosphere, ocean model, land/soil model, and sea ice) that work together to accurately depict weather conditions. More information can be accessed here: https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast

## Working with the script

### Libraries needed:

- xarray
- geopandas
- numpy
- datetime
- pathlib
- logging
- click
- warnings


### Runnin the Script
This script runs in a python terminal and the following command needs to be used:

- The boundary of the AOI needs to be saved as a shapefile under the *boundary_data* folder.

```python 
python CFS_climateForecastSystemData.py --clim_var=<precipitation or temparature> --bndr=<boundary file name>
```
For help with the script you can run

```python 
python CFS_climateForecastSystemData.py --help
```
- The final output of the script will be stored in the *forecast_data*