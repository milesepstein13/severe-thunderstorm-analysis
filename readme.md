This repository contains code to analyze Convective Outlooks, Storm Reports (and their associated PPH), and near-storm environmental ERA5 data. Existing code processes and summarizes convective outlooks, storm reports, and PPH. Future work will incorporate ERA5 data and perform further analysis with ML methods.

## End-to-end usage:

1. Download the following data into the `/raw_data` folder:
   * All six (hail, wind, and tornado, each with overall and sig datasets) PPH datasets from: [https://atlas.niu.edu/pperfect/BAMS/]() into `/raw_data/pph`
     * 1979-2019 PPH data has been used, newer data may be available
   * Each year's storm report data from: [https://www.ncdc.noaa.gov/stormevents/ftp.jsp]() into `/raw_data/storm_reports`
     * 1950-2023 Storm Report data has been used, newer data may be available
   * Day 1-3 Convective Outlooks as 'Cake Layers' from: [https://mesonet.agron.iastate.edu/request/gis/outlooks.phtml]() into `/raw_data/outlooks`. Download size may be limited, so data may need to be downloaded in several multi-year chunks (each beginning at 00:00Z Jan 1 and ending at 23:59Z Dec 31)
     * 1989-2023 Convective Outlooks have been used, newer data may be available
2. Run `load_data.ipynb`
   * This reads in the downloaded CO, PPH, and report data from `/raw_data` and compiles the many files into:

     * 2 `.shp` files containing all Convective Outlooks (since there were too many to save as one file), saved into `/data/outlooks`
     * 1 `.nc` file containing all PPH, saved into `data/pph`
     * 1 `.csv` file containing all storm reports, with only the columns of potential interest, saved into `/data/storm_reports`
   * A variable is added to each of these files identifying each CO/PPH/report with the valid date formatted as `'yyyymmdd0000'` for ease of analysis across datasets.
   * `year_list` will need to be edited to match the year ranges of downloaded Convective Outlooks
   * This script also identifies all dates for which there was a MDT or HIGH convective outlook issed, and saves a Convective Outlook `.shp`, PPH `.nc`, and storm report `.csv` valid on only these dates alongside the full saved datasets in the respective folders within `/data`. These datasets are not used any futher, though (since we create a more generalized version later on)
3. Run `labelling.ipynb`
   * This reads in the CO, PPH, and report data output by `load_data.ipynb` from `/data` and adds the following variables (each date is associated with one value for each of these variables):
     * `MAX_CAT`: the highest categorical risk issued valid on that date (out of `['TSTM', 'MRGL', 'SLGT', 'ENH', 'MDT', 'HIGH']`)
     * `RAMP_UP`: the maximum increase in risk levels between any two convective outlooks valid for the date (e.g., if convective outlooks are issused with SLGT, MRGL, ENH, and SLGT risk, the ramp up is `2` (MRGL to ENH))
     * `RAMP_UP`: the maximum decrease in risk levels between any two convective outlooks valid for the date (e.g., if convective outlooks are issused with MRGL, HIGH, MDT, and SLGT risk, the ramp down is `3` (HIGH to SLGT))
     * `RAMP_CATEGORIES`: whether there is a ramp up, down, both, or neither for the given date
     * `SEASON`: meteorological season
     * `REGION`: One of: West, Midwest, Great Plains, Northeast, South, or NONE (if no storm reports on a given date). This is determined as the region (region boundaries defined [here](https://journals.ametsoc.org/view/journals/wefo/31/6/waf-d-16-0046_1.xml)) where total PPH (i.e. probability of at least one type of hazard occuring, given PPH probabilities for each hazard independently) is maximized
     * accuracy of forecast: to be added
     * characterization by environmental data: to be added
   * The modified datasets are also saved in `/data`, with `labelled_` as a prefix on the filename
   * When functions to add new labels are added, this file can be rerun with `labelled = True` to begin with already-labelled datasets and only run the additon of desired new labels.
4. To be completed: downloading and incorporating ERA5 data associated with locations and dates of interest

## Offshoots:

* `mcax.ipynb` does MCA analysis between gridded PPH and day-1 outlooks for each of the three hazard types
* `explore_subsets.ipynb` produces 1D histograms for each label and 2D historgrams for each pair of labels (as created in `labelling.ipynb`). This is done for all dates (with concurrent outlook, PPH, and report data; 1987-2019), dates with `MAX_CAT` of MDT or HIGH, dates since MRGL and ENH were added as categorical risks, and dates with `MAX_CAT` of MDT or HIGH since MRGL and ENH were added as categorical risks. Plots are saved in [/plots/label_distributions](https://github.com/milesepstein13/severe-thunderstorm-analysis/tree/master/plots/label_distributions).

## Notes:

* Functions are mostly modularized and availible in the `utils` files. Some especially useful functions are:
  * `read_datasets` reads in the outlooks, PPH, and reports datasets, either post-`load_data.ipynb` or post-`labelling.ipynb` (by setting argument `labelled = True`)
* We only consider the Day 3 outlook (08z), both Day 2 outlooks (07z and 17z), and the first (06z) Day 1 outlook.
* We only consider the categorical (as opposed to hazard-specific) outlooks.
* Date when MRGL and ENH were added as categorical risks: October 23, 2014
