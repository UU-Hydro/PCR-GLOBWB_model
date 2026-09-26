import glob
import logging
import math
import os
import shutil

from pcrglobwb.common import virtualOS as vos

logger = logging.getLogger(__name__)


class SpinUp(object):

    def __init__(self, iniItems):
        object.__init__(self)

        self.noSpinUps = None

        # number of soil layers (excluding groundwater)
        self.numberOfLayers = int(
            iniItems.landSurfaceOptions["numberOfUpperSoilLayers"]
        )

        # option to save the netCDF files of the latest spin-up cycle
        self.spinUpOutputDir = None
        if "spinUpOutputDir" in list(iniItems.globalOptions.keys()):
            self.outNCDir = str(iniItems.outNCDir)
            if iniItems.globalOptions["spinUpOutputDir"] not in ["None", "False"]:
                self.spinUpOutputDir = vos.getFullPath(
                    iniItems.globalOptions["spinUpOutputDir"], self.outNCDir
                )
            if iniItems.globalOptions["spinUpOutputDir"] == "True":
                self.spinUpOutputDir = self.outNCDir + "/spin-up/"

        self.setupConvergence(iniItems)

    def setupConvergence(self, iniItems):

        self.noSpinUps = int(iniItems.globalOptions["maxSpinUpsInYears"])

        self.minConvForTotlSto = float(iniItems.globalOptions["minConvForTotlSto"])
        self.minConvForSoilSto = float(iniItems.globalOptions["minConvForSoilSto"])
        self.minConvForGwatSto = float(iniItems.globalOptions["minConvForGwatSto"])
        self.minConvForChanSto = float(iniItems.globalOptions["minConvForChanSto"])

        # TODO: including the convergence of ResvSto (reservoir storage)

        # directory for end states (PCRaster maps)
        self.endStateDir = iniItems.endStateDir

    def soilStorageVolume(self, state, cellAreaMap):

        if self.numberOfLayers == 2:
            # (m3)
            return vos.getMapVolume(
                state["landSurface"]["topWaterLayer"]
                + state["landSurface"]["storUpp"]
                + +state["landSurface"]["storLow"]
                + state["groundwater"]["storGroundwater"],
                cellAreaMap,
            )

        if self.numberOfLayers == 3:
            # (m3)
            return vos.getMapVolume(
                state["landSurface"]["topWaterLayer"]
                + state["landSurface"]["storUpp000005"]
                + state["landSurface"]["storUpp005030"]
                + state["landSurface"]["storLow030150"]
                + state["groundwater"]["storGroundwater"],
                cellAreaMap,
            )

    def groundwaterStorageVolume(self, state, cellAreaMap):
        # (m3)
        return vos.getMapVolume(state["groundwater"]["storGroundwater"], cellAreaMap)

    def channelStorageVolume(self, state, cellAreaMap):
        # (m3)
        return vos.getMapVolume(state["routing"]["channelStorage"], cellAreaMap)

    def totalStorageVolume(self, state, cellAreaMap):
        # (m3)
        return (
            self.soilStorageVolume(state, cellAreaMap)
            + self.groundwaterStorageVolume(state, cellAreaMap)
            + vos.getMapVolume(
                state["landSurface"]["interceptStor"]
                + state["landSurface"]["snowFreeWater"]
                + state["landSurface"]["snowCoverSWE"],
                cellAreaMap,
            )
        )

    def checkConvergence(self, beginState, endState, spinUpRun, cellAreaMap):

        beginSoilSto = max(1e-20, self.soilStorageVolume(beginState, cellAreaMap))
        endSoilSto = self.soilStorageVolume(endState, cellAreaMap)

        convSoilSto = math.fabs(100 * (endSoilSto - beginSoilSto) / beginSoilSto)

        logger.info(
            "Delta SoilStorage = %.2f percent ; SpinUp No. %i of %i"
            % (convSoilSto, spinUpRun, self.noSpinUps)
        )

        beginGwatSto = max(
            1e-20, self.groundwaterStorageVolume(beginState, cellAreaMap)
        )
        endGwatSto = self.groundwaterStorageVolume(endState, cellAreaMap)

        convGwatSto = math.fabs(100 * (endGwatSto - beginGwatSto) / beginGwatSto)

        logger.info("Delta GwatStorage = %.2f percent" % (convGwatSto))

        beginChanSto = max(1e-20, self.channelStorageVolume(beginState, cellAreaMap))
        endChanSto = self.channelStorageVolume(endState, cellAreaMap)

        convChanSto = math.fabs(100 * (endChanSto - beginChanSto) / beginChanSto)

        logger.info("Delta ChanStorage = %.2f percent" % (convChanSto))

        beginTotlSto = max(1e-20, self.totalStorageVolume(beginState, cellAreaMap))
        endTotlSto = self.totalStorageVolume(endState, cellAreaMap)

        convTotlSto = math.fabs(100 * (endTotlSto - beginTotlSto) / beginTotlSto)

        logger.info("Delta TotlStorage = %.2f percent" % (convTotlSto))

        if self.spinUpOutputDir is not None:
            logger.info(
                "Move all netcdf files resulted from the spin-up run to the spin-up directory: "
                + self.spinUpOutputDir
            )

            # clean up the spin-up directory
            if os.path.exists(self.spinUpOutputDir):
                shutil.rmtree(self.spinUpOutputDir)
            os.makedirs(self.spinUpOutputDir)

            for filename in glob.glob(os.path.join(self.outNCDir, "*.nc")):
                shutil.move(filename, self.spinUpOutputDir)

        return (
            convSoilSto <= self.minConvForSoilSto
            and convGwatSto <= self.minConvForGwatSto
            and convChanSto <= self.minConvForChanSto
            and convTotlSto <= self.minConvForTotlSto
        )
