PCR-GLOBWB git repository.
For questions, please contact E.H.Sutanudjaja@uu.nl.

Some git reference cards:
- https://help.github.com/articles/git-cheatsheet
- http://devcheatsheet.com/tag/git/

A cookbook about how to run PCR-GLOBWB and contribute to its development: 
- http://goo.gl/8d9frs (created on May 2014).
- Examples of model input files can be obtained from git@github.com:UU-Hydro/PCR-GLOBWB_input_example.git (including ini files). 

The version number is 2.0.2 if you (just) clone this repo from:
- the master branch of git@github.com:UU-Hydro/PCR-GLOBWB.git ; or from
- the master branch of git@edwin1.geo.uu.nl:~/pcrglobwb.git

This version 2.0.2 is released on 5 October 2014. 

This version 2.0.2 is basically a bug fix version for 2.0.1.  
Very short summary of changes introduced in this version 2.0.2 (compared to the version 2.0.1):

- Bug fixing while opening refETPotFileNC file that is given without its absolute path. 

- Bug fixing to allow model runs with the option limitAbstraction = True. 

- Fixing (small) rounding errors while scaling/correcting land cover fractions. 

- Add more water balance debugs/checks.  

- Remove the option to allow model runs without lakes and/or reservoirs (as they may produce unrealistic results, e.g. near Caspian Sea).    

- Remove the initial condition waterBodyStorageIni (as this can be directly calculated from channelStorageIni). 

- New-style reporting: Add "reporting.py" and "variable_list.py" modules.  
- Please list variable names that you want to report in the (new) field "reportingOptions" of your configuration/ini file (see ini file examples).  
- The "variable_list.py" contains information of all variables that can be reported. 
- The list in "variable_list.py" includes "variable_names" and "units" that will be used in netcdf files. 
- Note that old-style/previous version (2.0.1) reporting and old-style/previous format configuration ini file should still work. 

- Add “known_issues.txt”. 
- For known issues/bugs that have not been solved, please refer to the file “known_issues.txt”.
