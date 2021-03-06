import os, csv
from arcpy import *
env.overwriteOutput = "TRUE"

"""
========================================================================
Tech_Report_Chapter7
========================================================================
Author: Mitchell Fyock
========================================================================
Date			Modifier	Description of Change
01/04/2017		MF			Created
========================================================================
"""

#~ output_folder = r'P:\Boardman to Hemingway Transmission Project\B to H Docs\Cultural Resources\B2H_GIS\Data\TetraTech\ASC_CR_Technical__Report\05_January_2017\GIS_Queries_FASC_Technical_Report\Chapter7'
output_folder = str(GetParameter(0))

# Survey Footprints
'''The 'surveyed_footprint' feature is comprised of all surveys performed, starting with 2011 through to the present.  THIS IS EVERYTHING THAT HAS BEEN SURVEYED IN THE PAST.'''
'''The 'current_footprint' feature is created by merging the route buffer, access buffer, and work area buffers into a single feature for the current survey year'''
surveyed_footprint = r'P:\Boardman to Hemingway Transmission Project\B to H Docs\Cultural Resources\B2H_GIS\Data\TetraTech\Routes\Cultural\B2H_to_6B2H\B2H_to_6B2H_Surveyed_Routes.gdb\Footprint\S_Footprint_B2H_to_6B2H_Dissolve'
management.MakeFeatureLayer(surveyed_footprint, "Surveyed_Footprint")
current_footprint = r'P:\Boardman to Hemingway Transmission Project\B to H Docs\Cultural Resources\B2H_GIS\Data\TetraTech\ASC_CR_Technical__Report\05_January_2017\B2H_Project Features_FASC_20160902.gdb\Footprint\Footprint_Merge_Route_Dissolve_OR'
management.MakeFeatureLayer(current_footprint, "Current_Footprint")

# Clip Features
'''The following lines of code create layers from the different components of the footprint to be used for clipping'''
route_poly = r'P:\Boardman to Hemingway Transmission Project\B to H Docs\Cultural Resources\B2H_GIS\Data\TetraTech\ASC_CR_Technical__Report\05_January_2017\B2H_Project Features_FASC_20160902.gdb\Routes\Routes_250ftBuff_Dissolve_OR'
management.MakeFeatureLayer(route_poly, "Route_Poly")
route_line = r'P:\Boardman to Hemingway Transmission Project\B to H Docs\Cultural Resources\B2H_GIS\Data\TetraTech\ASC_CR_Technical__Report\05_January_2017\B2H_Project Features_FASC_20160902.gdb\Routes\Routes_Dissolve_OR'
management.MakeFeatureLayer(route_line, "Route_Line")
work_area = r'P:\Boardman to Hemingway Transmission Project\B to H Docs\Cultural Resources\B2H_GIS\Data\TetraTech\ASC_CR_Technical__Report\05_January_2017\B2H_Project Features_FASC_20160902.gdb\Features\Features_Route_OR'
management.MakeFeatureLayer(work_area, "Work_Area")
access_line = r'P:\Boardman to Hemingway Transmission Project\B to H Docs\Cultural Resources\B2H_GIS\Data\TetraTech\ASC_CR_Technical__Report\05_January_2017\B2H_Project Features_FASC_20160902.gdb\Access\Access_Route_OR'
management.MakeFeatureLayer(access_line, "Access_Line")
access_poly = r'P:\Boardman to Hemingway Transmission Project\B to H Docs\Cultural Resources\B2H_GIS\Data\TetraTech\ASC_CR_Technical__Report\05_January_2017\B2H_Project Features_FASC_20160902.gdb\Access\Access_100ftBuff_Route_OR'
management.MakeFeatureLayer(access_poly, "Access_Poly")

# Create a list of the features to loop through during the numerical analysis
features = ["Route_Poly", "Route_Line", "Work_Area", "Access_Line", "Access_Poly"]
clip_features = ["Route_Poly_clip", "Route_Line_clip", "Work_Area_clip", "Access_Line_clip", "Access_Poly_clip"]
dissolve_features = ["Route_Poly_dissolve_clip", "Route_Line_dissolve_clip", "Work_Area_dissolve_clip", "Access_Line_dissolve_clip", "Access_Poly_dissolve_clip"]

# Isolate the different linear routes in the footprint and create layers of them
routes = []
with da.SearchCursor("Current_Footprint", "ROUTE") as cursor:
	for row in cursor:
		management.MakeFeatureLayer("Current_Footprint", "{}".format(row[0]), "ROUTE = '{}'".format(row[0]))
		routes.append(row[0])

''' Perform Numerical analysis'''

csv_output = []

# Start a loop using the 'routes' list
for route in routes:
	
	# Create a blank dictionary for the route to be populated with the results
	dictionary = {
	'Route':route,
	}
		
	# Identify the total mileage for the access roads, route buffer, and work areas for each route and populate the dictionary accordingly
	for item in features:
		management.SelectLayerByAttribute(item, "ADD_TO_SELECTION", "ROUTE = '{}'".format(route))
	
	with da.SearchCursor("Route_Poly", "Acres") as cursor:
		for row in cursor:
			dictionary['Total Route Acreage'] = row[0]
	
	with da.SearchCursor("Route_Line", 'Miles') as cursor:
		for row in cursor:
			dictionary['Total Route Length'] = row[0]
	
	with da.SearchCursor("Access_Poly", "Acres") as cursor:
		for row in cursor:
			dictionary['Total Access Acreage'] = row[0]
	
	with da.SearchCursor("Access_Line", 'Miles') as cursor:
		for row in cursor:
			dictionary['Total Access Length'] = row[0]

	with da.SearchCursor("Work_Area", "Acres") as cursor:
		for row in cursor:
			dictionary['Total Work Area Acreage'] = row[0]
	
	for item in features:
		management.SelectLayerByAttribute(item, "CLEAR_SELECTION")
		
	# Clip each feature to the 'surveyed_footprint' 
	for item in features:
		x = analysis.Clip(item, "Surveyed_Footprint", "in_memory/{}_clip".format(item))
		desc = arcpy.Describe(x)
		if desc.shapeType == 'Polygon':
			management.CalculateField(x, "Acres", "!shape.geodesicArea@acres!", "PYTHON")
		elif desc.shapeType == 'Polyline':
			management.CalculateField(x, "Miles", "!shape.geodesicLength@miles!", "PYTHON")
		management.MakeFeatureLayer(x, "{}_clip".format(item))
	
	for item in clip_features:
		management.SelectLayerByAttribute(item, "ADD_TO_SELECTION", "ROUTE = '{}'".format(route))
	
	# Identify the total mileage for the access roads, route buffer, and work areas for each route THAT WAS SURVEYED and populate the dictionary accordingly	
	with da.SearchCursor("Route_Poly_clip", "Acres") as cursor:
		for row in cursor:
			dictionary['Surveyed Route Acreage'] = row[0]
	
	with da.SearchCursor("Route_Line_clip", 'Miles') as cursor:
		for row in cursor:
			dictionary['Surveyed Route Length'] = row[0]
	
	with da.SearchCursor("Access_Poly_clip", "Acres") as cursor:
		for row in cursor:
			dictionary['Surveyed Access Acreage'] = row[0]
	
	with da.SearchCursor("Access_Line_clip", 'Miles') as cursor:
		for row in cursor:
			dictionary['Surveyed Access Length'] = row[0]
	
	with da.SearchCursor("Work_Area_clip", "Acres") as cursor:
		for row in cursor:
			dictionary['Surveyed Work Area Acreage'] = row[0]
	
	csv_output.append(dictionary)

# Write the results of the query to a .csv
with open(os.path.join(output_folder, 'Tech_Report_Table_7.csv'), 'wb') as csvfile:
	fieldnames = ['Route', 'Total Route Acreage', 'Total Route Length', 'Total Access Acreage', 'Total Access Length', 'Total Work Area Acreage', 'Surveyed Route Acreage', 'Surveyed Route Length', 'Surveyed Access Acreage', 'Surveyed Access Length', 'Surveyed Work Area Acreage']
	writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
	
	writer.writeheader()
	for row in csv_output:
		writer.writerow(row)

"""
Repeat the process above, with alterations
Create a .CSV containing the total amount for the combined access, route, and work areas by dissolving the Clip layers and performing another clipping analysis
"""

for item in features:
	# Identify the shapetype of the feature
	desc = arcpy.Describe(item)
	
	# Perform the dissolve function
	x = management.Dissolve(item, "in_memory/{}_dissolve".format(item))
	
	# Calculate the new metrics for the feature, based on its shapetype
	if desc.shapeType == 'Polygon':
		management.AddField(x, "Acres", "DOUBLE")
		management.CalculateField(x, "Acres", "!shape.geodesicArea@acres!", "PYTHON")
	elif desc.shapeType == 'Ployline':
		management.AddField(x, "Miles", "DOUBLE")
		management.CalculateField(x, "Miles", "!shape.geodesicLength@miles!", "PYTHON")
	management.MakeFeatureLayer(x, "{}_dissolve".format(item))	

# Create a blank dictionary for the route to be populated with the results
dictionary = {
'Route': 'Combined Routes',
}
	
# 
with da.SearchCursor("Route_Poly_dissolve", "Acres") as cursor:
	for row in cursor:
		dictionary['Total Route Acreage'] = row[0]

with da.SearchCursor("Route_Line_dissolve", 'Miles') as cursor:
	for row in cursor:
		dictionary['Total Route Length'] = row[0]

with da.SearchCursor("Access_Poly_dissolve", "Acres") as cursor:
	for row in cursor:
		dictionary['Total Access Acreage'] = row[0]

with da.SearchCursor("Access_Line_dissolve", 'Miles') as cursor:
	for row in cursor:
		dictionary['Total Access Length'] = row[0]

with da.SearchCursor("Work_Area_dissolve", "Acres") as cursor:
	for row in cursor:
		dictionary['Total Work Area Acreage'] = row[0]
	
# Clip each feature to the 'surveyed_footprint' 
for item in dissolve_features:
	x = analysis.Clip(item, "Surveyed_Footprint", "in_memory/{}_dissolve_clip".format(item))
	desc = arcpy.Describe(x)
	if desc.shapeType == 'Polygon':
		management.CalculateField(x, "Acres", "!shape.geodesicArea@acres!", "PYTHON")
	elif desc.shapeType == 'Polyline':
		management.CalculateField(x, "Miles", "!shape.geodesicLength@miles!", "PYTHON")
	management.MakeFeatureLayer(x, "{}_dissolve_clip".format(item))

# Identify the total mileage for the access roads, route buffer, and work areas for each route THAT WAS SURVEYED and populate the dictionary accordingly	
with da.SearchCursor("Route_Poly_dissolve_clip", "Acres") as cursor:
	for row in cursor:
		dictionary['Surveyed Route Acreage'] = row[0]

with da.SearchCursor("Route_Line_dissolve_clip", 'Miles') as cursor:
	for row in cursor:
		dictionary['Surveyed Route Length'] = row[0]

with da.SearchCursor("Access_Poly_dissolve_clip", "Acres") as cursor:
	for row in cursor:
		dictionary['Surveyed Access Acreage'] = row[0]

with da.SearchCursor("Access_Line_dissolve_clip", 'Miles') as cursor:
	for row in cursor:
		dictionary['Surveyed Access Length'] = row[0]

with da.SearchCursor("Work_Area_dissolve_clip", "Acres") as cursor:
	for row in cursor:
		dictionary['Surveyed Work Area Acreage'] = row[0]

# Write the results of the query to a .csv
with open(os.path.join(output_folder, 'Tech_Report_Table_7_Totals.csv'), 'wb') as csvfile:
	fieldnames = ['Route', 'Total Route Acreage', 'Total Route Length', 'Total Access Acreage', 'Total Access Length', 'Total Work Area Acreage', 'Surveyed Route Acreage', 'Surveyed Route Length', 'Surveyed Access Acreage', 'Surveyed Access Length', 'Surveyed Work Area Acreage']
	writer = csv.DictWriter(csvfile, fieldnames = fieldnames)
	
	writer.writeheader()
	writer.writerow(dictionary)
