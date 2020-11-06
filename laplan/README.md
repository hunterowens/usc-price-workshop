# README for laplan package

---

The `laplan` package is created for the Los Angeles Department of City Planning. There are 3 sub-modules, each of which can be used independently.

The sub-modules that allow users to clean up zoning data from ZIMAS, entitlement data from PCTS, and Census data from the American Community Survey. 

1. [Getting Started](#getting-started)
1. [Zoning](#zoning)
1. [PCTS](#pcts)
1. [Census](#census)
    * [Cleaning ACS Data](#cleaning-acs-data)
    * [Three Types of ACS Tables](#three-types-of-acs-tables)
    * [General Functions](#general-functions)
    * [Income Functions](#income-functions)


## Getting Started
This package is installed in our Docker image.

To install it into another GitHub repo: 
```
pip install "git+https://github.com/CityOfLosAngeles/planning-entitlements#subdirectory=laplan" 

# Ways to use within notebook/script
import laplan
import laplan.census
from laplan import census 
```

## Zoning
The sub-module is `zoning.py`. Zoning data comes from ZIMAS, and is publicly available on the [GeoHub](http://geohub.lacity.org/datasets/zoning). Planning's [Guide to Zoning String](https://planning.lacity.org/zoning/guide-current-zoning-string) shows that the zoning string is made up of component parts. 

The zoning string contains information about prefix on (Q)ualified or (T)entative zone classifications, zone class, the height district, (D)evelopment limits, and specific plans and overlays applicable. 

The `ZoningInfo` dataclass takes a zoning string and returns any or all of the components as a new dataframe. 

Ex 1: Return all the components
```
import laplan 

parsed_col_names = ['Q', 'T', 
                    'zone_class', 'specific_plan', 
                    'height_district', 'D', 'overlay']

# ZONE_CMPLT is the column to be parsed.
def parse_zoning(row):
    try:
        z = laplan.zoning.ZoningInfo(row.ZONE_CMPLT)
        return pd.Series([z.Q, z.T, 
                            z.zone_class, z.specific_plan, 
                            z.height_district, z.D, z.overlay], 
                            index = parsed_col_names)
    # If it can't be parsed, return either a failed or blank string
    except ValueError:
        return pd.Series(['failed', 'failed',  
                            'failed', 'failed', 
                            'failed', 'failed', ''], 
                            index = parsed_col_names)

parsed = df.apply(parse_zoning, axis = 1)
df = pd.concat([df, parsed], axis = 1)
```

| ZONE_CMPLT | Q | T | zone_class | height_district | D | overlay |
| ---| --- | --- | --- | --- | --- | --- | --- |
| C2-1-SP| False | False | C2 | 1  | False | [SP]
| [Q]C1.5-1VLD-RIO | True | False | C1.5 | 1 | True |  [RIO] 


Ex 2: Return just one of the components

```
parsed_col_names = ['zone_class']

def parse_zoning(row):
    try:
        z = laplan.zoning.ZoningInfo(row.ZONE_CMPLT)
        return pd.Series([z.zone_class], 
                         index = parsed_col_names)
    except ValueError:
        return pd.Series(['failed'], 
                         index = parsed_col_names)

    
parsed = df.apply(parse_zoning, axis = 1)
```
## Census
The sub-module is `census.py`. 

### Cleaning ACS Data

The American Community Survey (ACS) data for various years, topics, and geographies all follow a similar pattern. Browse the [Census Data Catalog](https://data.census.gov/cedsci/) or [Census API](https://api.census.gov/data.html) to get the tables needed. 

The scripts to download clean Census data are provided below. These scripts can be adapted to include other Census tables; our project dealt with a limited subset of ACS tables for census tracts.

1. [Download Census data](https://github.com/CityOfLosAngeles/planning-entitlements/blob/master/src/C1_download_census.R)
1. [Clean Census data, part 1](https://github.com/CityOfLosAngeles/planning-entitlements/blob/master/src/C2_clean_census.py)
1. [Clean Census data, part2](https://github.com/CityOfLosAngeles/planning-entitlements/blob/master/src/C3_clean_values.py)
1. [Subset Census](https://github.com/CityOfLosAngeles/planning-entitlements/blob/master/src/C4_subset_census.py)

The resulting table from these scripts has this form. At minimum, the table **MUST** have columns `['GEOID', 'year', 'table', 'main_var', 'second_var', 'num']`, in order to use the functions in `census.py`. These necessary columns have stars next to the column name in the table below.

| Column | Description | 
| --- | --- | 
| GEOID * | `str` preferable, but `numeric` works, geographic identifier for county, tract, block group, etc. 
| variable | `str`, the original Census variable name, such as `B01001_001` or `S0801_C01_001`. This is tagged as more human-readable columns, `main_var` and `second_var`. 
| year * | `numeric`, year associated with the table
| table * | `str`, a human-readable name given to the table in `C2_clean_census.py`. Ex: For `S0801_C01_001`, the table is `S0801`, and is `commute`.
| main_var * | `str`, a human-readable name that captures what the variable is mainly about. Ex: For `S0801_C01_001`, the `C01` portion what tags `main_var` as `workers`. `C02` would be `male`, `C03` would be `female`, etc. 
| last2 | `str`. The last 2 digits of `variable`.
| second_var * | `str`, a human-readable name that captures what the last two digits from the variable. Ex: For `S0801_C01_001`, the last 2 digits is `01` and designates `total`.
| new_var * | `str`, combines `main_var` and `second_var`. Ex: For `S0801_C01_001`, this value is `workers_total`. 
| pct | `numeric`, holds percent values, ranging from 0-1. 
| num * | `numeric`, holds count values. The method of standardizing across tables is to have one column holding counts and one column holding percents, and filling in all the values for all tables. 

### Three Types of ACS Tables

ACS tables always provide a summary statistic with a `total`, the denominator, representing the universe from which this summary statistic is derived. This universe can be the entire population, the population 16 years and up, workers 16 years and up, etc. 

When downloading ACS tables through the Census API, remember these things:
* **Know the *unit*** of the numerator and denominator.
* **Does the unit change across years?** Sometimes, the table will undergo a change; it will change from reporting count values to percent values after a certain year.
* **Are variables are stable in reporting the same information?** Particuarly, if the table has undergone a change, new columns might be added, such as `C02`. The *same* information might be found in `C01` from 2010-2013, and then in `C02` from 2014-onward. 

We broadly group ACS tables into 3 types in our data cleaning process:
1. **Count tables**: counts are provided for numerator and denominator. Ex: # households that fall into particular income range, as well as the total # households overall within a census tract (or any other geography)
1. **Percent tables**: percent for numerator and count for denominator. Ex: 15 for people with less than HS education (which is 15%, not a count of 15 people), and 1,000 households in census tract. These need to be converted to counts from percents using the denominator.
1. **Dollar tables**: median household income or aggregate income, inflation-adjusted for each year. These tables separate, particularly because median household income is a tricky topic. Users beware! Do not calculate summary statistics from median income values (average median income is meaningless); only report values as is. Users should think carefully about what the ACS is reporting and how to use it meaningfully in analysis.

### General Functions

The main function is `transform_census_percent`, which uses 3 sub-functions, each of which can be used on its own. `transform_census_percent` takes a long, cleaned Census df, grabs one or more columns to aggregate, and reshapes the df to be wide. [Example notebook](https://github.com/CityOfLosAngeles/planning-entitlements/blob/master/notebooks/B1-census-tract-stats.ipynb).


`transform_census_percent()`: this function subsets the Census df for a particular table and year, grabs the relevant rows, aggregates them, renames the aggregated row, and then calculates the percent. The specifics of the function are best illustrated in an example.

```
import laplan

commute_group = [
    "workers_transit", 
    "workers_walk", 
    "workers_bike"
]

# Grab the 2018 commute table for all workers
# Aggregate transit, walk and bike
# Rename aggregated group as "non_car_workers"
# Calculate percent (non_car_workers / workers_total)
# Numerator is non_car_workers
# Denominator is workers_total
# Rename this new column "pct_non_car_workers"

laplan.census.transform_census_percent(
    "commute", 
    2018, 
    "workers", 
    commute_group, 
    "non_car_workers", 
    "non_car_workers", 
    "workers_total"
)
```

Cleaned, long Census df:
| GEOID | variable | year | table | main_var | second_var | new_var | num |
| ---| --- | --- | --- | --- | --- | --- | --- |
| A | S0801_C01_001 | 2018 | commute | workers  | total | workers_total| 1000
| A | S0801_C01_009 | 2018 | commute | workers  | transit | workers_transit | 50
| A | S0801_C01_010 | 2018 | commute | workers  | walk | workers_walk | 10
| A | S0801_C01_011 | 2018 | commute | workers  | bike | workers_bike | 20

`transform_census_percent` returns a wide df that looks like:

| GEOID | non_car_workers | workers_total | pct_non_car_workers | 
| ---| --- | --- | --- |
| A | 80 | 1000 | 0.08 | 


The sub-functions can be used individually, and **should be used to construct reshaped income and race/ethnicity tables**. 
* Median household income: `subset_census_table` will return those values needed. No aggregation should be done!
* Households by income ranges: this table is used in conjunction with the `income_percentiles` function to re-calculate median household incomes.
* Race/ethnicity: use sub-functions because race/ethnicity groups can sum over 100%; race and ethnicity are *not* mutually exclusive.


`subset_census_table(table, table_name, year, main_var)`: subsets our cleaned, long Census df and grabs a particular table, year, and main_var. 

```
# census_df is a df of 
# cleaned, long Census data described above.

# 2018 commute mode table
subset_census_table(
    census_df, 
    "commute", 
    2018, 
    "workers"
)
```

`aggregate_group(df, aggregate_me, name="aggregated_group")`: this function takes the df from `subset_census_table` and aggregates several rows into one. If no aggregation is needed, simply provide a list of 1. The list is made up of value(s) from new_var.

```
# To aggregate 3 groups:
# Rename new_var to "non_car_workers"
commute_group = [
    "workers_transit", 
    "workers_walk", 
    "workers_bike"
]

aggregate_group(
    df, 
    commute_group, 
    "non_car_workers"
)

# To aggregate 1 group 
# Rename new_var to "zero_veh_workers"

vehicle_group = ["workers_veh0"]
aggregate_group(
    df, 
    vehicles_group, 
    "zero_veh_workers"
)
```

`make_wide(df, cols)`: this function takes reshapes the df from long to wide, or takes rows and pivots them to be columns. Cols is a list of values in from new_var.

```
reshape_me = ['non_car_workers', 'workers_total']

make_wide(df, reshape_me)
```

### Income Functions

The income functions are `make_income_range_wide` and `income_percentiles`. 

`make_income_range_wide(df, year, main_var="total")`: subsets the long, cleaned Census df and grabs the `incomerange` table for a particular year and main_var. The default main_var is `total`, which is all households, rather than a specific race or ethnicity.

```
# 2018 all households by income bins 
make_income_range_wide(
    census_df,
    2018,
)

# 2018 white households by income bins
make_income_range_wide(
    census_df, 
    2018, 
    "white"
)
```

`income_percentiles`: takes a df and returns the estimated income percentiles. This can be used to re-calculate the median household income (50th percentile). The households are aggregated done to a larger geographic area after `make_income_range_wide`, after which the [median household income is re-calculated over this larger geographic area](http://www.dof.ca.gov/Forecasting/Demographics/Census_Data_Center_Network/documents/How_to_Recalculate_a_Median.pdf). If no aggregation is needed, then using the median household income table is sufficient in itself. The function returns percentiles in **thousands of dollars**, so multiple by 1,000 to get the result in dollars. 

```
# Calculate 25th, 50th, and 75th percentiles.
iqr_df = (df.apply(
        lambda r: 
        pd.Series(laplan.census.income_percentiles(
            r, [25,50,75]),
            dtype="float64"),
            axis=1,
    ).rename(
        columns={0: "Q1", 
                1: "Q2",   
                2: "Q3"})
)
```

`iqr_df` looks like (note: units are thousands of dollars): 
| GEOID | Q1 | Q2 | Q3 
| ---| --- | --- | --- | 
| A | 30.5 | 55.7 | 82.6 
| B | 40.5 | 58.7 | 90.6 