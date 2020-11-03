# usc-price-workshop
workshop for USC price students around build data driven policy briefs.

## simulation exercise 

This workshop consists of a simulation exercise where you will develop data-driven policy and planning briefs for a theoretical LA based state lawmaker. You are charged with coming up with and negiotating a bill to solve the housing crisis. 

Each group will be in charge of proposing a theoretical state level housing policy change. For example, you could propse something like last sessions [SB 1120](https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=201920200SB1120) or [AB 68](https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=201920200AB68)

## getting start 
To start, fork this repo and name your project.

## datasets 
All data is provided using an [Intake Catalog](https://intake.readthedocs.io/en/latest/catalog.html). We additionally provided interfaces to the City of LA [open data](http://data.lacity.org) and [geohub](http://geohub.lacity.org) using the [intake-dcat](https://github.com/cityoflosangeles/intake-dcat) library. The main datasets are

### Core 
1) `county_parcels`: All LA County Parcels 2006-2019, including joined GEOID10 for the census tract and last year it existed. 

1) `zoning_parsed`: Using the `laplan` utlity pacakge, we parsed the `zoning` file on the geohub so that you can break apart the zone strings (stuff like `R1-CDO-RIV` in consistuient parts using regular expressions. 

### Aux 
1) `metro_bus_stops`: in case you want to propose a transit orient policy. 

1) `metro_rail_lines`: Metro rail lines 

1) `metro_rail_stations`: Metro rail stops, points, not polygons 

1) `metro_rapid_bus_lines`: Metro Rapid Buses 

1) `metrolink_routes`: Metrolink routes 

### Census Data 

No data driven analysis is really complete without using American Community Survey data. We've cleaned and parsed some ACS data for you, to see the cleaning scripts see `notebooks`. 

1) `census_analysis_tables`: 

1) `census_cleaned`: census tables clean to outcomes of intrestes. use the analysis table for hte main data, this is a subset. 

### Loading data 

To load any data, simply run 

```python 
# NB you can call the dataset whatever you want
census_df = catalog.census_cleaned_read()
```

or 

```python
gdf = catalog.metro_rail_lines.read()
```

To load data from one of the city's open data portals, you can take a look at this [demo notebook](https://github.com/CityOfLosAngeles/intake-dcat/blob/master/examples/demo.ipynb). 

## submitting your work 
To submit your work, commit the updated policy branch and send us the link on github.  

## run on binder / running locally
If you have docker / docker-compose installed, you can simiply run 

`docker-compose up` from the project root. Otherwise, you  can use binder

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/hunterowens/usc-price-workshop/main)
