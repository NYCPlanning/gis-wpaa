# WPAA Distribution

*******************************

This script is used for migrating WPAA datasets, provided by the Waterfront Division, across DCP's internal network system:

### Prerequisites

An installation of Python 2 with the following packages is required. A version of Python with the default ArcPy installation that comes with ArcGIS Desktop is required in order to utilize Metadata functionality that is currently not available in the default ArcPy package that comes with ArcGIS Pro (Python 3) installation or the 64-bit Arcpy package that comes with 64-bit Background Geoprocessing.

##### WPAA\_distribution.py

```
arcpy, os, datetime, sys, ConfigParser
```

### Instructions for running

##### WPAA\_distribution.py

1. Open the script in any integrated development environment (PyCharm is suggested)

2. Ensure that your IDE is set to be utilizing a version of Python 2 with the arcpy module installed, as well as the above listed required python packages.

3. Ensure that the configuration ini file is up-to-date with path variables and S3 credentials. If any paths or credentials have changed since the time of this writing, those changes must be reflected in the Config.ini file.

4. Run the script. The script will check for the existence of metadata, shp, web, and fgdb directories. If they exist, the script will use them. If they do not exist, the script will generate them.

5. The script will check if there are available shapefiles within the individual dataset directories. If available shapefiles are found, the script will repair their respective geometries and export them to the SDE with “NoProj” appended to the end.

6. New projected feature classes are exported from the previous export. Previous export feature classes are removed from SDE.

7. The publicly owned waterfront dataset has agency field values standardized. All WPAA datasets then have their field names altered to match pre-defined values.

8. Metadata xmls are exported to a temporary XML directory

9. A log of any fields that were not successfully altered in the process is generated in a temporary directory

10. The script will output shapefiles in the appropriate BYTES shapefile directory.
