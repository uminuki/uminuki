# -*- coding: utf-8 -*-
An overview of the tasks:

 - extract OpenStreetMap data from Philippines
 - make a simple visualization  
 - calculate building density for a given city/municipality

## Problem 1
 - download and initialize OpenStreetMap data reader for any city/municipality in the Philippines of your choice using `osmnx`
 - Read following datasets from the OSM:

   1. Buildings
   2. Roads
   3. Administrative boundary for the city/municipality of interest

 - Select the buildings and roads that intersect with the given administrative boundary (city/municipality)
 - Project the selected buildings and roads to appropriate UTM Zone projection
 - Visualize the reprojected buildings, roads and the administrative boundary and produce a map that pleases your eye (style is free).
"""

# Install needed packages
!pip install mapclassify
!pip install osmnx

import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Download and extract OSM data for Pasig City
# City
city = ox.geocode_to_gdf("Pasig City, National Capital Region")

# City Roads
roads = ox.graph_to_gdfs(ox.graph_from_place("Pasig"), nodes=False)

# City Buildings
bldgs = ox.features.features_from_place(query="Pasig", tags={"building":True})

# Buildings and roads that intersect with the administrative boundary
city_bldgs_int = bldgs[bldgs.intersects(city.unary_union)]
city_roads_int = roads[roads.intersects(city.unary_union)]

# Projection

# Detect crs of the city data
crs = ox.project_gdf(city).crs

# Project to the defined crs
city = city.to_crs(crs)
city_bldgs_int = city_bldgs_int.to_crs(crs)
city_roads_int = city_roads_int.to_crs(crs)

# Visualization of the city

# Function for city plot
def plot_city(city, bldg, road, map_title):
  # city: city boundary data
  # bldg: buildings data
  # road: road data
  # map_title: "map title"

  # Plot style and size
  plt.style.use("default")
  fig, a = plt.subplots(figsize=(10,10))

  # Features style
  road.plot(ax=a, color="silver", linewidth=0.5)
  bldg.plot(ax=a, color="teal")
  city.plot(ax=a, facecolor="none", edgecolor="red")

  # Map Title
  plt.title(map_title, fontsize=15, fontweight="bold", color="black", pad=20)

  # Map Legend
  lgd_1 = mpatches.Patch(facecolor="silver", label="Roads", linewidth=0.5, edgecolor="black")
  lgd_2 = mpatches.Patch(facecolor="teal", label="Buildings", linewidth=0.5, edgecolor="black")
  lgd_3 = mpatches.Patch(facecolor="red", label="City Boundary", linewidth=0.5, edgecolor="black")

  legend = plt.legend(handles=[lgd_1, lgd_2, lgd_3], title="Legend", loc=2, fontsize="medium", fancybox=True)

  return plt.show()

plot_city(city, city_bldgs_int, city_roads_int, "Map of Pasig City")

"""## Problem 2 

Based on the buildings and city/municipality GeoDataFrames, calculate the building density for the given city/municipality. :

 - Calculate the total area of all buildings within your city/municipality
   - Note: Use the buildings and city/municipality from Problem 1
 - Divide this total building area by the area of the city/municipality
   - the result shows the building density as percentage (i.e. proportion of the land that is allocated for buildings)
 - Print the result for your city/municipality to the screen in percentages with 1 decimal point. I.e. it should say something like:
   - "Building density in Matandang Balara is 14.7 %.

"""

# Function for computing building density of a city
def bldg_density(city_boundary, city_bldgs):
  # city_boundary: city boundary data
  # city_bldgs: city buildings data intersected with city boundary

  # Total city area
  city_area = city_boundary.area.iloc[0]

  # Total area of all buildings in the city (sqm.)
  city_bldgs["area"] = city_bldgs.geometry.area
  total_bldgs_area = city_bldgs["area"].sum()

  # Computation for building density
  bldg_density = (total_bldgs_area / city_area) * 100

  return bldg_density

# Compute and print building density for Pasig City
city_bldg_density = bldg_density(city, city_bldgs_int)
print(f'Building density in Pasig City is {city_bldg_density} %')

"""## Problem 3 

Calculate building densities for all barangays in your own City/Municipality.

**Description**:

 1. Read the boundaries for your City/Municipality using `osmnx` and add `"admin_level"` as an extra attribute for `extra_attributes` -parameter (see docs of pyrosm). This will ensure that the `admin_level` tag is kept as a column in the resulting GeoDataFrame.
 2. Read the buildings for your City/Municipality with `osmnx`
 3. Select all barangays from the administrative boundaries of your City/Municipality (step 1), i.e. all rows in which the `admin_level` is `"10"` (notice that the number is stored as a string).
 4. Reproject all barangays and buildings to proper UTM Zone
 5. Create a new column called `density` for barangays GeoDataFrame and assign a value 0 to it
 6. Iterate over barangays, calculate the building density (in a similar manner as in Problem 2) and update the result into the `density` column in the barangays GeoDataFrame. The density should be represented as a percentage (0-100) rounding it to 1 decimal.
 7. Visualize the results and add a legend and title for the map according to your liking.


"""

import pandas as pd
import geopandas as gpd
import matplotlib as mpl

# Retrieve barangays and buildings data of Pasig City from OSM
barangay = ox.features_from_place("Pasig City", tags={"admin_level":"10"})
building = ox.features.features_from_place(query="Pasig City", tags={"building":True})

# Reproject barangays and buildings to proper UTM zone
crs = ox.project_gdf(barangay).crs
barangay = barangay.to_crs(crs)
building = building.to_crs(crs)

# Data filtering for Barangay geometry
# Filter for barangay values in the OSM keys
barangay_node = barangay[barangay['admin_type:PH'].str.contains("barangay", na=False)] # queries for barangays and fills value for missing values
# Get exact geometry of each barangay by intersecting each node with the geometry
# Barangay node must be within the barangay geometry and the geometry should be valid ( area > 0)
barangay = barangay[barangay.intersects(barangay_node.unary_union)]
barangay = barangay[barangay.is_valid & (barangay.geometry.area > 0)]

# New column for density in barangay data
barangay['density'] = 0

# Function for looping through barangays in a city to obtain building density
def city_baranagays_density(city_barangays, city_buildings):
  # city_barangays: city barangays data
  # city_buildings: city buildings data

  for i in range(len(city_barangays)):
    # Retrieve the barangay row
    current = city_barangays.iloc[i]
    current_baranagay_area = current.geometry.area

    # Get the total area of buildings in each barangay
    # Intersect barangay geometry with building footprint
    barangay_buildings_int = city_buildings[city_buildings.intersects(current.geometry)]
    total_buildings_area = barangay_buildings_int.geometry.area.sum()

    # Compute for building density
    building_density = (total_buildings_area / current_baranagay_area) * 100

    # Add computed building density to the density row
    city_barangays.loc[city_barangays.index[i], "density"] = round(building_density, 1)

# Command for computing building density per barangay in Pasig City
city_baranagays_density(barangay, building)

def barangay_density_map(barangay_density_data, map_title):
  fig, ax = plt.subplots(figsize=(10,10))

  cmap = "YlGn"
  norm = mpl.colors.Normalize(vmin=0, vmax=100)
  barangay_density_data.plot(ax=ax, column="density", cmap=cmap, norm=norm)

  # Map Title
  plt.title(map_title, fontsize=15, fontweight="bold", color="black", pad=20)

  sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
  sm.A = []
  cbar = fig.colorbar(sm, ax=ax)
  cbar.set_label("Building Density (%)", fontsize=13)


  return plt.show()

barangay_density_map(barangay, "Building Density per Barangay in Pasig City")
