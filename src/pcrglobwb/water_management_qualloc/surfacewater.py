# surface water module of the QUAlloc model

# modules
import logging
import pcraster as pcr

try:
    from .basic_functions import pcr_return_val_div_zero, pcr_get_map_value
    from .model_time      import match_date_by_julian_number
except:
    from basic_functions import pcr_return_val_div_zero, pcr_get_map_value
    from model_time      import match_date_by_julian_number

# global attributes
logger = logging.getLogger(__name__)
NoneType = type(None)

# class

class surfacewater(object):

    """
    surfacewater: class that holds the surface water component of the QUAlloc \
    model.
    
    1initial states and fluxes:
    discharge:              initial discharge [m3/s]
    
    variables:
    ==========
    ldd:                    local drainage direction map [-]
    fraction_water:         fractional fresh water surface area [m2/m2]
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
    
    functions:
    ==========
    estimate_stage_from_discharge:
                            function which estimates the available storage from
                            the discharge.
    """
    
    def __init__(self, \
                  ldd, \
                  cellarea, \
                  fraction_water, \
                  water_cropfactor , \
                  channel_gradient, \
                  channel_width, \
                  channel_length, \
                  mannings_n, \
                  storage_ini, \
                  ):
        
        # initialize the object
        object.__init__(self)
        
        # parameters
        self.max_iterations    = 25
        self.convergence_limit = 1.0e-4
        self.beta              = 0.60
        
        # set the channel properties
        self.cellarea         = cellarea           # m2
        self.ldd              = pcr.lddrepair(ldd) # dimensionless
        self.fraction_water   = fraction_water     # m2/m2
        self.water_cropfactor = water_cropfactor   # dimensionless
        self.channel_gradient = channel_gradient   # m/m
        self.channel_width    = channel_width      # m
        self.channel_length   = channel_length     # m
        self.mannings_n       = mannings_n         # m^(-1/3)*s
        
        # limit the gradient to 1:10000000 and the channel width to 5 m
        self.channel_gradient = pcr.max(1.e-6, self.channel_gradient)
        self.channel_width    = pcr.max(5.000, self.channel_width)
        
        # states and fluxes
        # initial surface water storage (units: m)
        self.storage = storage_ini
        # channel discharge initialized
        self.discharge = pcr.ifthen(pcr.defined(self.ldd), pcr.scalar(0))
        
        # set the state names
        self.report_state_info = {'surfacewater_storage': 'storage', \
                                  'discharge'           : 'discharge'}
        
        # returns none
        return None
    
    def __str__(self):
        return 'this is the surface water module of the QUAlloc model.'
    
    def get_wetted_perimeter(self, channel_width, waterdepth):
        # returns the wetted perimeter for a rectangular channel (units: m)
        return channel_width + 2 * waterdepth
    
    def get_alpha(self, mannings_n, wetted_perimeter, channel_gradient, beta):
        # returns alpha of the equation A = alpha * Q ** beta
        return (mannings_n * wetted_perimeter ** (2.0/3.0) * channel_gradient ** -0.5) ** beta
    
    def estimate_waterdepth_from_discharge(self, discharge, waterdepth):
        '''
        estimate_waterdepth_from_discharge :
                     function to estimate the water depth at the end of the time-step
                     based on the discharge after water withdrawals and the channel parameters;
                     values is obtained by iteration, starting by the water depth of the
                     previous time-step
        
        input:
        =====
        discharge  : discharge at the end of the time-step, after water withdrawals
                     (units: m3/s)
        waterdepth : water depth at the start of the time-step (units: m)
        
        output:
        ======
        waterdepth : water depth at the end of the time-step based on the discharge
                     and the channel parameters (units: m)
        '''
        
        # set the mask where water is present (units: m3/s)
        discharge_mask = discharge > 0
        
        # set the number of iterations and convergence
        icnt = 0
        convergence = False
        
        # and iterate over all time steps
        while icnt < self.max_iterations and not convergence:
            
            # set the old water depth (units: m)
            waterdepth_old = pcr.max(0.001, waterdepth)
            
            # get the wetted perimeter and the corresponding alpha
            wetted_perimeter = self.get_wetted_perimeter(self.channel_width, waterdepth_old)
            alpha = self.get_alpha(self.mannings_n, wetted_perimeter, \
                                   self.channel_gradient, self.beta)
            
            # compute the new water depth (units: m)
            wetted_area = alpha * discharge ** self.beta
            waterdepth = pcr.max(0.001, wetted_area / self.channel_width)
            
            # compare the water depth
            conv_value  = pcr.cellvalue(pcr.mapmaximum(pcr.abs(waterdepth -  waterdepth_old)),1)[0]
            convergence = conv_value < self.convergence_limit
            
            # update icnt
            icnt = icnt + 1
        
        # set the water depth
        waterdepth = pcr.ifthenelse(discharge_mask, waterdepth, pcr.scalar(0))
        
        # set the message string
        message_str = 'water depth converged after %d iterations with a maximum deviation of %.3g' % (icnt, conv_value)
        logger.debug(message_str)
        
        # return water depth (units: m)
        return waterdepth
    
    
    
    def get_total_runoff(self, \
                         direct_runoff, \
                         interflow, \
                         base_flow, \
                         channel_runoff, \
                         return_flow, \
                         date = None, \
                         ):
        '''
        get_total_runoff: 
                        function to calculate the total runoff based on the different
                        surface water componentes: direct runoff and interflow over land;
                        channel runoff (net precipitation) over streams; base flow over
                        the entire area; and extra water incomes (return flows)
        
        input:
        =====
        direct_runoff  : PCRaster map with direct runoff values (units: m/day)
        interflow      : PCRaster map with interflow values (units: m/day)
        base_flow      : PCRaster map with base flow values (units: m/day)
        channel_runoff : PCRaster map with channel runoff values (units: m/day)
        return_flow    : PCRaster map with return runoff values (units: m/day)
        date          : string, date under evaluation
        
        output:
        ======
        total_runoff   : PCRaster map with sum of surface water components over their
                        correspondent matrices: overland and over-river (units: m/day)
        '''
        
        # echo to screen
        logger.info('update surface water module for %s' % date)
        
        # set the total runoff (units: m/day)
        # note:
        #  base flow over the entire area,
        #  direct runoff and interflow over the land area,
        #  channel runoff over the fresh water surface
        total_runoff = base_flow + \
                      (1.0 - self.fraction_water) * (direct_runoff + interflow) + \
                      self.fraction_water * channel_runoff
        
        # add the total return flow to the total runoff (units: m/day)
        total_runoff = total_runoff + return_flow
        
        # set variable
        # after limiting total runoff to positive values
        self.total_runoff = pcr.max(0, \
                                   total_runoff)
        
        # return total runoff (units: m/day)
        return None
    
    
    
    def update(self, \
                potential_withdrawal, \
                time_step_seconds = 86400, \
                ):
        '''
        update               : set variables in the object surfacewater useful
                               for the next time step
        
        input:
        =====
        potential_withdrawal : PCRaster map of sum of water withdrawals from all sector
                               (units: m3/day)
        time_step_seconds    : integer, number of second in a day (i.e., 86400 sec/day)
        
        output:
        ======
        discharge            : PCRaster map of channel discharge after total water withdrawals
                               (units: m3/s)
        actual_withdrawal    : PCRaster map of actual renewable surface water withdrawals to
                               meet sectoral potential surface water withdrawals (units: m3/day)
        '''
        
        # convert runoff units from water slice to volume per day
        # (units: m3/day)
        total_runoff  = self.total_runoff * self.cellarea
        
        # get actual withdrawal and the discharge (units: m3/day)
        actual_withdrawal = pcr.accuthresholdstate(self.ldd, \
                                                   total_runoff, \
                                                   potential_withdrawal)
        
        self.discharge    = pcr.accuthresholdflux(self.ldd, \
                                                 total_runoff, \
                                                 potential_withdrawal)
        
        # cover actual withdrawals to land mask extension
        actual_withdrawal = pcr.ifthen(pcr.defined(self.ldd), \
                                       actual_withdrawal)
        
        # convert discharge from days to senconds (units: m3/s)
        self.discharge = self.discharge / time_step_seconds
        
        # compute the storage (units: m)
        self.storage = self.estimate_waterdepth_from_discharge(self.discharge, \
                                                               self.storage)
        
        # return discharge (units: m3/s) and actual withdrawal (units: m3/day)
        return actual_withdrawal
    
    
    
    def get_final_conditions(self):
        '''
        get_final_conditions:
                     function that returns a dictionary holding all states and fluxes
                     of the soil hydrology module that are necessary for a restart
        
        output:
        ======
        state_info : dictionary with the key and the value
        '''
        
        # initialize states
        state_info = {}
        
        # iterate over the report name and attribute name
        for report_name, attr_name in self.report_state_info.items():
        
            # set the state
            state_info[report_name] = getattr(self, attr_name)
        
        # return results
        return state_info

# end of the surface water class
