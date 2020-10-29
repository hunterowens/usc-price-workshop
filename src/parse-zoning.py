#!/usr/bin/env python
# coding: utf-8

# # Clean ZIMAS / zoning file
# * Dissolve zoning file so they are multipolygons
# * Use parser in `laplan.zoning` to parse ZONE_CMPLT
# * Manually list the failed to parse observations and fix
# * Use this to build crosswalk of height, density, etc restrictions


import geopandas as gpd
import intake
import numpy as np
import os
import pandas as pd
import laplan
import shutil

catalog = intake.open_catalog("./catalog.yml")

# Dissolve zoning to get multipolygons
# File is large, but we only care about unique ZONE_CMPLT, which need to be parsed
zones = catalog.zoning.read()
zones = zones[['ZONE_CMPLT', 'ZONE_SMRY', 'geometry']].assign(
    zone2 = zones.ZONE_CMPLT
)

df = zones.dissolve(by='zone2').reset_index(drop=True)
df.head()


print(f'# obs in zoning: {len(zones)}')
print(f'# unique types of zoning: {len(df)}')


parsed_col_names = ['Q', 'T', 'zone_class', 'specific_plan', 'height_district', 'D', 'overlay']

def parse_zoning(row):
    try:
        z = laplan.zoning.ZoningInfo(row.ZONE_CMPLT)
        return pd.Series([z.Q, z.T, z.zone_class, z.specific_plan, z.height_district, z.D, z.overlay], 
                         index = parsed_col_names)
    except ValueError:
        return pd.Series(['failed', 'failed', 'failed', 'failed', 'failed', 'failed', ''], 
                         index = parsed_col_names)

parsed = df.apply(parse_zoning, axis = 1)

df = pd.concat([df, parsed], axis = 1)

print(f"length of parsed zoning df is {len(df)}")



fails_crosswalk = pd.read_parquet(f'gcs://usc-price-workshop/crosswalk_zone_parse_fails.parquet')

print(f'# obs in fails_crosswalk: {len(fails_crosswalk)}')



# Grab all obs in our df that shows up in the fails_crosswalk, even if it was parsed correctly
# There were some other ones that were added because they weren't valid zone classes
fails = df[df.ZONE_CMPLT.isin(fails_crosswalk.ZONE_CMPLT)]
print(f'# obs in fails: {len(fails)}')

# Convert the overlay column from string to list
fails_crosswalk.overlay = fails_crosswalk.overlay.str[1:-1].str.split(',').tolist()

# Fill in Nones with empty list
fails_crosswalk['overlay'] = fails_crosswalk['overlay'].apply(lambda row: row if isinstance(row, list) else [])


df1 = df[~ df.ZONE_CMPLT.isin(fails_crosswalk.ZONE_CMPLT)]

# Append the successfully parsed obs with the failed ones
df2 = df1.append(fails_crosswalk)


# Make sure cols are the same type again
for col in ['zone_class', 'specific_plan', 'height_district']:
    df2[col] = df2[col].astype(str)

for col in ['Q', 'T', 'D']:
    df2[col] = df2[col].astype(int)


print(f'# obs in df: {len(df)}')
print(f'# obs in df2: {len(df2)}')


# ## Need to do something about overlays and specific plans...
# * leave as list? -> then split (ZONE_CMPLT, geometry) from the rest, so we can save geojson and tabular separately
# * GeoJSON can't take lists. Convert to strings...later make it a list again?


# Fill in Nones, otherwise cannot do the apply to make the list a string
df2.overlay = df2.overlay.fillna('')

just_overlay = df2[df2.overlay != ''][['ZONE_CMPLT', 'overlay']]
just_overlay['no_brackets'] = just_overlay['overlay'].apply(', '.join)

split = just_overlay.no_brackets.str.split(',', expand = True).fillna('')
split.rename(columns = {0: 'o1', 1: 'o2', 2: 'o3'}, inplace = True)

just_overlay = pd.concat([just_overlay, split], axis = 1)


supplemental_use = pd.read_parquet(f'gcs://usc-price-workshop/crosswalk_supplemental_use_overlay.parquet')
specific_plan = pd.read_parquet(f'gcs://usc-price-workshop/crosswalk_specific_plan.parquet')



supplemental_use_dict = supplemental_use.set_index('supplemental_use').to_dict()['supplemental_use_description']
specific_plan_dict = specific_plan.set_index('specific_plan').to_dict()['specific_plan_description']

# Trouble mapping it across all columns
for col in ['o1', 'o2', 'o3']:
    just_overlay[col] = just_overlay[col].str.strip()
    new_col = f'{col}_descrip'
    just_overlay[new_col] = just_overlay[col].map(supplemental_use_dict)
    just_overlay[new_col] = just_overlay[new_col].fillna('')



# Put df back together
df3 = pd.merge(df2, just_overlay, on = 'ZONE_CMPLT', how = 'left', validate = '1:1')
df3.head()



col_order = ['ZONE_CMPLT', 'ZONE_SMRY', 
             'Q', 'T', 'zone_class', 'height_district', 'D',
             'specific_plan', 'no_brackets', 'geometry']

# Geometry is messed up, so let's get it back from original dissolve
final = (pd.merge(df[['ZONE_CMPLT', 'geometry']], df3.drop(columns = "geometry"), 
                  on = "ZONE_CMPLT", how = "left", validate = "1:1")
         [col_order]
         .rename(columns = {'no_brackets': 'overlay'})
         .sort_values(['ZONE_CMPLT', 'ZONE_SMRY'])
         .reset_index(drop=True)
        )

final.head()

# Fix CRS. It's EPSG:2229, not EPSG:4326
final.crs = "EPSG:2229"


# Make zipped shapefile
# Remember: shapefiles can only take 10-char column names
def make_zipped_shapefile(df, path):
    """
    Make a zipped shapefile and save locally
    Parameters
    ==========
    df: gpd.GeoDataFrame to be saved as zipped shapefile
    path: str, local path to where the zipped shapefile is saved.
            Ex: "folder_name/census_tracts" 
                "folder_name/census_tracts.zip"
    """

    # Grab first element of path (can input filename.zip or filename)
    dirname = os.path.splitext(path)[0]
    print(f'Path name: {path}')
    print(f'Dirname (1st element of path): {dirname}')
    # Make sure there's no folder with the same name
    shutil.rmtree(dirname, ignore_errors = True)
    # Make folder
    os.mkdir(dirname)
    shapefile_name = f'{os.path.basename(dirname)}.shp'
    print(f'Shapefile name: {shapefile_name}')
    # Export shapefile into its own folder with the same name 
    df.to_file(driver = 'ESRI Shapefile', filename = f'{dirname}/{shapefile_name}')
    print(f'Shapefile component parts folder: {dirname}/{shapefile_name}')
    # Zip it up
    shutil.make_archive(dirname, 'zip', dirname)
    # Remove the unzipped folder
    shutil.rmtree(dirname, ignore_errors = True)

## not great that I have to shapefile this but whatever 
make_zipped_shapefile(final, './zoning_parsed.zip')
