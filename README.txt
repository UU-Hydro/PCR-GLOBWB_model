PCR-GLOBWB git repository.

PCR-GLOBWB is copyrighted by Utrecht University and released under the GPL license, version 3

This program comes with ABSOLUTELY NO WARRANTY

See the "LICENSE" file for more information.

For questions, please contact Edwin Sutanudjaja (e-mail: E.H.Sutanudjaja@uu.nl).

Some git reference cards:
- https://help.github.com/articles/git-cheatsheet
- http://devcheatsheet.com/tag/git/

A cookbook about how to run PCR-GLOBWB and contribute to its development: 
- http://goo.gl/8d9frs (created on May 2014).
- Examples of model input files can be obtained from git@github.com:UU-Hydro/PCR-GLOBWB_input_example.git (including ini files). 

The version number is 2.0.3 if you (just) clone this repo from the the master branch of git@github.com:UU-Hydro/PCR-GLOBWB.git

The version 2.0.3 is released on 12 November 2014.

This version 2.0.3 includes kinematic wave routing features and some bug fixes for the previous version 2.0.2.  
Very short summary of changes introduced in this version 2.0.3 (compared to the version 2.0.2):

- Add more water balance checks/debugs.

- Kinematic routing features. There are two kinematic wave methods: "simplifiedKinematicWave" and "kinematicWave". To avoid numeric instability in using these methods, sub-time steps are required while routing surface water storage (i.e. "channelStorage"). The difference between "simplifiedKinematicWave" and "kinematicWave" is on how each method update "channelStorage" with local gains/losses (e.g. runoff, river bed exchange, evaporation, abstraction & allocation, and lake/reservoir inflow & outflow). The method "simplifiedKinematicWave" is relative similar to "accuTravelTime", which update first "channelStorage" with daily local gains/losses (for one full day time step) and subsequently routes the "channelStorage" along drainage network. In the "kinematicWave" method, local gains/losses are added/substracted to/from "channelStorage" within the sub-time step (not on the daily time step level).  

- The routing option "accuTravelTime" is still available.

- Add possibility to use fixed/constant channel widths (see "constantChannelWidth" in the routingOptions of the ini or configuration file). This is optional as channel widths can also be estimated in the model.

- Add possibility to constrain channel widths (with certain minimum values, see "constantChannelWidth" in the routingOptions of the ini or configuration file). This is also optional.

- Add/restore the initial condition "waterBodyStorageIni". This is optional (as this can also be directly calculated from the initial condition "channelStorageIni").

- Fixing small/minor water balance errors (at the beginning of each year) for runs using the option "historicalIrrigationArea".

- Add possibility to perform runs considering only natural water bodies (i.e. only lakes, no reservoirs). To activate this option, please set the option "onlyNaturalWaterBodies" to "True" (see "routingOptions" in the ini or configuration file).

- For known issues/bugs that have not been solved, please refer to the file “known_issues.txt”.
