import logging

import pcraster as pcr

logger = logging.getLogger(__name__)
NoneType = type(None)


class surfacewater(object):
    """
    surfacewater: class that holds the surface water component of the QUAlloc \
    model.

    1initial states and fluxes:
    discharge:              initial discharge [m3/s]

    variables:
    ==========
    ldd:                    local drainage direction map [-]
    channel_gradient:       gradient along the channel [m/m]
    channel_width:          width for a rectangular channel [m]
    channel_length:         channel length [m]
    mannings_n:             manning's coefficient [m^-1/3*s]

    initial states and fluxes:
    ==========================
    surfacewater_storage_ini:
                            initial surface water storage in water slice [m]
                            over the fresh water surface of the cell
                            channelStorage_monthAvg_output
    """

    def __init__(
        self,
        ldd,
        channel_gradient,
        channel_width,
        channel_length,
        mannings_n,
        storage_ini,
    ):

        object.__init__(self)

        # local drainage direction (-)
        self.ldd = pcr.lddrepair(ldd)
        # channel gradient (m/m)
        self.channel_gradient = channel_gradient
        # channel width (m)
        self.channel_width = channel_width
        # channel length (m)
        self.channel_length = channel_length
        # Manning's n (m-1/3.s)
        self.mannings_n = mannings_n

        # limit the gradient to 1e-6 and the channel width to 5 m
        self.channel_gradient = pcr.max(1.0e-6, self.channel_gradient)
        self.channel_width = pcr.max(5.000, self.channel_width)

        # initial surface water storage (m)
        self.storage = storage_ini
        self.discharge = pcr.ifthen(pcr.defined(self.ldd), pcr.scalar(0))

        self.report_state_info = {
            "surfacewater_storage": "storage",
            "discharge": "discharge",
        }

        return None

    def __str__(self):
        return "this is the surface water module of the QUAlloc model."

    def get_final_conditions(self):
        """
        get_final_conditions:
                     function that returns a dictionary holding all states and fluxes
                     of the soil hydrology module that are necessary for a restart

        output:
        ======
        state_info : dictionary with the key and the value
        """

        state_info = {}

        for report_name, attr_name in self.report_state_info.items():

            state_info[report_name] = getattr(self, attr_name)

        return state_info
