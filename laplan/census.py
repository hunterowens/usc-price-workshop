"""
Utilities for dealing with census data.
"""
# ---------------------------------------------------------------------------------------#
# Census functions
# ---------------------------------------------------------------------------------------#

def transform_census_percent(
    table,
    table_name,
    year,
    main_var,
    aggregate_me,
    aggregated_row_name,
    numer,
    denom,
):
    """
    Take long Census df, optionally aggregate some categories,
    and calculate the percents. 
    Ex: % renter, % white

    Parameters
    ==================
    table: pandas.DataFrame, ACS data as a long df.
    table_name: str
    year: numeric
    main_var: str
            based on main_var column and pick only one for which the processed df is
            derived from
    aggregate_me: list
            a list of new_var groups to aggregate into 1 group
    aggregated_row_name: str
            will be new name for this aggregated group
    numer: str
            based on new_var column
    denom: str
            based on new_var column
    """
    df = subset_census_table(table, table_name, year, main_var)

    df2 = aggregate_group(df, aggregate_me, name=aggregated_row_name)

    cols = [aggregated_row_name, denom]
    df3 = make_wide(df2, cols)

    new_var = f"pct_{aggregated_row_name}"

    df3 = df3.assign(new=df3[numer] / df3[denom],).rename(columns={"new": new_var})

    return df3


"""
Sub-functions
This most straightforward way to reshape from long to wide
Use number values, not percents, we can always derive percents later on if we need.
If we're aggregating to geographies that involve slicing parts of tracts,
we need numbers, not percents.
"""

def subset_census_table(df, table_name, year, main_var):
    """
    Given an ACS table, subset it by variable and year.
    The ACS table must have these 7 columns at minimum:
        GEOID, table_name, year, main_var, second_var, new_var, num 

    table: pandas.DataFrame, the ACS table as a long df.
    table_name: str, such as "income" or "population".
    year: numeric, 2010-2018.
    main_var: str
        Only one value from the main_var column may be given.
    """
    cols = ["GEOID", "new_var", "num"]
    df = df[(df.year == year) & (df.table == table_name) & (df.main_var == main_var)][
        cols
    ]
    return df


def make_wide(df, cols):
    """
    Pivot an ACS table.
    This function takes rows and pivots them to be columns.

    df: str
    cols: list. 
        One or more values from the new_var column may be given as a list.
        This function takes those values (rows), reshapes, and returns 
        them as columns in a new df.
    """
    return (
        df[df.new_var.isin(cols)]
        .assign(num=df.num.astype("Int64"))
        .pivot(index="GEOID", columns="new_var", values="num")
        .reset_index()
        .rename_axis(None, axis=1)
    )


def aggregate_group(df, aggregate_me, name="aggregated_group"):
    """
    Aggregates several rows into one row.

    df: str
    aggregate_me: list. 
        One or more values from the new_var column may be given as a list.
        This function takes those values (rows), aggregates them, and 
        returns one row that is the sum.
        Ex: commute mode table provides counts for various commute modes.
            One might want to combine public transit and biking commute modes together.
    name: str. This is the name of the new aggregated group.
        Ex: The sum of public transit and biking commute modes 
            will be named "sustainable_transport".
    """
    df = (
        df.assign(
            new_var2=df.apply(
                lambda row: name
                if any(x in row.new_var for x in aggregate_me)
                else row.new_var,
                axis=1,
            )
        )
        .groupby(["GEOID", "new_var2"])
        .agg({"num": "sum"})
        .reset_index()
        .rename(columns={"new_var2": "new_var"})
    )

    return df


# ---------------------------------------------------------------------------------------#
# Income functions
# ---------------------------------------------------------------------------------------#

CENSUS_INCOME_RANGES = [
    "lt10",
    "r10to14",
    "r15to19",
    "r20to24",
    "r25to29",
    "r30to34",
    "r35to39",
    "r40to44",
    "r45to49",
    "r50to59",
    "r60to74",
    "r75to99",
    "r100to124",
    "r125to149",
    "r150to199",
    "gt200",
    "total",
]

def make_income_range_wide(census_table, year, main_var="total"):
    """
    Pivot the incomerange table from long to wide.
    This needs to be done before calculating percentiles.

    Parameters
    ==========
    census_table: pandas.DataFrame
        The long, cleaned Census table.

    year: numeric

    main_var: str
        Value from the main_var column that designates which 
        race/ethnicity the ACS table is for, such as, "white" or "asian".
        Defaults to "total"

    Returns
    =======
    A wide df of number of households within each income range bin.
    """
    df = subset_census_table(
            census_table, 
            "incomerange", 
            year, 
            main_var
        )
    
    df = df.pivot(index="GEOID", columns = "new_var", values = "num")
    df.columns.name = ""
    df = df.reset_index()
    
    integrify_me = list(df.columns)
    integrify_me.remove("GEOID")
    
    df[integrify_me] = df[integrify_me].astype("Int64")
    
    return df


def income_percentiles(row, percentiles, prefix="total"):
    """
    Estimate income percentiles from counts in the census income ranges.

    Parameters
    ==========
    row: pandas.Series
        A series that contains binned incomes in the ranges given by
        CENSUS_INCOME_RANGES.

    percentiles: List[float]
        A list of percentiles (from zero to 100) for which to estimate values.

    prefix: str
        A prefix for the income range columns (e.g., census-indicated race).
        Defaults to "total"

    Returns
    =======
    A list of estimated income percentiles of the same length as percentiles,
    in thousands of dollars.
    """

    # Edges of the reported income bins, in thousands of dollars
    bins = [0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 75, 100, 125, 150, 200]
    # Iterator over percentiles
    p_it = iter(percentiles)
    # Final values for percentiles
    values = []
    # Initialize current percentile and an accumulator variable
    curr = next(p_it)
    acc = 0
    # The total count for the tract
    total = row[f"{prefix}_total"]
    if total <= 0:
        return values
    for i, b in enumerate(bins):
        # Compute the label of the current bin
        if i == 0:
            label = f"{prefix}_lt{bins[i+1]}"
        elif i == len(bins) - 1:
            label = f"{prefix}_gt{b}"
        else:
            label = f"{prefix}_r{b}to{bins[i+1]-1}"
        # Estimate the value for the current percentile
        # if it falls within this bin
        while (acc + row[label]) / total > curr / 100.0:
            frac = (total * curr / 100.0 - acc) / row[label]
            lower = b
            upper = bins[i + 1] if i < (len(bins) - 1) else 300.0
            interp = (1.0 - frac) * lower + frac * upper
            values.append(interp)
            try:
                curr = next(p_it)
            except StopIteration:
                return values
        # Increment the accumulator
        acc = acc + row[label]
    return values


