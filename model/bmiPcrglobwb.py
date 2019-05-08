#! /usr/bin/env python
from configuration import Configuration
from pcrglobwb import PCRGlobWB
import pcraster as pcr
import numpy as np
from currTimeStep import ModelTime
import sys
import logging
from reporting import Reporting
from imagemean import downsample
from bmi import EBmi
from bmi import BmiGridType
import datetime
import os

logger = logging.getLogger(__name__)


class BmiPCRGlobWB(EBmi):
    #we use the same epoch as pcrglobwb netcdf reporting
    def days_since_industry_epoch(self, modeltime):
        return (modeltime - datetime.date(1901, 1, 1)).days

    def in_modeltime(self, days_since_industry_epoch):
        return (datetime.datetime(1901, 1, 1) + datetime.timedelta(days=days_since_industry_epoch)).date()

    def calculate_shape(self):
        # return pcr.pcr2numpy(self.model.landmask, 1e20).shape
        return (pcr.clone().nrRows(), pcr.clone().nrCols())

    #BMI initialize (as a single step)
    def initialize(self, fileName):
        self.initialize_config(fileName)
        self.initialize_model()

    #EBMI initialize (first step of two)
    def initialize_config(self, fileName):
        logger.info("PCRGlobWB: initialize_config")

        try:

            self.configuration = Configuration(fileName, relative_ini_meteo_paths = True)
            pcr.setclone(self.configuration.cloneMap)

            # set start and end time based on configuration
            self.model_time = ModelTime()
            self.model_time.getStartEndTimeSteps(self.configuration.globalOptions['startTime'],
                                             self.configuration.globalOptions['endTime'])

            self.model_time.update(0)

            self.shape = self.calculate_shape()

            logger.info("Shape of maps is %s", str(self.shape))

            self.model = None

        except:
            import traceback
            traceback.print_exc()
            raise


    #EBMI initialize (second step of two)
    def initialize_model(self):
        if self.model is not None:
            #already initialized
            return

        try:

            logger.info("PCRGlobWB: initialize_model")

            initial_state = None
            self.model = PCRGlobWB(self.configuration, self.model_time, initial_state)

            self.reporting = Reporting(self.configuration, self.model, self.model_time)

            logger.info("Shape of maps is %s", str(self.shape))

            logger.info("PCRGlobWB Initialized")

        except:
            import traceback
            traceback.print_exc()
            raise



    def update(self):
        timestep = self.model_time.timeStepPCR

        self.model_time.update(timestep + 1)

        self.model.read_forcings()
        self.model.update(report_water_balance=True)
        self.reporting.report()

    #         #numpy = pcr.pcr2numpy(self.model.landSurface.satDegUpp000005, 1e20)
    #         numpy = pcr.pcr2numpy(self.model.landSurface.satDegUpp000005, np.NaN)
    #         print numpy.shape
    #         print numpy


    def update_until(self, time):
        while self.get_current_time() + 0.001 < time:
            self.update()

    def update_frac(self, time_frac):
        raise NotImplementedError

    def finalize(self):
        pass

    def get_component_name(self):
        return "pcrglobwb"

    def get_input_var_names(self):
        return ["top_layer_soil_saturation"]

    def get_output_var_names(self):
        return ["top_layer_soil_saturation"]

    def get_var_type(self, long_var_name):
        return 'float64'

    def get_var_units(self, long_var_name):
        #TODO: this is not a proper unit
        return '1'

    def get_var_rank(self, long_var_name):
        return 0

    def get_var_size(self, long_var_name):
        return np.prod(self.get_grid_shape(long_var_name))

    def get_var_nbytes(self, long_var_name):
        return self.get_var_size(long_var_name) * np.float64.itemsize

    def get_start_time(self):
        return self.days_since_industry_epoch(self.model_time.startTime)

    def get_current_time(self):
        return self.days_since_industry_epoch(self.model_time.currTime)

    def get_end_time(self):
        return self.days_since_industry_epoch(self.model_time.endTime)

    def get_time_step(self):
        return 1

    def get_time_units(self):
        return "Days since 1901-01-01"

    def get_value(self, long_var_name):
        logger.info("getting value for var %s", long_var_name)

        if (long_var_name == "top_layer_soil_saturation"):

            if self.model is not None and hasattr(self.model.landSurface, 'satDegUpp000005'):

                #first make all NanS into 0.0 with cover, then cut out the model using the landmask.
                # This should not actually make a difference.
                remasked = pcr.ifthen(self.model.landmask, pcr.cover(self.model.landSurface.satDegUpp000005, 0.0))

                pcr.report(self.model.landSurface.satDegUpp000005, "value.map")
                pcr.report(remasked, "remasked.map")

                value = pcr.pcr2numpy(remasked, np.NaN)

            else:
                logger.info("model has not run yet, returning empty state for top_layer_soil_saturation")
                value = pcr.pcr2numpy(pcr.scalar(0.0), np.NaN)

            # print "getting var", value
            # sys.stdout.flush()

            doubles = value.astype(np.float64)

            # print "getting var as doubles!!!!", doubles

            result = np.flipud(doubles)

            # print "getting var as doubles flipped!!!!", result
            # sys.stdout.flush()

            return result
        else:
            raise Exception("unknown var name" + long_var_name)

    def get_value_at_indices(self, long_var_name, inds):
        raise NotImplementedError

    #     def get_satDegUpp000005_from_observation(self):
    #
    #         # assumption for observation values
    #         # - this should be replaced by values from the ECV soil moisture value (sattelite data)
    #         # - uncertainty should be included here
    #         # - note that the value should be between 0.0 and 1.0
    #         observed_satDegUpp000005 = pcr.min(1.0,\
    #                                    pcr.max(0.0,\
    #                                    pcr.normal(pcr.boolean(1)) + 1.0))
    #         return observed_satDegUpp000005

    def set_satDegUpp000005(self, src):
        mask = np.isnan(src)
        src[mask] = 1e20
        observed_satDegUpp000005 = pcr.numpy2pcr(pcr.Scalar, src, 1e20)

        pcr.report(observed_satDegUpp000005, "observed.map")

        constrained_satDegUpp000005 = pcr.min(1.0, pcr.max(0.0, observed_satDegUpp000005))

        pcr.report(constrained_satDegUpp000005, "constrained.map")

        pcr.report(self.model.landSurface.satDegUpp000005, "origmap.map")
        diffmap = constrained_satDegUpp000005 - self.model.landSurface.satDegUpp000005
        pcr.report(diffmap, "diffmap.map")

        # ratio between observation and model
        ratio_between_observation_and_model = pcr.ifthenelse(self.model.landSurface.satDegUpp000005 > 0.0,
                                                             constrained_satDegUpp000005 / \
                                                             self.model.landSurface.satDegUpp000005, 0.0)

        # updating upper soil states for all lad cover types
        for coverType in self.model.landSurface.coverTypes:
            # correcting upper soil state (storUpp000005)
            self.model.landSurface.landCoverObj[coverType].storUpp000005 *= ratio_between_observation_and_model

            # if model value = 0.0, storUpp000005 is calculated based on storage capacity (model parameter) and observed saturation degree   
            self.model.landSurface.landCoverObj[coverType].storUpp000005 = pcr.ifthenelse(
                self.model.landSurface.satDegUpp000005 > 0.0, \
                self.model.landSurface.landCoverObj[coverType].storUpp000005, \
                constrained_satDegUpp000005 * self.model.landSurface.parameters.storCapUpp000005)
            # correct for any scaling issues (value < 0 or > 1 do not make sense
            self.model.landSurface.landCoverObj[coverType].storUpp000005 = pcr.min(1.0, pcr.max(0.0,
                                                                                                self.model.landSurface.landCoverObj[
                                                                                                    coverType].storUpp000005))

    def set_value(self, long_var_name, src):

        if self.model is None or not hasattr(self.model.landSurface, 'satDegUpp000005'):
            logger.info("cannot set value for %s, as model has not run yet.", long_var_name)
            return

        logger.info("setting value for %s", long_var_name)

        # logger.info("dumping state to %s", self.configuration.endStateDir)
        # self.model.dumpStateDir(self.configuration.endStateDir + "/pre/")

        # print "got value to set", src

        # make sure the raster is the right side up
        src = np.flipud(src)

        # print "flipped", src

        # cast to pcraster precision
        src = src.astype(np.float32)

        # print "as float 32", src

        sys.stdout.flush()

        logger.info("setting value shape %s", src.shape)

        if (long_var_name == "top_layer_soil_saturation"):
            self.set_satDegUpp000005(src)
        else:
            raise Exception("unknown var name" + long_var_name)

        # write state here to facilitate restarting tomorrow
        # logger.info("dumping state to %s", self.configuration.endStateDir)
        # self.model.dumpStateDir(self.configuration.endStateDir + "/post/")

    def set_value_at_indices(self, long_var_name, inds, src):
        raise NotImplementedError

    def get_grid_type(self, long_var_name):
        return BmiGridType.UNIFORM

    def get_grid_shape(self, long_var_name):
        return

    def get_grid_shape(self, long_var_name):
        return self.shape

    def get_grid_spacing(self, long_var_name):

        cellsize = pcr.clone().cellSize()

        return np.array([cellsize, cellsize])

    def get_grid_origin(self, long_var_name):

        north = pcr.clone().north()
        cellSize = pcr.clone().cellSize()
        nrRows = pcr.clone().nrRows()

        south = north - (cellSize * nrRows)

        west = pcr.clone().west()

        return np.array([south, west])

    def get_grid_x(self, long_var_name):
        raise ValueError

    def get_grid_y(self, long_var_name):
        raise ValueError

    def get_grid_z(self, long_var_name):
        raise ValueError

    def get_grid_connectivity(self, long_var_name):
        raise ValueError

    def get_grid_offset(self, long_var_name):
        raise ValueError

    #EBMI functions

    def set_start_time(self, start_time):
        self.model_time.setStartTime(self.in_modeltime(start_time))

    def set_end_time(self, end_time):
        self.model_time.setEndTime(self.in_modeltime(end_time))

    def get_attribute_names(self):
        raise NotImplementedError

    def get_attribute_value(self, attribute_name):
        raise NotImplementedError

    def set_attribute_value(self, attribute_name, attribute_value):
        raise NotImplementedError

    def save_state(self, destination_directory):
        logger.info("saving state to %s", destination_directory)
        self.model.dumpStateDir(destination_directory)

    def load_state(self, source_directory):
        raise NotImplementedError



class ScaledBmiPCRGlobWB(BmiPCRGlobWB):
    factor = 5

    def set_value(self, long_var_name, scaled_new_value):
        # small value for comparison
        current_value = self.get_value(long_var_name)

        print 'current value after scaling', current_value

        print 'value given by user', scaled_new_value

        diff = scaled_new_value - current_value

        print "diff now", diff

        # scale to model resolution
        big_diff = np.repeat(np.repeat(diff, self.factor, axis=0), self.factor, axis=1)

        big_current_value = BmiPCRGlobWB.get_value(self, long_var_name)

        new_value = big_current_value + big_diff

        # new_value = np.repeat(np.repeat(src, self.factor, axis=0), self.factor, axis=1)

        BmiPCRGlobWB.set_value(self, long_var_name, new_value)

    def calculate_shape(self):
        original = BmiPCRGlobWB.calculate_shape(self)

        logger.info("original shape !!! =" + str(original))

        return np.array([original[0] // self.factor, original[1] // self.factor])

    def get_value(self, long_var_name):
        big_map = BmiPCRGlobWB.get_value(self, long_var_name)

        print "getting value original shape " + str(big_map.shape)
        print "original size " + str(big_map.size)
        print "nans in original " + str(np.count_nonzero(np.isnan(big_map)))

        result = np.zeros(shape=self.get_grid_shape(long_var_name))

        downsample(big_map, result)

        print "getting value new shape " + str(result.shape)
        print "result size " + str(result.size)
        print "nans count in result " + str(np.count_nonzero(np.isnan(result)))

        print "getting value", result
        sys.stdout.flush()

        return result

    def get_grid_spacing(self, long_var_name):
        cellsize = pcr.clone().cellSize()

        return np.array([cellsize * self.factor, cellsize * self.factor])
