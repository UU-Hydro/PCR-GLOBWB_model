'''
Takes care of reporting(writing) output to netcdf files. Aggregates totals and averages for various time periods.

Created on Oct 24, 2013

@author: Niels Drost
'''
import logging

logger = logging.getLogger(__name__)

class Period(object):
    HOUR = 1
    DAY = 2
    WEEK = 3
    MONTH = 4
    YEAR = 5
    
class Statistic(object):
    END = 1
    AVERAGE = 2
    TOTAL = 3
    ROOT_MEAN_SQUARE = 4


class OutputVariable(object):
    
    def __init__(self, name, period, statistic, dataset):
        pass
        
    

class Reporting(object):

    #list of all output variables
    
    def __init__(self, configuration, model, modelTime):
        self._model = model
        self._modelTime = modelTime
        self._configuration = configuration

        #ask the configuration for settings
        
        
        
        #ask the model for descriptions of parameters
        
        #create netcdf files
        
        #set up total maps
        
    def report(self):
        logger.info("reporting for time %s", self._modelTime.currTime)
        

        
        