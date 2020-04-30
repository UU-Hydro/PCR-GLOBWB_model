# PCR-GLOBWB

PCR-GLOBWB (PCRaster Global Water Balance) is a large-scale hydrological model intended for global to regional studies and developed at the Department of Physical Geography, Utrecht University (Netherlands). This repository holds the model scripts of PCR-GLOBWB. 

contact: Edwin H. Sutanudjaja (E.H.Sutanudjaja@uu.nl).

Please also see the file README.txt.

Main reference/paper: Sutanudjaja, E. H., van Beek, R., Wanders, N., Wada, Y., Bosmans, J. H. C., Drost, N., van der Ent, R. J., de Graaf, I. E. M., Hoch, J. M., de Jong, K., Karssenberg, D., López López, P., Peßenteiner, S., Schmitz, O., Straatsma, M. W., Vannametee, E., Wisser, D., and Bierkens, M. F. P.: PCR-GLOBWB 2: a 5 arcmin global hydrological and water resources model, Geosci. Model Dev., 11, 2429-2453, https://doi.org/10.5194/gmd-11-2429-2018, 2018.

## Input and output files

PCR-GLOBWB input and output files for the runs made in Sutanudjaja et al. (2018, https://doi.org/10.5194/gmd-11-2429-2018) are available on https://geo.data.uu.nl/research-pcrglobwb/pcr-globwb_gmd_paper_sutanudjaja_et_al_2018/. For requesting access, please send an e-mail to E.H.Sutanudjaja@uu.nl.

The input files are also available on the OPeNDAP server: https://opendap.4tu.nl/thredds/catalog/data2/pcrglobwb/version_2019_11_beta/catalog.html. 


## How to install

Please follow the following steps required to install PCR-GLOBWB:

 1. You will need a working Python environment, we recommend to install Miniconda, particularly for Python 3. Follow their instructions given at https://docs.conda.io/en/latest/miniconda.html. The user guide and short reference on conda can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/cheatsheet.html).

 2. Get the requirement or environment file from this repository [conda_env/pcrglobwb_py3.yml](conda_env/pcrglobwb_py3.yml) and use it to install all modules required () to run PCR-GLOBWB:

    `conda env create -f requirements.yaml`

    The requirements file will create a environment named *riverscape*.

 3. Activate the environment in a command prompt:

    `conda activate riverscape`

 4. Clone or download this repository. We suggest to use the latest version of the model

    `git clone https://github.com/UU-Hydro/RiverScape.git`

    This will clone PCR-GLOBWB into the current working directory.


## How to run

Activate the environment in a command prompt:

`conda activate riverscape`

Change to the RiverScape *scripts* directory.

You can start Jupyter from the command prompt and afterwards select a notebook in your browser:

`jupyter-notebook`



You can also open individual notebooks directly by specifying the filename, e.g. the intervention planning with:

`jupyter-notebook intervent_parameter.ipynb`



## PCR-GLOBWB website is under development

Currently under development. 
We will include some exercises. 


