import arcpy, os, datetime, sys, ConfigParser

try:

    # Set config var
    config = ConfigParser.ConfigParser
    config.read(r'G:\SCRIPTS\WPAAs_Distribution\ini\wpaa_distribution.ini')

    # Set path variables
    sde_path = config.get("INPUT_PATHS", "sde_path")
    WPAA_path = config.get("INPUT_PATHS", "wpaa_bytes_path")
    template_path = config.get("INPUT_PATHS", "template_path")
    layer_path = config.get("INPUT_PATHS", "layer_path")
    log_path = config.get("INPUT_PATHS", "log_path")
    arc_dir = arcpy.GetInstallInfo("desktop")["InstallDir"]
    translator = os.path.join(arc_dir, "Metadata\Translator\ArcGIS2FGDC.xml")
    xslt_html = os.path.join(arc_dir, "Metadata\Stylesheets\ArcGIS.xsl")
    xslt_remove_storage = os.path.join(arc_dir, r"Metadata\Stylesheets\gpTools\remove local storage info.xslt")
    xslt_remove_geoproc_hist = os.path.join(arc_dir, r"Metadata\Stylesheets\gpTools\remove geoprocessing history.xslt")

    # Define log file
    log = open(log_path, "a")
    StartTime = datetime.datetime.now().replace(microsecond=0)

    # Parse raw directory path
    yr_dir_list = []

    for dir in os.listdir(WPAA_path):
        yr_dir_list.append(datetime.datetime.strptime(dir, '%Y'))

    latest_yr_dir = datetime.datetime.strftime(max(yr_dir_list), '%Y')

    export_dirs_yr = os.path.join(WPAA_path, latest_yr_dir)

    export_dir_month_list = os.listdir(export_dirs_yr)
    print(export_dir_month_list)

    export_dirs = []

    for dir in export_dir_month_list:
        export_dirs.append(datetime.datetime.strptime(dir, '%Y%m'))

    desired_export_dir = datetime.datetime.strftime(max(export_dirs), '%Y%m')

    print(desired_export_dir)

    desired_export_path = os.path.join(export_dirs_yr, desired_export_dir)

    desired_raw_path = os.path.join(desired_export_path, 'raw')
    desired_meta_path = os.path.join(desired_export_path, 'metadata')
    temp_meta_path = r'C:\temp\meta\wpaa'
    desired_shp_path = os.path.join(desired_export_path, 'shp')
    desired_web_path = os.path.join(desired_export_path, 'web')
    desired_fgdb_path = os.path.join(desired_export_path, 'fgdb_working')

    if os.path.exists(desired_raw_path):
        print("Raw directory available. Continuing script")
    else:
        print("Raw directory not available. Aborting script since no inputs are currently available")
        sys.exit("No raw path available. Aborting script run")

    # Check the directory path availability for all desired export directories
    def check_path_availability(path):
        if os.path.exists(path):
            print("{} already exists. Continuing script".format(path))
        else:
            print("{} does not exist. Creating path".format(path))
            os.mkdir(path)


    check_path_availability(desired_meta_path)
    check_path_availability(desired_shp_path)
    check_path_availability(desired_web_path)
    check_path_availability(desired_fgdb_path)
    check_path_availability(temp_meta_path)

    available_directories = []

    for dir in os.listdir(desired_raw_path):
        if dir.endswith('.gdb'):
            available_directories.append(dir)
            wpaa_gdb_path = os.path.join(desired_raw_path, dir)
            print("GDB Path: {}".format(wpaa_gdb_path))

    if len(available_directories) > 0:
        print('Raw input geodatabase found. Continuing')
    else:
        print("No raw input geodatabase found. Aborting")
        sys.exit()

    waterfront_projected_feature_classes = []

    # Export projected feature classes to SDE

    arcpy.env.workspace = wpaa_gdb_path
    arcpy.env.overwriteOutput = True

    desired_raw_fc_list = arcpy.ListFeatureClasses()

    print(desired_raw_fc_list)

    # Disconnect users from Production SDE to prohibit any schema locks if necessary
    arcpy.AcceptConnections(sde_prod_env, False)
    arcpy.DisconnectUser(sde_prod_env, "ALL")

    arcpy.env.workspace = sde_path
    arcpy.env.overwriteOutput = True

    for fc in desired_raw_fc_list:
        coord_sys_ref = 'Projected Coordinate Systems/State Plane/NAD 1983 (US Feet)/NAD 1983 StatePlane New York Long Isl FIPS 3104 (US Feet)'
        out_coord_sys = arcpy.SpatialReference(coord_sys_ref)
        raw_shp_path = os.path.join(wpaa_gdb_path, fc)
        print("Repairing {} geometry errors".format(fc))
        arcpy.RepairGeometry_management(raw_shp_path)
        print("Exporting {} to {}".format(raw_shp_path, 'DCP_WOS_{}'.format(fc)))
        print("Setting coordinate system")
        print("Projecting {} to Long Island State Plane".format(fc))
        arcpy.Project_management(raw_shp_path, 'DCP_WOS_{}'.format(fc), out_coord_sys)
        print("Export complete")
        waterfront_fc_name = os.path.join(sde_path, 'DCP_WOS_{}'.format(fc))
        waterfront_projected_feature_classes.append(waterfront_fc_name)

    print(waterfront_projected_feature_classes)

    # Export and update metadata. Export shapefiles to shapefile directory on BytesProd

    for fc in waterfront_projected_feature_classes:
        waterfront_fc_name = os.path.join(sde_path, fc)

        temp_metadata_xml_name = r'{}.xml'.format(os.path.join(temp_meta_path, waterfront_fc_name.split('\\')[-1]))
        desired_metadata_xml_name = r'{}.xml'.format(os.path.join(desired_meta_path, waterfront_fc_name.split('\\')[-1]))
        print(temp_metadata_xml_name)
        metadata_xml_nostorage_name = temp_metadata_xml_name.replace('.xml', '_nostorage.xml')
        print(metadata_xml_nostorage_name)
        metadata_xml_final_name = temp_metadata_xml_name.replace('.xml', '_final.xml')
        print(metadata_xml_final_name)
        print("Exporting xml metadata to temporary location for cleaning")
        arcpy.ExportMetadata_conversion(waterfront_fc_name,
                                        translator,
                                        temp_metadata_xml_name)
        arcpy.XSLTransform_conversion(temp_metadata_xml_name,
                                      xslt_remove_storage,
                                      metadata_xml_nostorage_name)
        arcpy.XSLTransform_conversion(metadata_xml_nostorage_name,
                                      xslt_remove_geoproc_hist,
                                      metadata_xml_final_name)
        print("Metadata xml final name - {}".format(metadata_xml_final_name))
        print('Waterfront FC name - {}'.format(waterfront_fc_name))
        arcpy.MetadataImporter_conversion(metadata_xml_final_name,
                                          waterfront_fc_name)
        print("Exporting xml metadata to desired location on BytesProd")
        arcpy.ExportMetadata_conversion(metadata_xml_final_name,
                                        translator,
                                        desired_metadata_xml_name)
        print(desired_metadata_xml_name.replace('.xml', '.html'))
        arcpy.XSLTransform_conversion(desired_metadata_xml_name, xslt_html, desired_metadata_xml_name.replace('.xml', '.html'))
        print("Exporting shapefiles to desired location on BytesProd")
        arcpy.FeatureClassToShapefile_conversion(waterfront_fc_name, desired_shp_path)

        # Export layers and associated metadata to desired directories

        print("Layer path - {}".format(os.path.join(layer_path, r'{}.lyr'.format(desired_metadata_xml_name.split('\\')[-1].replace('.xml', '')))))
        print("Exporting layers to desired location on DATA")
        arcpy.MakeFeatureLayer_management(waterfront_fc_name, r'{}'.format(desired_metadata_xml_name.split('\\')[-1].replace('.xml', '')))
        arcpy.SaveToLayerFile_management(r'{}'.format(desired_metadata_xml_name.split('\\')[-1].replace('.xml', '')),
                                         os.path.join(layer_path, r'{}.lyr'.format(desired_metadata_xml_name.split('\\')[-1].replace('.xml', ''))))
        print("Exporting xmls to desired location on DATA")
        arcpy.ExportMetadata_conversion(waterfront_fc_name, translator, os.path.join(layer_path, r'{}.lyr.xml'.format(desired_metadata_xml_name.split('\\')[-1].replace('.xml',''))))
        print("Processing complete")

    EndTime = datetime.datetime.now().replace(microsecond=0)
    print("Script runtime: {}".format(EndTime - StartTime))
    log.write(str(StartTime) + "\t" + str(EndTime) + "\t" + str(EndTime - StartTime) + "\n")
    log.close()

    arcpy.AcceptConnections(sde_prod_env, True)

except:
    arcpy.AcceptConnections(sde_prod_env, True)
    print "error"
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages() + "\n"

    print pymsg
    print msgs

    log.write("" + pymsg + "\n")
    log.write("" + msgs + "")
    log.write("\n")
    log.close()