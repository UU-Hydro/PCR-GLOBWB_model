"""

qualloc_runner.py: main file that runs the QUAlloc model that emulates \
the large-scale hydrological model PCR-GLOBWB 2; \
requires a configuration file that is entered on the command line.

"""

# TODO: move spinup to separate class to reduce the size of this runner
# TODO: include general settings for spinup as global variables for easy adaptation

###########
# modules #
###########
# general modules and packages
import os
import sys
import logging

import pcraster as pcr
from pcraster.multicore import set_nr_worker_threads
from pcraster.framework import DynamicModel
from pcraster.framework import DynamicFramework

# specific packages
from qualloc.model_configuration import configuration_parser
from qualloc.model_time import model_time
from qualloc.qualloc_main import qualloc_model
from qualloc.qualloc_reporting import qualloc_reporting

########
# TODO #
########
critical_improvements= str.join('\n',\
             ( \
              '', \
              ))

development= str.join('\n\t',\
             ( \
              '',\
              ))
if len(critical_improvements) > 0 or len(development) > 0:
    print ('\nDevelopments for qualloc_runner:')

if len(critical_improvements) > 0:
    print('Critical improvements: \n%s' % \
          critical_improvements)

if len(development) > 0:
    print ('Ongoing: \n%s' % development)

if len(critical_improvements) > 0:
    sys.exit()

####################
# global variables #
####################

# multicore number of workers
set_nr_worker_threads(4)

# type set to identify None (compatible with pytyon 2.x)
NoneType = type(None)

# inherit logger and start afresh
logger = logging.getLogger(__name__)

# allowed time increments, currently monthly and daily
allowed_time_increments = ['monthly','daily']

# command line flags and the configuration file placeholders they fill; the
# names match those of pcrglobwb's run-with-arguments so that a coupled run
# can pass the same values to both models
argument_tokens = { \
                   '-mid'           : 'MAIN_INPUT_DIR', \
                   '-mod'           : 'MAIN_OUTPUT_DIR', \
                   '-clonemap'      : 'CLONEMAP', \
                   '-pcrglobwb_mod' : 'PCRGLOBWB_OUTPUT_DIR', \
                  }

#==============================================================================
class qualloc_runner(DynamicModel):
    
    def __init__(self, model_configuration, model_time, \
                 model_flags = {}, initial_conditions = None):
        DynamicModel.__init__(self)
        
        # initialization
        self.model_configuration = model_configuration
        self.model_time = model_time
        self.model = qualloc_model(self.model_configuration, \
                                   self.model_time, \
                                   model_flags, \
                                   initial_conditions)
        self.reporting = qualloc_reporting(self.model_configuration)
        
        # returns None
        return None
    
    def initial(self):
        
        # initialize the model
        self.model.initialize()
        
        # initialize the reports
        self.reporting.initialize()
        
        # returns None
        return None
    
    def dynamic(self):
        
        # update the timer
        self.model_time.update(self.currentTimeStep())
        
        # update the model
        self.model.update()
        
        # report all variables
        self.reporting.report(self.model_time, self.model)
        
        if self.model_time.report_flags['yearly']:
            # additional processing at the end of year:
            # report the states, so the run can be restarted
            # as a safeguard and to reduce the initial states
            self.model.finalize_year()
        
        # last time step
        if self.model_time.last_time_step:
            
            # close down all files open for input and output
            self.model.finalize_run()
            self.reporting.close()
            
            # return the warm states
            return self.model.initial_conditions

#==============================================================================

########
# MAIN #
########

def main():
    # parses options and arguments from the command line, including the configuration file
    # and runs the model script
    
    # split the command line into the flags of argument_tokens and the
    # remaining arguments: the configuration file, followed by the positional
    # substitution arguments
    replacements = {}
    arguments    = []
    
    system_argument = sys.argv[1:]
    argument_cnt    = 0
    
    while argument_cnt < len(system_argument):
        
        argument = system_argument[argument_cnt]
        
        if argument in argument_tokens:
            
            if argument_cnt + 1 == len(system_argument):
                sys.exit('%s is not followed by a value' % argument)
            
            replacements[argument_tokens[argument]] = \
                system_argument[argument_cnt + 1]
            argument_cnt += 2
        
        else:
            arguments.append(argument)
            argument_cnt += 1
    
    # substargs is a list of possible substitution arguments that can be used
    # to make the input file more generic.
    subst_args = []
    
    # passing the arguments; note that the error is currently disabled!
    if len(arguments) < 1:
        cfgfilename = 'qualloc_basic_setup.cfg'
    
    else:
        cfgfilename = arguments[0]
        subst_args = arguments[1:]
    cfgfilename = os.path.abspath(cfgfilename)
    
    # set the configuration object
    # object to handle configuration/ini file
    sections = ['general', 'time', 'forcing', 'groundwater', 'surfacewater', \
                'water_management','water_quality']
    groups= []
    model_configuration = configuration_parser(cfgfilename = cfgfilename, \
                                             sections   = sections, \
                                             groups     = groups, \
                                             subst_args = subst_args, \
                                             replacements = replacements)
    # change to the scratch path
    os.chdir(model_configuration.temppath)
    
    # initialize the time object:
    # note that thisis called pcr_time here and is recast
    # to model_time in the dynamic model and dependent modules
    startyear      = int(model_configuration.time['startyear'])
    endyear        = int(model_configuration.time['endyear'])
    time_increment = model_configuration.time['time_increment']
    
    # check on values
    if not time_increment in allowed_time_increments:
        message_str = ''
        message_str = str.join(' ', \
                       ('time increment %s is invalid,' % time_increment,\
                        'any of the following allowed:', \
                        str.join(', ', allowed_time_increments)))
        logger.error(message_str)
        sys.exit()
    
    # initialize the time increment
    pcr_time = model_time(startyear, endyear, time_increment)
    
    # dummy values for the model flags and initial conditions
    # initial conditions are initialized from the configuration file at the
    # start if set to None; otherwise, the existing warm states are used
    model_flags = {}
    initial_conditions = None
    
    # initialize dynamic model and run
    qualloc_instance = qualloc_runner( \
                                      model_configuration, \
                                      pcr_time, \
                                      model_flags, \
                                      initial_conditions)
    
    qualloc_model  = DynamicFramework( \
                                      qualloc_instance, \
                                      lastTimeStep = pcr_time.number_time_steps, \
                                      firstTimestep = 1)
    qualloc_model.setQuiet(True)
    initial_conditions = qualloc_model.run()
    
    # close logger files and change directory
    logging.shutdown()
    os.chdir(model_configuration.start_root_path)

########
# main #
########
if __name__ == '__main__':
    main()
    logging.shutdown()
    print ('all done')
