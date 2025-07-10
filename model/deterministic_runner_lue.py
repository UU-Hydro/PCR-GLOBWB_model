#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# PCR-GLOBWB (PCRaster Global Water Balance) Global Hydrological Model
#
# Copyright (C) 2016, Edwin H. Sutanudjaja, Rens van Beek, Niko Wanders, Yoshihide Wada, 
# Joyce H. C. Bosmans, Niels Drost, Ruud J. van der Ent, Inge E. M. de Graaf, Jannis M. Hoch, 
# Kor de Jong, Derek Karssenberg, Patricia López López, Stefanie Peßenteiner, Oliver Schmitz, 
# Menno W. Straatsma, Ekkamol Vannametee, Dominik Wisser, and Marc F. P. Bierkens
# Faculty of Geosciences, Utrecht University, Utrecht, The Netherlands
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

from lue.framework.pcraster_provider import pcr, pcrfw

# needed for lue experiment
import argparse
import lue.framework as lfr
import lue.qa.scalability.instrument as lqi

from configuration import Configuration
from currTimeStep import ModelTime
from reporting import Reporting
from spinUp import SpinUp

from pcrglobwb import PCRGlobWB

import logging
logger = logging.getLogger(__name__)

import disclaimer

class DeterministicRunner(pcrfw.DynamicModel):

    def __init__(self, configuration, modelTime, initialState, \
                 count: int,
                 nr_workers: int,
                 array_shape: tuple[int, int],
                 partition_shape: tuple[int, int],
                 result_pathname: str,
                 centre: tuple[int, int]    
                 ):
        
        pcrfw.DynamicModel.__init__(self)

        if pcr.provider_name == "lue":
	    
            pcr.setclone(configuration.cloneMap)

            # overrule whatever was used with setclone, we want this:
            pcr.configuration.partition_shape = partition_shape
            pcr.configuration.array_shape = array_shape
		    
            hyperslab_shape = array_shape
            hyperslab = lfr.Hyperslab(center = centre, shape = hyperslab_shape)
		    
            ldd_lue   = lfr.from_gdal(configuration.routingOptions['lddMap'], partition_shape = partition_shape, hyperslab = hyperslab)
            
            # ~ ldd_lue   = pcr.readmap(configuration.routingOptions['lddMap'])

            ldd_lue.future().get()

            # ~ # write the ldd file to a file 
            # ~ lfr.to_gdal(ldd_lue, "ldd_lue_used.tif")
        
        self.modelTime = modelTime        
        # ~ self.model     = PCRGlobWB(configuration, modelTime, initialState, None, ldd_lue)
        

        # skip any reporting during LUE scalability experiment
        self.lue_scalability_experiment = False
        if configuration.globalOptions['lue_scalability_experiment'] == "True": self.lue_scalability_experiment = True
        
        if self.lue_scalability_experiment is False: self.reporting = Reporting(configuration, self.model, modelTime)
        
    def initial(self): 
        pass

    def dynamic(self):

        # ~ # re-calculate current model time using current pcraster timestep value
        # ~ self.modelTime.update(self.currentTimeStep())

        # ~ # update model (will pick up current model time from model time object)
        # ~ self.model.read_forcings()
        # ~ state = self.model.update(report_water_balance = False, lue_scalability_experiment = self.lue_scalability_experiment)

        # ~ assert state is not None
        
        # ~ # skip any reporting during LUE scalability experiment
        # ~ if self.lue_scalability_experiment is False: self.reporting = Reporting(configuration, self.model, modelTime)

        state = pcr.scalar(1.0)
        state.future().get()
        return state

@pcr.runtime_scope
def main(
    count: int,
    nr_workers: int,
    array_shape: tuple[int, int],
    partition_shape: tuple[int, int],
    result_pathname: str,
    centre: tuple[int, int]
    ):

    # print disclaimer
    disclaimer.print_disclaimer()
    
    # get the full path of configuration/ini file given in the system argument
    iniFileName   = os.path.abspath(sys.argv[1])
    
    # debug option
    debug_mode = False
    if len(sys.argv) > 2: 
        if sys.argv[2] == "debug": debug_mode = True
    
    # no modification in the given ini file, use it as it is
    no_modification = True
    
    # use the output directory, clone and ldd maps, as given in the system arguments
    if len(sys.argv) > 3 and sys.argv[3] == "--output_dir": 
        no_modification  = False
        output_directory = sys.argv[4]
        clone_map        = sys.argv[6]
        ldd_map          = sys.argv[8]
        print(clone_map)

    # object to handle configuration/ini file
    configuration = Configuration(iniFileName = iniFileName, \
                                  debug_mode = debug_mode, \
                                  no_modification = no_modification)      
    if no_modification == False:
        configuration.main_output_directory = output_directory
        configuration.globalOptions['outputDir'] = output_directory
        configuration.globalOptions['cloneMap']  = clone_map
        configuration.routingOptions['lddMap']   = ldd_map
        configuration.set_configuration()
        print(configuration.globalOptions['cloneMap'])
    
    # timeStep info: year, month, day, doy, hour, etc
    currTimeStep = ModelTime() 
    
    # skipping spin_up for lue experiment
    # - set initial_state to None, so it will be based on the configuration .ini file
    initial_state = None
    
    # get the number of time steps
    currTimeStep.getStartEndTimeSteps(configuration.globalOptions['startTime'],
                                      configuration.globalOptions['endTime'])


    # initializing the deterministic runner, including reading ldd
    deterministic_runner = DeterministicRunner(configuration, currTimeStep, initial_state, count, nr_workers, array_shape, partition_shape, result_pathname, centre)
    dynamic_framework = pcrfw.DynamicFramework(deterministic_runner,currTimeStep.nrOfTimeSteps)
    # ~ dynamic_framework.setQuiet(True)

    experiment = lqi.ArrayExperiment(nr_workers, array_shape, partition_shape)
    experiment.start()

    for _ in range(count):
        run = lqi.Run()
        run.start()

        if pcr.provider_name == "lue":
            dynamic_framework.run(rate_limit=2)
        else:
            dynamic_framework.run()

        # lfr.wait(generation) # dynamic() waits instead at last timestep...
        run.stop()
        experiment.add(run)

    experiment.stop()
    lqi.save_results(experiment, result_pathname)        


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--lue:count'          )
    parser.add_argument('--lue:nr_workers'     )
    parser.add_argument('--lue:array_shape'    )
    parser.add_argument('--lue:partition_shape')
    parser.add_argument('--lue:centre'         )
    parser.add_argument('--lue:result'         )

    args, unknown = parser.parse_known_args()

    count = int(vars(args)["lue:count"])
    nr_workers = int(vars(args)["lue:nr_workers"])
    e1, e2 = vars(args)["lue:array_shape"].replace("[","").replace("]","").split(",")
    array_shape = (int(e1),int(e2))
    s1, s2 = vars(args)["lue:partition_shape"].replace("[","").replace("]","").split(",")
    partition_shape = (int(s1),int(s2))
    result_pathname = vars(args)["lue:result"]
    c1, c2 = vars(args)["lue:centre"].replace("[","").replace("]","").split(",")
    centre = (int(c1),int(c2))

    sys.exit(main(count, nr_workers, array_shape, partition_shape, result_pathname, centre))

# ~ if __name__ == '__main__':
    # ~ # print disclaimer
    # ~ disclaimer.print_disclaimer(with_logger = True)
    # ~ sys.exit(main())
