# RiverScape


This repository holds a set of Jupyter notebooks for the interactive evaluation of river management measures, the RiverScape Python package and necessary input data.

For a detailed description of the concepts, models and study area we refer to the reference publications
[Straatsma and Kleinhans (2018)](https://doi.org/10.1016/j.envsoft.2017.12.010),
[Straatsma et al. (2017)](https://advances.sciencemag.org/content/3/11/e1602762) and
[Straatsma et al. (2019)](https://doi.org/10.5194/nhess-19-1167-2019).


## How to install

A few steps are required to run the Jupyter notebooks:

 1. You will need a working Python environment, we recommend to install Miniconda. Follow their instructions given at:

    [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)

 2. Download the [requirements file](https://github.com/UU-Hydro/RiverScape/blob/master/requirements.yaml) and use it to install all modules required to run the Jupyter notebooks:

    `conda env create -f requirements.yaml`

    The requirements file will create a environment named *riverscape* using Python 3.8. In case you prefer a different name or Python version you need to edit the *requirements.yaml* file.

 3. Activate the environment in a command prompt:

    `conda activate riverscape`

 4. Clone or download this repository:

    `git clone https://github.com/UU-Hydro/RiverScape.git`

    This will clone RiverScape into the current working directory.

General information on Jupyter notebooks and manuals can be found [here](https://jupyter.readthedocs.io/en/latest/).
The user guide and short reference on Conda can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/cheatsheet.html).

## How to run

Activate the environment in a command prompt:

`conda activate riverscape`

Change to the RiverScape *scripts* directory.
You can start Jupyter from the command prompt and afterwards select a notebook in your browser:

`jupyter-notebook`



You can also open individual notebooks directly by specifying the filename, e.g. the intervention planning with:

`jupyter-notebook intervent_parameter.ipynb`



## Available notebooks

The following Jupyter notebooks are provided:

  1. Intervention planning: [intervent_parameter.ipynb](scripts/intervention_planning.ipynb)

  2. Evaluation of biodiversity: [biodiversity_evaluation.ipynb](scripts/biodiversity_evaluation.ipynb)

  3. Evaluation of implementation costs: [cost_evaluation.ipynb](scripts/cost_evaluation.ipynb)

  4. Evaluation of landowner involvement: [landowner_evaluation.ipynb](scripts/landowner_evaluation.ipynb)

  5. Evaluation of an ensemble of pre-defined measures: [measure_evaluation.ipynb](scripts/measure_evaluation.ipynb)




## Exemplary output set of measures

In case you want to run the evaluation notebooks without explicitly defining your own set of measures first you can load output data from a pre-defined set of measures.
A single measure is included in the *output* folder.
An ensemble of measures is provided as compressed file.
Extract the file *example_measures_waal.zip* in the *outputs* folder.
You'll get a *example_measures_waal* subfolder containing outputs of 17 measures.



