PCR-GLOBWB git repository.
For questions, please contact E.H.Sutanudjaja@uu.nl.

Some git reference cards:
- https://help.github.com/articles/git-cheatsheet
- http://devcheatsheet.com/tag/git/

A cookbook about how to run PCR-GLOBWB and contribute to its development: 
- http://goo.gl/8d9frs (created on May 2014).
- Examples of model input files can be obtained from git@github.com:UU-Hydro/PCR-GLOBWB_input_example.git (including ini files). 

This is a pre-release for the version 2.0.3 (alpha)

This version 2.0.3 includes kinematic routing features and some bug fixes for the previous version for 2.0.2.  
Very short summary of changes introduced in this version 2.0.3 (compared to the version 2.0.2):

- Fixing water balance errors (at the beginning of each year) while using the option "historicalIrrigationArea".

- Add more water balance debugs/checks.  

- Kinematic routing features. There are two options for kinematic waves: "simplifiedKinematicWave" and "kinematicWave". To avoid numeric instability, sub-time steps are needed while routing surface water storage (i.e. "channelStorage"). The difference between "simplifiedKinematicWave" and "kinematicWave" is on how each method calculates gains and losses (e.g. evaporation, abstraction & allocation and lake/reservoir inflow & outflow fluxes) in "channelStorage". The method "simplifiedKinematicWave" is relative similar to "accuTravelTime", which calculates first daily gains and losses in "channelStorage" (for one full day time step) and subsequently routes the water along drainage network. In the "kinematicWave" method, gains and losses "channelStorage" in are calculated within the sub-time step (not on the daily time step level). 
- The option for accuTravelTime is still available.     

- Add posibility to use fixed/constant channel width. 
- Add/return the initial condition waterBodyStorageIni. This is optional (as this can also be directly calculated from channelStorageIni).

- For known issues/bugs that have not been solved, please refer to the file “known_issues.txt”.
