# allocation module of the QUAlloc model

# modules
import sys

from copy import deepcopy

import pcraster as pcr

try:
    from .basic_functions import pcr_return_val_div_zero, sum_list, pcr_get_statistics
except:
    from basic_functions import pcr_return_val_div_zero, sum_list, pcr_get_statistics

# global variables

# small number to avoid zero divisions in PCRaster
very_small_number = 1.0e-12

# type of None, compatible with python 2.6
NoneType = type(None)


########
# TODO #
########
critical_improvements= str.join('\n\t',\
             ( \
              '',\
              ))

development= str.join('\n\t',\
             ( \
              '', \
              ))

print ('\nDevelopmens for main module:')

if len(critical_improvements) > 0:
    print('Critical improvements: \n%s' % \
          critical_improvements)

if len(development) > 0:
    print ('Ongoing: \n%s' % development)

if len(critical_improvements) > 0:
    sys.exit()

#############
# functions #
#############

# get the key
def get_key(str_list):
    
    if isinstance(str_list, list):
        key = str_list[0]
    else:
        key = str(str_list)
    
    for ix in range(1, len(str_list)):
        
        if str_list[ix - 1] == '': d_str = '';
        else:                      d_str = '_'
        
        key = str.join(d_str, \
                       (key, str_list[ix]))

    # return the key
    return key

# the following are functions that are based the present allocation in
# PCR-GLOBWB and use aggregated values over zones using the PCRaster area...
# functions.

def get_zonal_total(local_values, zones):
        
    '''
get_zonal_fraction: function that computes the fractional value per cell over \
the total of the provided zones.

    Input:
    ======
    local values:            local cell values as a scalar PCRaster field;
    zones:                   zones over which the totals are computed as 
                             a nominal PCRaster field.
    
    Output:
    =======
    totals:                  totals over the zones per cell as a scalar
                             PCRaster field.

'''

    # compute the totals
    return pcr.areatotal(local_values, zones)
    
def get_zonal_fraction(local_values, zones):
        
    '''
get_zonal_fraction: function that computes the fractional value per cell over \
the total of the provided zones.

    Input:
    ======
    local values:            local cell values as a scalar PCRaster field;
    zones:                   zones over which the fractional values for the 
                             cells are computed as a nominal PCRaster field.
    
    Output:
    =======
    fractional_values:       fractional values, summing to unity over the ap-
                             propriate zone, as a scalar PCRaster field.

'''

    # compute the totals
    totals = get_zonal_total(local_values, zones)
    
    fractional_values = pcr_return_val_div_zero(local_values, totals, \
                                                very_small_number)

    # return the fractional values
    return fractional_values

def obtain_allocation_ratio( \
                            demand, \
                            availability, \
                            zones, \
                            source_names, \
                            ):
    
    '''
    
    Input:
    ======
    demand:                 demand per cell as a scalar PCRaster field;
    availability:           availability per cell per source, same
                            unit as the total demand and organized as a dict-
                            ionary with the source names as keys and scalar
                            PCRaster fields as values; availability can be spec-
                            ified for any or all cells within a zone;
    zones:                  zones over which the demand and availability are
                            totaled; organized as a dictionary with the source 
                            names as keys and nominal PCRaster fields as values;
    source_names:           list of names of the available sources. 
    
    Output:
    =======
    zonal_availability:     availability per zone organized as
                            a dictionary with the sources as keys and as values
                            scalar PCRaster fields of the ratio
    zonal_potential_allocation:
                            potential allocation per zone,  organized as
                            a dictionary with the sources as keys and as values
                            scalar PCRaster fields of the ratio;
    allocation_ratio:       allocation of the demand as ratio subdivided over
                            the sources on the basis of the availability,
                            organized as a dictionary with the sources as keys
                            and as values scalar PCRaster fields of the ratio.

'''        
    
    # this function computes the allocation ratio on the basis of demand and
    # availability; these ratios are approximate as the actual availability is
    # not yet known

    # get the total availability, demand fraction per zone and the
    # potential abstraction on the basis of the demand fraction
    
    # zonal availability is dependent on the availability that is not
    # yet assigned to withdrawals per source
    zonal_availability  = dict((source_name, get_zonal_total( \
                                                 local_values = availability[source_name], \
                                                 zones        = zones[source_name])) \
                                for source_name in source_names)
        
        
    # zonal demand is dependent on the demand that is not yet met
    zonal_demand_fraction = dict((source_name, get_zonal_fraction( \
                                         local_values = demand, \
                                         zones        = zones[source_name])) \
                                  for source_name in source_names)

    # compute the zonal potential allocation
    zonal_potential_allocation = dict((source_name, zonal_demand_fraction[source_name] * \
                                                     zonal_availability[source_name]) \
                                        for source_name in source_names)
                                       
    # all values calculated, next compute the remaining allocation ratio
    total_zonal_potential_allocation = sum_list(list(zonal_potential_allocation.values()))
    allocation_ratio = dict((source_name, pcr_return_val_div_zero( \
                                              zonal_potential_allocation[source_name] , \
                                              total_zonal_potential_allocation, \
                                              very_small_number)) \
                             for source_name in source_names)
        
    # return the allocation ratio
    return zonal_availability, \
           zonal_potential_allocation, allocation_ratio

def allocate_demand_to_availability( \
                                    demand, \
                                    availability, \
                                    zones, \
                                    source_names, \
                                   ):
    
    '''
    
    Input:
    ======
    demand:                 demand per cell as a scalar PCRaster field;
    availability:           availability per cell per source, same
                            unit as the total demand and organized as a dict-
                            ionary with the source names as keys and scalar
                            PCRaster fields as values; availability can be spec-
                            ified for any or all cells within a zone;
    zones:                  zones over which the demand and availability are
                            totaled; organized as a dictionary with the source 
                            names as keys and nominal PCRaster fields as values;
    source_names:           list of names of the available sources. 
    
    Output:
    =======
    
    withdrawal:             withdrawal per cell subdivided over the sour-
                            ces on the basis of the availability, organized as
                            a dictionary with the sources as keys and as values
                            scalar PCRaster fields;
    allocated_demand:       allocation of the demand subdivided over the sour-
                            ces on the basis of the availability, organized as
                            a dictionary with the sources as keys and as values
                            scalar PCRaster fields;
    met_demand:             the demand that is met and the sum of the allocat-
                            ion per source;
    unmet_demand:           the demand that cannot be met;
    message_str:            a message string that provides an overview of the
                            allocation process.
    
'''
    # set test verbose for testing
    test_verbose = False
    test_at_iter = False

    # create a deep copy of availability
    availability = deepcopy(availability)

    # set the unmet demand
    # the iteration of the supplyallocation and
    # the exit condition
    iter_allocation = 1
    met_demand      = pcr.ifthen(demand >= 0, pcr.scalar(0))
    unmet_demand    = pcr.max(0, demand - met_demand)
    exit_condition  = False

    # initialize the output
    message_str      = ''
    withdrawal       = dict((source_name, \
                             pcr.ifthen(demand >= 0, pcr.scalar(0))) \
                             for source_name in source_names)
    allocated_demand = dict((source_name, \
                             pcr.ifthen(demand >= 0, pcr.scalar(0))) \
                             for source_name in source_names)

    min_number_cells_unmet_demand = pcr.cellvalue(pcr.maptotal( \
                                                  pcr.scalar(pcr.defined(met_demand))), 1)[0]

    # iterate untill all demand is allocated or the availability is exhausted
    while not exit_condition:

        message_str = str.join('\n', \
                                (message_str, \
                                 'allocation iteration %d' % iter_allocation))

        # obtain the allocation ratio that is used to the derive the allocation
        # per source
        zonal_availability, \
        zonal_potential_allocation, \
        allocation_ratio = obtain_allocation_ratio(\
                                                   unmet_demand, \
                                                   availability, \
                                                   zones, \
                                                   source_names, \
                                                   )
            
        # get the actual allocation: here we iterate to keep the dictionary alive
        for source_name in source_names:
            # get the zonal allocation as the minimum of the allocated available
            # supply and the local demand
            zonal_potential_allocation[source_name] = pcr.min(\
                                       zonal_potential_allocation[source_name], \
                                       allocation_ratio[source_name] * unmet_demand)

            # update the values of the allocated demand
            allocated_demand[source_name] = allocated_demand[source_name] + \
                                            zonal_potential_allocation[source_name]

            # get the increment in the withdrawal
            withdrawal_increment    = pcr_return_val_div_zero(get_zonal_total( \
                                                                  local_values = zonal_potential_allocation[source_name], \
                                                                  zones        = zones[source_name]), \
                                                              zonal_availability[source_name], \
                                                              very_small_number) * \
                                      availability[source_name]
                                      #pcr.max(0, availability[source_name] - \
                                      #           withdrawal[source_name])
            
            # update the values of the withdrawal
            withdrawal[source_name] = withdrawal[source_name] + withdrawal_increment
                                      
            
            # update the availability
            availability[source_name] = \
                              pcr.max(0, 
                                      availability[source_name] - withdrawal_increment)

        # met demand and unmet demand
        met_demand   = sum_list(list(allocated_demand.values()))
        unmet_demand = pcr.max(0, demand - met_demand)

        # get final info and assess the exit condition
        mask = unmet_demand > 0
        number_cells_unmet_demand = pcr.cellvalue(pcr.maptotal(pcr.scalar(mask)), 1)[0]
        mask = mask & (pcr.max(0, sum_list(list(availability.values())) - \
                                                sum_list(list(withdrawal.values()))) > 0)
        number_cells_unmet_demand = pcr.cellvalue(pcr.maptotal(pcr.scalar(mask)), 1)[0]
        
        # update the message string
        message_str = str.join('\n', \
                               (message_str, \
                                'cells with unmet demand: %6d / %6d in total' % \
                                (number_cells_unmet_demand, \
                                 number_cells_unmet_demand)))

        # set the condition
        exit_condition  = pcr.cellvalue(pcr.mapmaximum(pcr.scalar(mask)), 1)[0] == 0
        exit_condition  = exit_condition or \
                          (number_cells_unmet_demand == min_number_cells_unmet_demand)
        iter_allocation = iter_allocation + 1
        min_number_cells_unmet_demand = min(min_number_cells_unmet_demand, \
                                            number_cells_unmet_demand)

        # test iteration
        if test_verbose and test_at_iter: print (message_str, exit_condition, \
                                                 min_number_cells_unmet_demand)

    # add the final information to the message string
    demand_stats             = pcr_get_statistics(demand)
    met_demand_stats         = pcr_get_statistics(met_demand)
    unmet_demand_stats       = pcr_get_statistics(pcr.ifthenelse(unmet_demand > 0, unmet_demand, pcr.scalar(0)))
    total_withdrawal_stats   = pcr_get_statistics(sum_list(list(withdrawal.values())))
    total_alloc_demand_stats = pcr_get_statistics(sum_list(list(allocated_demand.values())))
    
    # update the message_str
    message_str = str.join('\n', \
                          (message_str, \
                           'statistics:',\
                           '=' * len('statistics:'), \
                           '%20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('demand', demand_stats['count'], demand_stats['average'], \
                                demand_stats['min'], demand_stats['max']), \
                           '%20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('met demand', met_demand_stats['count'], met_demand_stats['average'], \
                                met_demand_stats['min'], demand_stats['max']), \
                           '%20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('unmet demand', unmet_demand_stats['count'], unmet_demand_stats['average'], \
                                unmet_demand_stats['min'], unmet_demand_stats['max']), \
                           '%20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('alloc. demand', total_alloc_demand_stats['count'], total_alloc_demand_stats['average'], \
                                total_alloc_demand_stats['min'], total_alloc_demand_stats['max']), \
                           '%20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('total withdrawal', total_withdrawal_stats['count'], total_withdrawal_stats['average'], \
                                total_withdrawal_stats['min'], total_withdrawal_stats['max']), \
                            ))
                               
    # return the output
    return withdrawal, allocated_demand, met_demand, unmet_demand, message_str    

def allocate_demand_to_availability_with_options(\
                                                 demand, \
                                                 availability, \
                                                 zones, \
                                                 source_names, \
                                                 use_local_first, \
                                                 reallocate_surplus, \
                                                 use_allocation_zone = True, \
                                                 ):
    
    '''
    
    input:
    =====
    demand                : demand per cell as a scalar PCRaster field;
    availability          : availability per cell per source, same
                            unit as the total demand and organized as a dict-
                            ionary with the source names as keys and scalar
                            PCRaster fields as values; availability can be spec-
                            ified for any or all cells within a zone;
    zones                 : zones over which the demand and availability are
                            totaled; organized as a dictionary with the source 
                            names as keys and nominal PCRaster fields as values;
    source_names          : list of names of the available sources;
    use_local_first        : boolean PCRaster map that indicates if the local
                            availability should be used first;
    reallocate_surplus    : boolean variable (True, False) indicating that any
                            surplus will be used to satisfy any local demand.
    use_allocation_zone   : boolean variable (True, False) indicating that water
                            can be pooled from an allocation zone
    
    output:
    ======
    withdrawal            : withdrawal per cell subdivided over the sour-
                            ces on the basis of the availability, organized as
                            a dictionary with the sources as keys and as values
                            scalar PCRaster fields;
    allocated_demand      : allocation of the demand subdivided over the sour-
                            ces on the basis of the availability, organized as
                            a dictionary with the sources as keys and as values
                            scalar PCRaster fields;
    met_demand            : the demand that is met and the sum of the allocat-
                            ion per source;
    unmet_demand          : the demand that cannot be met;
    message_str           : a message string that provides an overview of the
                            allocation process.

'''

    # initialize the output
    message_str      = 'allocation of demand to availability with options:'
    withdrawal       = dict((source_name, \
                             pcr.ifthen(demand >= 0, pcr.scalar(0))) \
                             for source_name in source_names)
    allocated_demand = dict((source_name, \
                             pcr.ifthen(demand >= 0, pcr.scalar(0))) \
                             for source_name in source_names)
    
    # initialize the demand
    # met demand is updated with the allocated total demand
    # unmet demand is what is still outstanding at the end of each allocation
    # round and it is initialized here as the demand and updated consecutively
    met_demand   = pcr.ifthen(demand >= 0, pcr.scalar(0))
    unmet_demand = demand
    
    # these are values that progress with the options
    remaining_availability = availability.copy()

    # test on options
    # NOTE: the options are implemented by calling function on the allocation
    # three times: first for the local use, using single cell IDs as allocation
    # zones, then with the actual settings and then by including any surplus 
    # over the relevant zones if a deficit exists.
    # NOTE: the code could be condensed by calling the function within a loop
    # but that is not so transparent and limits the incorporation of specific
    # actions. For now, this works... 

    ##############
    # local      #
    # allocation #
    ##############
    # local allocation if implemented
    use_local_first = pcr.spatial(use_local_first)
    use_local_first_flag = pcr.cellvalue(pcr.mapmaximum(pcr.scalar(use_local_first)), 1)[0] == 1
    
    if use_local_first_flag:
        message_str = str.join('\n', \
                                (message_str, '', \
                                 '* allocating local resources first:'))
        
        # set the temporary zones
        local_zones = dict((source_name, pcr.ifthen(use_local_first, \
                                         pcr.nominal(pcr.uniqueid(\
                                                     use_local_first)))) \
                           for source_name in source_names)
        
        opt_withdrawal, opt_allocated_demand, \
                        opt_met_demand, unmet_demand, sub_message_str = \
                                        allocate_demand_to_availability( \
                                                        demand             = unmet_demand, \
                                                        availability       = remaining_availability, \
                                                        zones              = local_zones, \
                                                        source_names       = source_names, \
                                                        )

        # update the values:
        # totals: met demand
        met_demand = met_demand + opt_met_demand
        
        # dictionaries per source: iterate over the source names
        for source_name in source_names:
            
            # withdrawal
            withdrawal[source_name] = withdrawal[source_name] + \
                                      opt_withdrawal[source_name]
            # allocated demand
            allocated_demand[source_name] = allocated_demand[source_name] + \
                                            opt_allocated_demand[source_name]
        
            # remaining availability
            remaining_availability[source_name] = pcr.max(0, \
                                                          remaining_availability[source_name] - \
                                                          opt_withdrawal[source_name])

        # and update the message_str
        message_str = str.join('\n', \
                               (message_str, sub_message_str))


    ##############
    # zonal      #
    # allocation #
    ##############
    # allocate water with the provided zones
    if use_allocation_zone:
        message_str = str.join('\n', \
                            (message_str, '', \
                             '* allocating the available supply over the provided zones:'))
        
        opt_withdrawal, opt_allocated_demand, \
                        opt_met_demand, unmet_demand, sub_message_str = \
                                        allocate_demand_to_availability( \
                                                        demand             = unmet_demand, \
                                                        availability       = remaining_availability, \
                                                        zones              = zones, \
                                                        source_names       = source_names, \
                                                        )
        
        # update the values:
        # totals: met demand
        met_demand = met_demand + opt_met_demand
        
        # dictionaries per source: iterate over the source names
        for source_name in source_names:
            
            # withdrawal
            withdrawal[source_name] = withdrawal[source_name] + \
                                      opt_withdrawal[source_name]
            # allocated demand
            allocated_demand[source_name] = allocated_demand[source_name] + \
                                            opt_allocated_demand[source_name]
        
            # remaining availability
            remaining_availability[source_name] = pcr.max(0, \
                                                          remaining_availability[source_name] - \
                                                          opt_withdrawal[source_name])
        
        # and update the message_str
        message_str = str.join('\n', \
                               (message_str, sub_message_str))
        
    #################
    # surplus       #
    # re-allocation #
    #################
    # reallocate any surplus, if selected
    if reallocate_surplus:
        message_str = str.join('\n', \
                                (message_str, '',\
                                '* allocating any surplus from available supplyresources to satisfy outstanding demand:'))
        
        # free up supply iteratively as follows:
        # 0: initialize the deficit as the unmet demand;
        #    this will be reduced consecutively with the supply that is freed
        # iterate over the sources:
        # 1: determine the zonal deficit for the current allocation zone
        # 2: get the surplus and the zonal surplus dependent on the supply
        #    that is needed to satisfy the deficit
        # 3: before limiting the surplus, determine the ratio so the relative
        #    contribution from the other sources can be assessed
        # 4: assess the ratio of the deficit over the surplus that needs to be
        #    freed
        # 5: iterate over the other resources and allocate and remove water
        #    from the available other resources and assign it to the al-
        #    located supply and in turn, free it from the allocated supply for
        #    the present source
        
        
        # initialize the deficit
        deficit = unmet_demand
        
        for source_name in source_names:
            
            # get the other sources
            other_source_names = source_names[:]
            other_source_names.remove(source_name)
            
            s_str = str.join('', other_source_names)
            s_str = str.join('', \
                   ('- processing %s with any surplus for ' %  source_name,\
                   s_str))
            message_str = str.join('\n', \
                                   (message_str, \
                                    s_str))
            
            # get the zonal deficit
            zonal_deficit = get_zonal_total(local_values = deficit, \
                                            zones        = zones[source_name ])
            
            # get the surplus per cell as the sum of all available supplyfor
            # the other sources
            surplus = pcr.scalar(0)
            for other_source_name in other_source_names:
                surplus = surplus + remaining_availability[other_source_name]

            surplus_cont_ratio = dict((other_source_name, \
                                       pcr_return_val_div_zero( \
                                                  remaining_availability[other_source_name], \
                                                  surplus, very_small_number)) \
                                       for other_source_name in other_source_names)
            
            # get the surplus as the amount that can be actually freed before
            # getting the zonal surplus
            surplus       = pcr.min(allocated_demand[source_name], surplus)
            zonal_surplus = get_zonal_total(local_values = surplus, \
                                            zones        = zones[source_name ])
            
            # free up supply: if there is no surplus, no supply can be freed
            allocation_ratio = pcr.min(1.0, \
                                       pcr_return_val_div_zero(zonal_deficit, \
                                                               zonal_surplus, \
                                                               very_small_number))
            # get the supply that can be freed
            # total supply freed is the total per zone
            total_supply_freed = pcr.scalar(0)
            # iterate over the other sources to free up supply
            for other_source_name in other_source_names:
                
                # get the supply freed
                supply_freed = surplus_cont_ratio[other_source_name] * \
                              allocation_ratio * \
                              pcr.min(allocated_demand[source_name], \
                                      remaining_availability[other_source_name])
                
                # add the freed supply to the remaining available supply for the
                # current source, and reduce it from the other;
                # take it from the allocated demand from the source and add
                # it to the other
                remaining_availability[source_name]       = remaining_availability[source_name] + \
                                                            supply_freed
                allocated_demand[source_name]             = pcr.max(0, \
                                                                    allocated_demand[source_name] - \
                                                                    supply_freed)                   
                remaining_availability[other_source_name] = pcr.max(0, \
                                                                    remaining_availability[other_source_name] - \
                                                                    supply_freed)
                allocated_demand[other_source_name]       = allocated_demand[other_source_name] + \
                                                            supply_freed
                
                # update the total supply freed
                total_supply_freed = total_supply_freed + get_zonal_total( \
                                                        local_values = supply_freed, 
                                                        zones        = zones[source_name])
            
            # use the total supply freed to satisfy any outstanding demand
            deficit = pcr.max(0, deficit - total_supply_freed *\
                                 pcr_return_val_div_zero(deficit, \
                                                         zonal_deficit, \
                                                         very_small_number))
        
        # now use the freed supply to repeat the reallocation
        opt_withdrawal, opt_allocated_demand, \
                        opt_met_demand, unmet_demand, sub_message_str = \
                                        allocate_demand_to_availability( \
                                                        demand             = unmet_demand, \
                                                        availability       = remaining_availability, \
                                                        zones              = zones, \
                                                        source_names       = source_names, \
                                                        )
        # update the values:
        # totals: met demand
        met_demand = met_demand + opt_met_demand
        
        # dictionaries per source: iterate over the source names
        for source_name in source_names:
            
            # withdrawal
            withdrawal[source_name] = withdrawal[source_name] + \
                                      opt_withdrawal[source_name]
            # allocated demand
            allocated_demand[source_name] = allocated_demand[source_name] + \
                                            opt_allocated_demand[source_name]
            
            # remaining availability
            remaining_availability[source_name] = pcr.max(0, \
                                                          remaining_availability[source_name] - \
                                                          opt_withdrawal[source_name])
        
        # and update the message_str
        message_str = str.join('\n', \
                               (message_str, sub_message_str))        
    
    ##########
    # report #
    ##########
    # final allocation known, add the overall statistics
    message_str = str.join('\n', \
                        (message_str, '', \
                         '* overall allocation of the available supply resources over the provided zones:'))
    
    # add the final information to the message string
    demand_stats             = pcr_get_statistics(demand)
    met_demand_stats         = pcr_get_statistics(met_demand)
    unmet_demand_stats       = pcr_get_statistics(pcr.ifthenelse(unmet_demand > 0, unmet_demand, pcr.scalar(0)))
    total_withdrawal_stats   = pcr_get_statistics(sum_list(list(withdrawal.values())))
    total_alloc_demand_stats = pcr_get_statistics(sum_list(list(allocated_demand.values())))
    
    # update the message_str
    message_str = str.join('\n', \
                          (message_str, '',\
                           '=' * len('statistics:'), \
                           'statistics:',\
                           '=' * len('statistics:'), \
                           '%-20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('demand', demand_stats['count'], demand_stats['average'], \
                                demand_stats['min'], demand_stats['max']), \
                           '%-20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('met demand', met_demand_stats['count'], met_demand_stats['average'], \
                                met_demand_stats['min'], met_demand_stats['max']), \
                           '%-20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('unmet demand', unmet_demand_stats['count'], unmet_demand_stats['average'], \
                                unmet_demand_stats['min'], unmet_demand_stats['max']), \
                           '%-20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('alloc. demand', total_alloc_demand_stats['count'], total_alloc_demand_stats['average'], \
                                total_alloc_demand_stats['min'], total_alloc_demand_stats['max']), \
                           '%-20s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                               ('total withdrawal', total_withdrawal_stats['count'], total_withdrawal_stats['average'], \
                                total_withdrawal_stats['min'], total_withdrawal_stats['max']), \
                            ))
    
    # all options processed, return the output
    return withdrawal, allocated_demand, met_demand, unmet_demand, message_str

def allocate_demand_to_withdrawals(withdrawal_names, \
                                   source_names, \
                                   sector_names, \
                                   demand_per_sector, \
                                   renewable_withdrawal_per_sector, \
                                   nonrenewable_withdrawal_per_sector, \
                                   zones_per_sector, \
                                   use_local_first, \
                                   ):
    
    '''
    allocate_demand_to_withdrawals: 
                            function that allocates the supply to \
                            the demand per sector.
    
    input:
    =====
    withdrawal_names      : list with withdrawal names to be processed
                            (i.e., renewable and non-renewable)
    source_names          : list with source names to be processed
                            (i.e., surfacewater and groundwater)
    sector_names          : list with sector names to be processed
    demand_per_sector     : dictionary with the sector names as keys and as 
                            values the corresponding sectoral demand as scalar
    renewable_withdrawal_per_sector :
                            dictionary with source names (string) as keys with 
                            another dictionary with sector names (string) as keys 
                            and PCRaster maps with actual water withdrawal from
                            renewable sources
    nonrenewable_withdrawal_per_sector :
                            dictionary with source names (string) as keys with 
                            another dictionary with sector names (string) as keys 
                            and PCRaster maps with actual water withdrawal from
                            non-renewable sources
    zones_per_sector      : dictionary with source names (string) as keys with 
                            another dictionary with sector names (string) as keys 
                            and PCRaster maps with zones over which the demand and
                            availability are totaled
    use_local_first        : boolean PCRaster map that indicates if the local
                            availability should be used first
    
    output:
    ======
    allocated_supply_per_sector:
                            supply, allocated to the different sectors, organ-
                            ized as a dictionary with the combined key of sup-
                            ply - source name as a composite key and a nested
                            dictionary as value with the sector name as key and
                            a scalar PCRaster field of the allocated supply per
                            cell as value;
    remaining_supply_per_source: 
                            a dictionary organized similarly as the input
                            supply_per_source but now with any supply that is
                            not allocated to meet the demand;
    allocated_demand_per_sector:
                            demand, allocated to the different sectors, organ-
                            ized as a dictionary with the combined key of sup-
                            ply - source name as a composite key and a nested
                            dictionary as value with the sector name as key and
                            a scalar PCRaster field of the allocated demand per
                            cell as value; the supply is what is locally
                            withdrawn, the demand is what is locally allocated
                            to meet the demand and over the appropriate alloc-
                            ation zone should balance;
    met_demand_per_sector:  dictionary organzized as the input demand_per_sector
                            with the sector names as keys and as values the 
                            demand per sector that is actually met;
    message_str:            a message string that provides an overview of the
                            allocation process, including the number of iter-
                            ations and the allocated supply/demand.
    
    The package requires all input to be compatible with spatial, scalar PCRaster
    fields and the values of supply and demand to have the same value, being volume
    over time per cell.
    '''
    
    # initialize the output
    message_str = 'allocation of demand to supply with water quality:'
    
    # initialize the variables
    # allocated withdrawal  and demand per sector, grouped per withdrawal and source
    # total of the met demand per sector
    allocated_withdrawal_per_sector = {}
    allocated_demand_per_sector = {}
    
    for withdrawal_name in withdrawal_names:
        for source_name in source_names:
            key = get_key([withdrawal_name, source_name])
            allocated_withdrawal_per_sector[key] = \
                        dict((sector_name, \
                              pcr.ifthen(demand_per_sector[sector_name] >= 0, \
                                         pcr.scalar(0))) \
                             for sector_name in sector_names)
            
            allocated_demand_per_sector[key] = \
                        dict((sector_name,
                              pcr.ifthen(demand_per_sector[sector_name] >= 0, \
                                         pcr.scalar(0))) \
                             for sector_name in sector_names)
    
    met_demand_per_sector = dict((sector_name, \
                                  pcr.ifthen(demand_per_sector[sector_name] >= 0, \
                                             pcr.scalar(0))) \
                                 for sector_name in sector_names)
    
    # total remaining withdrawal and demand per source
    remaining_withdrawal_per_source_sector = {'renewable'   : deepcopy(renewable_withdrawal_per_sector), \
                                              'nonrenewable': deepcopy(nonrenewable_withdrawal_per_sector)}
    
    remaining_demand_per_sector = deepcopy(demand_per_sector)
    
    # allocate water withdrawn to pixels
    # 1st: local use, using single cell IDs as allocation zones
    # 2nd: actual allocation zones
    
    # initializing local allocation parameters
    use_local_first = pcr.spatial(use_local_first)
    use_local_first_flag = pcr.cellvalue(pcr.mapmaximum(pcr.scalar(use_local_first)), 1)[0] == 1
    local_zones = dict((source_name, \
                        dict((sector_name, \
                              pcr.ifthen(use_local_first, \
                                         pcr.nominal(pcr.uniqueid(use_local_first)))) \
                             for sector_name in sector_names)) \
                       for source_name in source_names)
    
    # evaluate for local and zonal resources
    for option_str, (option_flag, option_mask, option_zones) in { \
                   'allocating local resources': (use_local_first_flag, \
                                                  use_local_first, \
                                                  local_zones), \
                   'allocating zonal resources': (True, \
                                                  pcr.spatial(pcr.boolean(1)), \
                                                  zones_per_sector)}.items():
        
        # process if the option is True
        if option_flag:
            # add the option to the message string
            message_str = str.join('\n', \
                                  (message_str, '', \
                                   '* %s:' % option_str))
            
            # evaluate per withdrawal and source
            for withdrawal_name in withdrawal_names:
                for source_name in source_names:
                    
                    # add the option to the message string
                    message_str = str.join('\n', \
                                          (message_str, \
                                           '- allocating demand to %s %s withdrawal' % \
                                           (withdrawal_name, source_name)))
                    
                    # initialize variable
                    actual_allocated_withdrawal = pcr.scalar(0)
                    
                    # set the key
                    key = get_key([withdrawal_name, source_name])
                    
                    # allocate the withdrawals to the demand per sector
                    for sector_name in sector_names:
                        
                        # set the total zonal withdrawal per sector
                        total_zonal_withdrawal = \
                            get_zonal_total( \
                                            local_values = remaining_withdrawal_per_source_sector\
                                                           [withdrawal_name][source_name][sector_name], \
                                            zones        = option_zones[source_name][sector_name])
                        
                        # get the allocated withdrawals per cell based on
                        # the fractional total demand per sector and the total zonal withdrawals;
                        # this may exceed the demand if the withdrawal is plenty
                        allocated_withdrawal = \
                            total_zonal_withdrawal * \
                            get_zonal_fraction( \
                                               local_values = pcr.max(0, \
                                                                      demand_per_sector[sector_name] - met_demand_per_sector[sector_name]), \
                                               zones        = option_zones[source_name][sector_name])
                        
                        # allocate the withdrawals to the demand; this returns
                        # the amount of withdrawals that are applied locally
                        # for the current sector from the current supply
                        # and source; this is a local value in the loop, 
                        # which is subsequently added to the allocated demand
                        # per sector
                        allocated_withdrawal_demand = \
                            pcr.min(allocated_withdrawal, \
                                    pcr.max(0, \
                                            demand_per_sector[sector_name] - met_demand_per_sector[sector_name]))
                        
                        # update the totals: allocated supply per sector
                        # the supply that is required is dependent on the supply
                        # allocated to the demand on the ratio of the zonal totals
                        # of the allocated_withdrawal_demand and the total zonal
                        # supply;
                        # updated here too are the allocated supply per section and
                        # the actual_allocated_withdrawal
                        required_allocated_withdrawal = \
                            remaining_withdrawal_per_source_sector[withdrawal_name][source_name][sector_name] * \
                            pcr.min(1.0, \
                                    pcr_return_val_div_zero( \
                                                            get_zonal_total( \
                                                                            local_values = allocated_withdrawal_demand, \
                                                                            zones        = option_zones[source_name][sector_name]), \
                                                            total_zonal_withdrawal, \
                                                            very_small_number))
                        
                        # update the totals
                        # - allocated demand per sector
                        # - met demand per sector
                        # - actual allocated withdrawal
                        allocated_demand_per_sector[key][sector_name] += \
                               allocated_withdrawal_demand
                        
                        met_demand_per_sector[sector_name] += \
                               allocated_withdrawal_demand
                        
                        allocated_withdrawal_per_sector[key][sector_name] += \
                               required_allocated_withdrawal
                        
                        actual_allocated_withdrawal += \
                               required_allocated_withdrawal
                        
                        # update remaining withdrawal
                        remaining_withdrawal_per_source_sector[withdrawal_name][source_name][sector_name] = \
                            pcr.max(0.0, \
                                    remaining_withdrawal_per_source_sector[withdrawal_name][source_name][sector_name] - required_allocated_withdrawal)
    
    # aggregating results
    remaining_withdrawal_per_source = {}
    for withdrawal_name in withdrawal_names:
        remaining_withdrawal_per_source[withdrawal_name] = {}
        for source_name in source_names:
            remaining_withdrawal_per_source[withdrawal_name][source_name] = \
                sum_list(list(remaining_withdrawal_per_source_sector[withdrawal_name][source_name].values()))
    
    # .........................................................................................
    # add the statistics on the withdrawal, remaining withdrawal, demand and met demand
    # final allocation known, add the overall statistics
    message_str = str.join('\n', \
                           (message_str, '', \
                            '* overall allocation of the supply to meet demand over the provided zones:'))
    
    # add the final information to the message string
    # demand and allocation
    for sector_name in sector_names:
        
        # get the total and the unmet demand
        demand_stats     = pcr_get_statistics(demand_per_sector[sector_name])
        met_demand_stats = pcr_get_statistics(met_demand_per_sector[sector_name])
        
        # update the message_str
        message_str = str.join('\n', \
                               (message_str, '', \
                                '=' * len('statistics - %s demand:' % sector_name), \
                                'statistics - %s demand:' % sector_name,\
                                '=' * len('statistics - %s demand:' % sector_name), \
                                     '-%60s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                                         ('demand', demand_stats['count'], demand_stats['average'], \
                                         demand_stats['min'], demand_stats['max']), \
                                     '-%60s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                                         ('met demand', met_demand_stats['count'], met_demand_stats['average'], \
                                         met_demand_stats['min'], met_demand_stats['max'])))
        
        # get the allocated supply and demand per sector
        for withdrawal_name in withdrawal_names:
            for source_name in source_names:
                key = get_key([withdrawal_name, source_name])
                key_str = get_key([sector_name, 'from', key])
                
                # statistics on withdrawal and demand
                withdrawal_stats = pcr_get_statistics(allocated_withdrawal_per_sector[key][sector_name])
                demand_stats = pcr_get_statistics(allocated_demand_per_sector[key][sector_name])
                
                # update the message_str
                message_str = str.join('\n', \
                                       (message_str, \
                                        '%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                                            ('%s - %s' % ('supply', key_str), withdrawal_stats['count'], withdrawal_stats['average'], \
                                            withdrawal_stats['min'], withdrawal_stats['max']), \
                                        '%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                                            ('%s - %s' % ('demand', key_str), demand_stats['count'], demand_stats['average'], \
                                            demand_stats['min'], demand_stats['max'])))
    
    # overall supply
    message_str = str.join('\n', \
                           (message_str, '', \
                            '=' * len('statistics - supply'), \
                                    'statistics - supply', \
                                    '=' * len('statistics - supply')))
    
    for withdrawal_name in withdrawal_names:
        for source_name in source_names:
            for sector_name in sector_names:
                # statistics on supply
                withdrawal_per_source = {'renewable'   : renewable_withdrawal_per_sector, \
                                         'nonrenewable': nonrenewable_withdrawal_per_sector}
                total_withdrawal_stats     = pcr_get_statistics(withdrawal_per_source[withdrawal_name][source_name][sector_name])
                remaining_withdrawal_stats = pcr_get_statistics(remaining_withdrawal_per_source_sector[withdrawal_name][source_name][sector_name])
                
                # update the message_str
                message_str = str.join('\n', \
                            (message_str, '', \
                              '%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                                  ('total supply %s - %s - %s' % (withdrawal_name, source_name, sector_name),  \
                                  total_withdrawal_stats['count'], total_withdrawal_stats['average'], \
                                  total_withdrawal_stats['min'], total_withdrawal_stats['max']), \
                              '%-60s - count: %6d - avg.: %10g - min: %10g - max: %10g' % \
                                  ('remaining supply %s - %s - %s' % (withdrawal_name, source_name, sector_name), \
                                  remaining_withdrawal_stats['count'], remaining_withdrawal_stats['average'], \
                                  remaining_withdrawal_stats['min'], remaining_withdrawal_stats['max'])))
    
    # add a blank line at last
    message_str = str.join('\n', \
                           (message_str, ''))
    
    # return the allocated demand, the 
    return allocated_withdrawal_per_sector, remaining_withdrawal_per_source, \
           allocated_demand_per_sector, met_demand_per_sector, message_str
