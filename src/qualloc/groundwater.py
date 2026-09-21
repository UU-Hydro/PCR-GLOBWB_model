# groundwater module of the QUAlloc model

# modules
import logging

import pcraster as pcr

# global attributes

logger = logging.getLogger(__name__)

NoneType = type(None)

# functions
def compute_daily_base_flow(alpha, base_flow, recharge):

    '''
    compute_daily_base_flow:
    function that computes the new base flow given the recession constant alpha and
    the current base flow and recharge as flows per day; returns the new base flow.
    All input is expected to be compatible with PCRaster scalar maps.
    '''
    
    k_factor = pcr.exp(-alpha * pcr.spatial(pcr.scalar(1)))
    return k_factor * base_flow + (1.0 - k_factor) * recharge

# class

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
    
    def __init__(self, \
                  alpha, \
                  total_base_flow_ini, \
                  storage_ini):
        
        # initialize the object
        object.__init__(self)
        
        # groundwater alpha [day**-1]
        self.alpha = alpha
        
        # states and fluxes
        # initial groundwater storage (units: m/day)
        self.storage = storage_ini
        # recharge (units: m/day)
        self.total_recharge = pcr.ifthen(pcr.defined(self.alpha), \
                                         pcr.scalar(0)) 
        # base flow (units: m/period)
        self.total_base_flow = pcr.ifthen(pcr.defined(self.alpha), \
                                         pcr.scalar(total_base_flow_ini))
        # set the state names
        self.report_state_info = {'total_recharge'     : 'total_recharge', \
                                  'total_base_flow'     : 'total_base_flow', \
                                  'groundwater_storage' : 'storage'}
        
        # returns none
        return None
    
    def __str__(self):
        return 'this is the groundwater module of the QUAlloc model.'
    
    def get_storage(self, \
                     recharge, \
                     potential_withdrawal, \
                     time_step_length, \
                     date):
        
        '''
        get_storage          : function to calculate the groundwater storage based
                               on the total recharge [ and the potential withdrawal ]
                               for the given time step length in days
        
        input:
        =====
        recharge             : PCRaster map with groundwater recharge (units: m/day)
        potential_withdrawal : PCRaster map with sum of renewable and non-renewable
                               potential withdrawals of all sectors (units: m/day)
        time_step_length     : integer, number of days in period (e.g., 30 days/month)
        date                 : string, date under evaluation
        '''
        
        # echo to screen
        logger.info('update groundwater module for %s' % date)
        
        # set the total recharge (units: m/day)
        self.recharge = recharge
        
        # set the recharge (units: m/period)
        self.total_recharge = self.recharge * time_step_length
        
        # set the actual recharge (units: m/day)
        actual_recharge = self.recharge - potential_withdrawal
        
        # set the base flow (units: m/day)
        self.base_flow = self.alpha * self.storage
        
        # initialize the total base flow (units: m/period)
        self.total_base_flow = pcr.ifthen(pcr.defined(self.alpha), \
                                         pcr.scalar(0))
        
        # update the total base flow at the end of the period
        # (units: m/period)
        for day in range(time_step_length):
            self.base_flow = pcr.max(0, \
                               compute_daily_base_flow(self.alpha, \
                                                      self.base_flow, \
                                                      actual_recharge))
            self.total_base_flow = self.total_base_flow + self.base_flow
        
        # return None
        return None
    
    def update(self, \
                renewable_withdrawal, \
                nonrenewable_withdrawal):
        '''
        update                  : function to update the groundwater storage at the
                                  end of the period, accounting for the water withdrawals
        
        input:
        =====
        renewable_withdrawal,
        nonrenewable_withdrawal : PCRaster map with actual groundwater renewable and non-
                                  renewable withdrawals (units: m/period)
        '''
        # subtract the withdrawal from the storage (units: m/period)
        self.storage = self.storage \
                       + self.total_recharge - self.total_base_flow \
                       - renewable_withdrawal - nonrenewable_withdrawal
        
        # return None
        return None
    
    def get_final_conditions(self):
        '''
        get_final_conditions: 
        function that returns a dictionary holding all states and fluxes 
        of the soil hydrology module that are necessary for a restart.
        
        Returns 'state_info', a dictionary with the key and the value
        '''
        
        # initialize states
        state_info = {}
        
        # iterate over the report name and attribute name
        for report_name, attr_name in self.report_state_info.items():
        
            # set the state
            state_info[report_name] = getattr(self, attr_name)
        
        # return results
        return state_info

# end of the groundwater class
