This repository contains code to analyze Convective Outlooks, Storm Reports (and their associated PPH), and near-storm environmental ERA5 data. Existing code processes and summarizes convective outlooks, storm reports, and PPH. Future work will incorporate ERA5 data and perform further analysis with ML methods.

## End-to-end usage:

1. Download the following data into the `/raw_data` folder:

   * All six (hail, wind, and tornado, each with overall and sig datasets) PPH datasets from: [https://atlas.niu.edu/pperfect/BAMS/]() into `/raw_data/pph`
     * 1979-2022 PPH data has been used, newer data may be available
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
   * Before you run, `year_list` will need to be edited to match the year ranges of downloaded Convective Outlook datasets
   * This script also fixes a data issue in the mesonet outlooks dataset where most day three forecasts issued on the last day of a month between 2002-2019 are mistakenly labelled (in `ISSUE` and `EXPIRE` fields) as being for the first day of that month.
   * This script also identifies all dates for which there was a MDT or HIGH convective outlook issed, and saves a Convective Outlook `.shp`, PPH `.nc`, and storm report `.csv` valid on only these dates alongside the full saved datasets in the respective folders within `/data`. These datasets are not used any futher, though (since we create a more generalized way to pull out MDT+ days)
   * Typical running time: A few minutes
3. Run `gridize.ipynb` and `gridize2.ipynb`

   * This takes in the CO, PPH, and report data output by `load_data.ipynb` from `/data` and creates gridded netCDF files (usable by xarray) from outlook `.shp` and report `.csv` files. These `.nc` files are saved alongside the `.shp` and `.csv` files they were derived from. For each day: each outlook issued for that day is "gridized" by noting the implied probability of a storm occuring within 25 miles of each gridpoint, and reports are "gridized" by counting the number of storm reports within 25 miles of each gridpoint and noting whether or not any storm report occurred within 25 miles of each gridpoint.
   * Outlooks are only gridized beginning when day 3 outlooks are issued (since prior outlooks are purely categorical), which is the time period we are ultimately working with, but be warned if attempting to use for earlier time periods.
   * Typical running time: `gridize.ipynb` (for outlooks) takes a few days to run (and can be resumed partway through if needed). `gridize2.ipynb` takes a few minutes
4. Run `create_contingency.ipynb`

   This file creates the probabilistic contingency tables between probabilistic convective outlooks and pph. At each grid point, a, b, c, and d can be calculated from the forecast probability and PPH probability:

   |                                  | Observed Outcome | (PPH probability v) |
   | -------------------------------- | ---------------- | ------------------- |
   | Forecast (Outlook Probability p) | Yes (v)          | No (1-v)            |
   | Yes (p)                          | a = p * v        | b = p * (1-v)       |
   | No (1-p)                         | c = (1-p) * v    | d = (1-p) * (1-v)   |

   The values of a, b, c, and d are summed across all gridpoints for each date and hazard type (wind, hail, tornado, and all-hazard). That is, for each hazard type on each date, there is one total value for a representing the (expected) number of positive forecasts/positive outcomes, one total value b representing the (expected) number of positive forecasts/negative outcomes, etc. These values a, b, c, and d are saved to `data/contingency/contingency.nc`


   * Typicall running time: a few minutes
5. Run `track_displacement.ipynb`

   * This file uses the Farneback optical flow algorithm to find the spatial shift between outlooks and pph. The algorithm, originally used to track the movement of an object from one frame of a video to the next, produces a vector at each gridpoint (pixel) representing object motion. These vectors capture the displacement and deformation of an object (or in our case, storm probabilities). Some key interpretations are that vectors point a direction if storms generally occured that direction from where they were forecast, vectors are near zero where no storms were forecast or reported, and vectors diverge where storms are underforecast (and converge where overforecast). These vector fields are saved in `/data/displacement/displacements.nc`
   * These fields are calculated for all-hazard probabilities and each hazard-specific probability. For each day/hazard type, the following values are recorded at each gridpoint:
     * `x/y_flow`: The displacement, in along-grid directions and units of grid squares
     * `end_lon/lat`: The endpoint of the displacement vector in lat/lon coordinates, useful for plotting displacements with plt.arrow()
     * `e/n_flow`: The displacement, in cardinal directions with units of m
   * Additionally, average spatial shifts and divergences are calculated (for all hazards, Hail, Wind, and Tornadoes):
     * `E_SH[_H/W/T]` (East Shift): Average e_flow across all gridpoints, weighted by outlook probability (or PPH probability if outlook is zero).
     * `N_SH[_H/W/T]` (North Shift): Average n_flow is taken across all gridpoints, weighted by outlook probability (or PPH probability if outlook is zero).
     * `DIV[_H/W/T]` (Divergence): Average divergence in the x/y_flow field across all gridpoints, weighted by outlook probability (or PPH probability if outlook is zero).
   * Typical running time: about a day
6. Run `labelling.ipynb`

   * This reads in the CO, PPH, and report data output by `load_data.ipynb` from `/data` and adds the following variables (each date is associated with one value for each of these variables):

     * `MAX_CAT`: the highest categorical risk issued valid on that date (out of `['TSTM', 'MRGL', 'SLGT', 'ENH', 'MDT', 'HIGH']`)
     * `RAMP_UP`: the maximum increase in risk levels between any two convective outlooks valid for the date (e.g., if convective outlooks are issused with SLGT, MRGL, ENH, and SLGT risk, the ramp up is `2` (MRGL to ENH))
     * `RAMP_DOWN`: the maximum decrease in risk levels between any two convective outlooks valid for the date (e.g., if convective outlooks are issused with MRGL, HIGH, MDT, and SLGT risk, the ramp down is `3` (HIGH to SLGT))
     * `RAMP_CATEGORIES`: whether there is a ramp up, down, both, or neither for the given date
     * `SEASON`: meteorological season
     * `REGION`: One of: West, Midwest, Great Plains, Northeast, South, or NONE (if no storm reports on a given date). This is determined as the region (region boundaries defined [here](https://journals.ametsoc.org/view/journals/wefo/31/6/waf-d-16-0046_1.xml)) where total PPH (i.e. probability of at least one type of hazard occuring, given PPH probabilities for each hazard independently) is maximized
     * `REGION_M`: As above, but where total PPH is the max of each hazard-specific PPH (i.e. assuming dependence)
     * `LAT_NUM`: the latitude at which total PPH (assuming dependence) is maximized
     * `LON_NUM`: the longitude at which total PPH (assuming dependence) is maximized
     * `PPH_NUM`: The maximum PPH (assuming independence) at any one grid cell for the date
     * `PPH_CAT`: The categorical risk associated with the maximum PPH (assuming independence) at any one grid cell for the date (e.g. HIGH = 60)
     * `PPH_D_NUM`: The maximum PPH (assuming dependence) at any one grid cell for the date
     * `PPH_D_CAT`: The categorical risk associated with the maximum PPH (assuming dependence) at any one grid cell for the date (e.g. HIGH = 60)
     * `NUM_REPORTS_NUM`: The total number of severe storm reports on the date
     * `TOR_REPORTS_NUM`: The total number of tornado reports on the date
     * `WIND_REPORTS_NUM`: The total number of severe (>= 50 kt) thunderstorm wind reports on the date
     * `HAIL_REPORTS_NUM`: The toal number of severe (>= 1 in) hail reports on the date
     * `MAX_TORNADO_RATING`: The highset (E)F rating of a tornado on the date
     * `MAX_WIND_SPEED_NUM`: The highest severe thunderstorrm wind speed recorded on the date
     * `MAX_WIND_SPEED_CAT`: One of `'sig_severe'`, `'severe'`, or `'NONE'`; the severity of the strongest thunderstorrm wind speed recorded on the date
     * `MAX_HAIL_SIZE_NUM`: The largest hail size recorded on the date
     * `MAX_HAIL_SIZE_CAT`: One of `'sig_severe'`, `'severe'`, or `'NONE'`; the severity of the largest hail size recorded on the date
     * Accuracy of outlook. Verification of forecasts of this type are challenging, but possible metrics are SAL, Brier score, Wavelet analysis. To do so, gridded outlook and report datasets from step 3 are opened and used, and a variety of verification metrics have been created.

       * Direct metrics:
         * `BS_NUM`: the brier score for all grid points on date between the outlook probability of seeing a storm report within 25 miles of a point and whether that actually occurred.
         * `RMSE_NUM`: the RMSE between the outlook probability of seeing a storm report within 25 miles and the PPH probability
         * `NEIGH_NUM`: the MSE between outlook probability of seeing a storm report within 25 miles and the true probability, as given by the fraction of the 5x5 nearest gridpoints that had a storm report within 25 miles.
       * Metrics Using Probabilistic Contingency Tables: As described in create_contingency.ipynb, the (expected) contingency table values a, b, c, and d are calculated for each day/hazard type. From these values, the following statistics are calculated: `_H/W/T` represents hazard type, all followed by `_NUM`
         * `PC` (Percent Correct): (a + d) / (a + b + c + d)
         * `POD `(Probability of Detection): a / (a + c)
           * The expected mean probability of any [hail/wind/tornado] hazard occurance in the Day 1 outlook across grid squares for which there was a verifying event within 25 miles
           * = 1 - FOM (Frequency of Misses)
         * `FAR` (False Alarm Ratio): b / (a + b)
           * The expected fraction of grid squares for which any [hail/wind/tornado] hazard did not occur within 25 miles, weighted by the Day 1 outlook probability.
           * = 1 - FOH (Frequency of Hits)
         * `POFD` (Probability of False Detection): b / (b + d)
           * The expected mean probability of any [hail/wind/tornado] hazard occurance in the Day 1 outlook across grid squares for which there was NOT a verifying event within 25 miles
           * Note that FOM and POFD are the non-squared (unless you set `squared = True`) contributions to the BS by at verifying and non-verifying grid squares respectively.
           * = 1 - PCF (Percent Correct Rejections)
         * `DFR` (Detection Failure Ratio): c / (c + d)
           * The expected mean PPH probability where no storms were forecast.
           * = 1 - FOCN (Frequency of Correct Null Forecasts)
         * `CSI` (Critical Success Index): a / (a + b + c)
           * Ranges from zero to 1, where 1 is best performance
         * `Bias`: (a + b) / (a + c)
           * Whether storms were underforecast (<1) or overforecast (>1)
         * `ETS` (Equitable Threat Score): (a - Bias/n) / (a + b + c - Bias/n)
           * Like CSI, accounting for bias
         * `TSS` (True Skill Score): (ad - bc) / ((a + c)(b + d))
       * Metrics using optical flow displacement vectors (only 2002- for H and W):
         * `E_SH[_H/W/T]` (East Shift): Average eastward (negative is westward) shift from all-hazard [hail/wind/tornado] outlooks to pph using Farneback optical flow (m). Average is taken across all gridpoints, weighted by outlook probability (or PPH probability if outlook is zero).
         * `N_SH[_H/W/T]` (North Shift): Average northward (negative is southward) shift from all-hazard [hail/wind/tornado] outlooks to pph using Farneback optical flow (m). Average is taken across all gridpoints, weighted by outlook probability (or PPH probability if outlook is zero).
         * `DIV[_H/W/T]` (Divergence): Average divergence in the flow field of all-hazard [hail/wind/tornado] outlooks to pph using Farneback optical flow. Average is taken across all gridpoints, weighted by outlook probability (or PPH probability if outlook is zero).
     * characterization by environmental data: to be added
     * The modified datasets are also saved in `/data`, with `labelled_` as a prefix on the filename
     * When functions to add new labels are added, this file can be rerun with `labelled = True` to begin with already-labelled datasets and only run the additon of desired new labels. If doing so, the pph data will be saved as `labelled_pph2.nc` (since `labelled_pph.nc` is in use). You need to manually delete `labelled_pph.nc` and then rename `labelled_pph2.nc` as labelled_pph2.nc once this file is done running.
   * Running Time: ~20 minutes to read in data. Most labels are instant to ~10 minutes to add, but regions takes a few hours.
7. To be completed: downloading and incorporating ERA5 data associated with locations and dates of interest
8. Further steps: ML analysis of all this data

## Offshoots/Products:

* Especially interesting figures are copied into `/plots/results`
* `mcax.ipynb` does MCA analysis between gridded PPH and day-1 outlooks for each of the three hazard types
* `explore_subsets.ipynb` produces 1D histograms for each label and 2D historgrams for each pair of labels (as created in `labelling.ipynb`). This is done for all dates (with concurrent outlook, PPH, and report data; 1987-2022), dates with `MAX_CAT` of MDT or HIGH, dates since MRGL and ENH were added as categorical risks, and dates with `MAX_CAT` of MDT or HIGH since MRGL and ENH were added as categorical risks. Plots are saved in [/plots/label_distributions](https://github.com/milesepstein13/severe-thunderstorm-analysis/tree/master/plots/label_distributions).
  * Also can create a timeseries of any numerical label if desired.
  * Also creates displacement plots [DESCRIBE]
  * Running Time: About 20 minutes to read in data, then about 20 minutes more to plot, scaling as n^2 with number of labels
* `explore_date.ipynb` plots the Day 3, Day 2 7z, Day 2 17z, and Day 1 outlooks, the PPH, and reports on maps, along with printing and saving to a `.txt` file all labels, for any dates requested. The results are saved in [/plots/daily/[datestring]](https://github.com/milesepstein13/severe-thunderstorm-analysis/tree/master/plots/daily)
  * Running time: seconds per requested date after reading datasets
* `create_performance_diagrams.ipynb` adsfa
  * [DESCRIBE]
* `clustering.ipynb` clusters all days with various methods (knn, k-means, pca) after labelling. First, a mxn matrix is created, where m is the number of samples (dates of interest, in our case MDT/HIGH days since 2002) and n is the dimensionality (in our case the number of numerical or ordinal labels). This data is standardized before any PCA or clustering
  * PCA: PCA is run on this data matrix, and the fraction of variance explained by each PC and the components of the first few PCs are printed
  * Clustering: `cluster_partial()` clusters the dataset in only the `cluster_vars` dimensions with each clustering algorithm in `clustering_algorithms`, returning a dict (by clustering algorithms) of lists of the portions of the entire dataset in each cluster. Then, for the clusters created by each method, `summarize_clusters` plots the cluster centers on a map (with some higher-dimension information encoded in plot point characteristics), creates distribution 2d-historgams for each variable (by cluster number), and/or saves to text the centers of each cluster. Plots can be shown in console or saved in `/plots/clustering/... `
  * Running Time: a few minutes after reading datasets

## Notes/Standards/Assumptions:

* Functions are mostly modularized and availible in the `utils` files. Some especially useful functions are:
  * `read_datasets` in `utils_filters.py` reads in the outlooks, PPH, and reports datasets, use `mod_string` to read different datasets:
    * `mod_string = 'all'`  loads post-`load_data.ipynb`
    * `mod_string = 'labelled'` loads post-`labelling.ipynb`
* We only consider the Day 3 outlook (08z), both Day 2 outlooks (07z and 17z), and the first (06z) Day 1 outlook. Later Day 1 outlooks are not considered because these forecasts are issued after the beginning of the full verification period.
* We only consider the categorical (as opposed to hazard-specific) outlooks. Numerical probabilities for any hazard are available directly on Days 3 and 2 (pre- 02/01/2020), but must be constructed from hazard-specific probabilities on Day 1 and pre-02/01/2020 Day 2 by taking the max of any hazard-specific probability at each gridpoint.
* Dates when forecast practices changed:
  * MRGL and ENH were added as categorical risks: October 23, 2014
  * Day 3 forecasts first issued '200203300000'
  * Day 2 7z forecasts first issued '199707100000'
  * Day 2 17z forecasts first issued '199504040000'
* All gridded datasets are on the same grid as used in PPH datasets, which is stated to be the [NCEP 211 Grid](https://www.nco.ncep.noaa.gov/pmb/docs/on388/tableb.html#GRID211), although I have difficulty exactly recreating this grid and have only used the grid directly from the PPH datasets.
* Marine hail/wind and waterspouts are not included.
