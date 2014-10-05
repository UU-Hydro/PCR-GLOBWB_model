PCR-GLOBWB git repository.
For questions, please contact E.H.Sutanudjaja@uu.nl

Some git reference cards:
- https://help.github.com/articles/git-cheatsheet
- http://devcheatsheet.com/tag/git/

The version number is 2.0.2 if you (just) clone this repo from the "master" branch of "git@github.com:UU-Hydro/PCR-GLOBWB.git" or "git@edwin1.geo.uu.nl:~/pcrglobwb.git"

This version 2.0.2 is released on 5 October 2014. 

This version 2.0.2 is a bug fix version for 2.0.1.  
Very short summary of changes introduced in this version 2.0.2 (compared to the version 2.0.1):
- Bug fixing while opening refETPotFileNC file that is given without its absolute path. 
- Bug fixing to allow model runs with the option limitAbstraction = True. 
- Fixing (small) rounding errors while scaling/correcting land cover fractions. 
- Add more water balance debugs/checks.  
- Remove the option to allow model runs without lakes and/or reservoirs (as they may produce unrealistic results, e.g. near Caspian Sea).    
- Remove the initial condition waterBodyStorageIni (as this can be directly calculated from channelStorageIni). 
- Add “known_issues.txt”. 
- New-style reporting: Add "reporting.py" and "variable_list.py" modules.  
- Please list the variable names that you want to report in the (new) field "reportingOptions" of your configuration/ini file (see ini file for an example).  
- The "variable_list.py" contains information of all variables that can be reported. This list includes "variable_names" and "units" that will be used in reported netcdf files. 
- Note that old-style/previous version reporting and old-style/previous format ini file should still works. 
