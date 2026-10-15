import logging

import pcraster as pcr

logger = logging.getLogger(__name__)

NoneType = type(None)


class groundwater(object):
    """
    groundwater: class that holds the groundwater component of the QUAlloc
                 model

    initial states and fluxes:
    ==========================
    total_baseflow_ini       : initial base flow from the cell as a total,
                              e.g per month [m3/m2/month = m/month]
    groundwater_storage_ini : initial groundwater storage in water slice [m]
                              over the cell area
    """

    def __init__(self, landmask, total_base_flow_ini, storage_ini):

        object.__init__(self)

        # initial groundwater storage (m)
        self.storage = storage_ini
        # recharge (m/day)
        self.total_recharge = pcr.ifthen(landmask, pcr.scalar(0))
        # base flow (m/period)
        self.total_base_flow = pcr.ifthen(landmask, pcr.scalar(total_base_flow_ini))
        self.report_state_info = {
            "total_recharge": "total_recharge",
            "total_base_flow": "total_base_flow",
            "groundwater_storage": "storage",
        }

        return None

    def __str__(self):
        return "this is the groundwater module of the QUAlloc model."

    def get_final_conditions(self):
        """
        get_final_conditions:
        function that returns a dictionary holding all states and fluxes
        of the soil hydrology module that are necessary for a restart.

        Returns 'state_info', a dictionary with the key and the value
        """

        state_info = {}

        for report_name, attr_name in self.report_state_info.items():

            state_info[report_name] = getattr(self, attr_name)

        return state_info
