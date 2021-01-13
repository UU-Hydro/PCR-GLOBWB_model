
set -x

INP_FOLDER="/scratch/ms/copext/cynw/pcrglobwb_ulysses_reference_runs_version_2020-12-01/old-jgw_uly-et0_uly-lcv_merged_1981-2019/runoff/"
OUT_FOLDER="/scratch/ms/copext/cynw/pcrglobwb_ulysses_reference_runs_version_2020-12-01/old-jgw_uly-et0_uly-lcv_merged_1981-2019/daily_runoff_in_monthly_files/"

INP_FOLDER=$1
OUT_FOLDER=$2

bash cdo_selmon.sh 1981 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1982 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1983 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1984 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1985 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1986 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1987 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1988 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1989 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1990 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1991 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1992 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1993 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1994 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1995 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1996 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1997 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1998 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 1999 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2000 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2001 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2002 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2003 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2004 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2005 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2006 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2007 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2008 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2009 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2010 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2011 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2012 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2013 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2014 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2015 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2016 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2017 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2018 ${INP_FOLDER} ${OUT_FOLDER}
#~ bash cdo_selmon.sh 2019 ${INP_FOLDER} ${OUT_FOLDER}
                   
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 19:33 1981
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 19:33 1982
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 19:33 1983
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 19:33 1984
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 19:33 1985
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 19:33 1986
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 19:33 1987
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 19:33 1988
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 19:33 1989
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1990
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1991
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1992
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1993
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1994
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1995
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1996
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1997
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1998
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 21:15 1999
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:39 2000
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:40 2001
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:40 2002
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:40 2003
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:40 2004
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:40 2005
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:40 2006
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:40 2007
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:40 2008
#~ dr-xr-x---  2 cynw copext 4.0K Dec  7 22:40 2009
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2010
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2011
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2012
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2013
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2014
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2015
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2016
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2017
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2018
#~ dr-xr-x---  2 cynw copext 4.0K Dec  8 00:08 2019
#~ -r--r-----  1 cynw copext  19K Dec  7 19:33 merge_netcdf_6_arcmin_ulysses.py
#~ (pcrglobwb_python36_ulysses) cynw@cca-login4:/scratch/ms/copext/cynw/pcrglobwb_ulysses_reference_runs_version_2020-12-01/old-jgw_uly-et0_uly-lcv_merged_1981-2019/runoff>

set +x
