import logging
import sys

import pcraster as pcr

from pcrglobwb.water_demand import (
    domestic_water_demand,
    industry_water_demand,
    irrigation_water_demand,
    livestock_water_demand,
    manufacture_water_demand,
    thermoelectric_water_demand,
)

logger = logging.getLogger(__name__)


class WaterDemand(object):

    def __init__(self, iniItems, landmask, landCoverTypeNames, landCoverObjects):
        object.__init__(self)

        self.cloneMap = iniItems.cloneMap
        self.tmpDir = iniItems.tmpDir
        self.inputDir = iniItems.globalOptions["inputDir"]
        self.landmask = landmask

        # check that the industry, manufacturing and thermoelectric sectors are consistent
        if (
            iniItems.waterDemandOptions["includeIndustryWaterDemand"] == "True"
            and iniItems.waterDemandOptions["includeManufactureWaterDemand"] == "True"
            and iniItems.waterDemandOptions["includeThermoelectricWaterDemand"]
            == "True"
        ):

            msg = "\nIndustry, Manufacturing and Thermoelectric water use sectors are included in the calculations.\n"
            msg += "Industrial demands already account for Manufacturing and Thermoelectric, thus water demands will be double counted.\n"
            msg += 'Set either "includeIndustryWaterDemand" to "False" or\n'
            msg += '           "includeManufactureWaterDemand" and "includeThermoelectricWaterDemand" to "False".'
            logger.warning(msg)
            sys.exit()

        self.water_demand_domestic = domestic_water_demand.DomesticWaterDemand(
            iniItems, self.landmask
        )
        self.water_demand_industry = industry_water_demand.IndustryWaterDemand(
            iniItems, self.landmask
        )
        self.water_demand_livestock = livestock_water_demand.LivestockWaterDemand(
            iniItems, self.landmask
        )
        self.water_demand_manufacture = manufacture_water_demand.ManufactureWaterDemand(
            iniItems, self.landmask
        )
        self.water_demand_thermoelectric = (
            thermoelectric_water_demand.ThermoelectricWaterDemand(
                iniItems, self.landmask
            )
        )

        # irrigation water demand objects, one per irrigation land cover type ("irr*")
        self.water_demand_irrigation = {}
        self.coverTypes = landCoverTypeNames
        for coverType in self.coverTypes:
            if coverType.startswith("irr"):
                self.water_demand_irrigation[coverType] = (
                    irrigation_water_demand.IrrigationWaterDemand(
                        iniItems,
                        coverType + str("Options"),
                        self.landmask,
                        landCoverObjects[coverType],
                    )
                )

    def update(self, meteo, landSurface, groundwater, routing, currTimeStep):

        # non-irrigation demand (m); based on landSurface.py
        self.water_demand_domestic.update(currTimeStep)
        self.water_demand_industry.update(currTimeStep)
        self.water_demand_livestock.update(currTimeStep)
        self.water_demand_manufacture.update(currTimeStep)

        if routing.quality:
            self.water_demand_thermoelectric.update(
                currTimeStep, routing=routing, read_file=False
            )
        else:
            self.water_demand_thermoelectric.update(currTimeStep)

        # irrigation demand (m/day) per irrigation land cover type
        for coverType in self.coverTypes:
            if coverType.startswith("irr"):
                self.water_demand_irrigation[coverType].update(
                    meteo, landSurface, groundwater, routing, currTimeStep
                )

        # irrigation demand volume (m3)
        self.total_vol_irrigation_demand = pcr.scalar(0.0)
        for coverType in self.coverTypes:
            if coverType.startswith("irr"):
                self.total_vol_irrigation_demand = (
                    self.total_vol_irrigation_demand
                    + self.water_demand_irrigation[coverType].irrGrossDemand
                    * routing.cellArea
                )
