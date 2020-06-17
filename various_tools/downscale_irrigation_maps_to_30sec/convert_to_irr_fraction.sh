rm *.tif
rm *.map

gdalwarp -tr 0.00833333333333333333333333333333333333333333333333333333333333333333333333 0.00833333333333333333333333333333333333333333333333333333333333333333333333 -te -180 -90 180 90 -r near ../GFSAD1KCM.2010.001.2016348142550.tif GFSAD1KCM.2010.001.2016348142550_global_30sec.tif

pcrcalc irrigated_fraction.map = "if(scalar(GFSAD1KCM.2010.001.2016348142550_global_30sec.tif) eq 1, boolean(1.0), if( scalar(GFSAD1KCM.2010.001.2016348142550_global_30sec.tif) eq 2, boolean(1.0))   )"

mapattr -s -P yb2t irrigated_fraction.map

# TODO: split irrgated_fraction.map to paddy and non-paddy


