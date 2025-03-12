#!/usr/bin/env python
#  -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# CALEROS Landscape Development Model:                                        #
#                                                                             #
# Copyright (c) 2019 Ludovicus P.H. (Rens) van Beek - r.vanbeek@uu.nl         #
# Department of Physical Geography, Faculty of Geosciences,                   #
# Utrecht University, Utrecht, The Netherlands.                               #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
# basic_functions: module with additional functions to support dynamic model- #
# ling. This development is part of the CALEROS landscape development         #
#                                                                             #
###############################################################################
"""

"""

###########
# Modules #
###########

import os
import sys

import numpy as np
import pcraster as pcr

########
# TODO #
########
critical_improvements= str.join('\n\t',\
             ( \
              '', \
              ))

development= str.join('\n\t',\
             ( \
              '', \
              'include generic function to split string to lists', \
              '', \
              ))

print ('\nDevelopmens for basic functions:')

if len(critical_improvements) > 0:
    print('Critical improvements: \n%s' % \
          critical_improvements)

if len(development) > 0:
    print ('Ongoing: \n%s' % development)

if len(critical_improvements) > 0:
    sys.exit()

#####################
# Global variables #
####################

very_small_number =  1.0e-12
convergence_limit = 1.0e-12
max_number_iterations = 100

#############
# Functions #
#############

# The following are generic functions to process lists

def expand_list(list_in, length, entry= None):
    '''
expand_list: generic function to expand the list specified until it contains the required \
number of entries.

    Input:
    ======
    list_in:            input list with entries of any type;
    length:             the desired length of the list;
    entry:              preferred entry to be added to the list. This may be a
                        single entry of the type contained by the input list
                        or a list of those. Optional, default value is None,
                        in which case the input list is used.

    Output:
    =======
    list_out:           list of the desired length
'''
    #-expands a list until it contains the required number of elements
    # initialize the output list
    list_out = []
    # test entry
    if not entry is None:
        if not type(entry) is list:
            entry = [entry]
    else:
        entry = list(list_in)
    
    # iterate until the length of the output list is met
    while len(list_out) < length:
        for e in entry:
            list_out.append(e)

    # finally, return list
    return list_out[:length]

def sum_list(list_in):
    '''
sum_list: generic function that returns the sum of a list of which \
the entries can be summed (integers, floats, arrays etc.).

'''
    #-sums all entries in a list-like type
    return sum(list_in)

def product_list(list_in):

    '''
product_list: generic function that returns the product of a list of which \
the entries can be multiplied (integers, floats, arrays etc.).

'''
    # initialize the output
    y = list_in[0]
    
    for ix in range(1, len(list_in)):
        y = y * list_in[ix]

    # return the output
    return y

def max_dicts(dict_in):

    '''
max_dicts: generic function that returns the maximum pcr map from a collection \
of arrays contained in a dictionary.

'''
    # initialize exit condition
    map_maximum = None
    
    # get maximum comparing maps in pairs
    for key, values in dict_in.items():
        if isinstance(map_maximum, type(None)):
            map_maximum = values
        
        else:
            map_maximum = pcr.max(values, map_maximum)

    # return the output
    return map_maximum

def add_dicts(a_dict, b_dict, halt_on_key_error = False):
    '''
add_dicts: generic function that returns a dictionary that uses the inter\
section of the keys of dictionaries a and b and the sum of their entries as \
values. This assumes that the  entries can be added directly (integers, \
floats, arrays etc.) and missing values are not explicitly handled by the \
function.

The function can produce a warning or halt if keys of the dictionaries a and b \
do not match if halt_on_key_error is set respecively False or True \
(default: False).

'''

    # create an empty dictionary
    c_dict = {}
    
    # check on keys
    if len(a_dict) != len(b_dict):
        message_str = 'length of keys of dictionaries (%d, %d) do not match' % \
            (len(a_dict), len(b_dict))
        if halt_on_key_error:
            sys.exit('error: %s' % message_str)
        else:
            print ('warning: %s' % message_str)

    # extract common keys
    common_keys = []
    if len(a_dict) >= len(b_dict):
        keys = list(a_dict.keys())
    else:
        keys = list(b_dict.keys())
    for key in keys:
        if key in a_dict.keys() and key in b_dict.keys():
            common_keys.append(key)
    
    # sort the common keys
    common_keys.sort()
    
    # get the values
    for key in common_keys:
        c_dict[key] = a_dict[key] + b_dict[key]

    # and return the resulting dictionary
    return c_dict 


def multiply_dicts(a_dict, b_dict, halt_on_key_error = False):
    '''
multiply_dicts: generic function that returns a dictionary that uses the inter\
section of the keys of dictionaries a and b and the product of their entries as \
values. This assumes that the  entries can be multiplied directly (integers, \
floats, arrays etc.) and missing values are not explicitly handled by the \
function.

The function can produce a warning or halt if keys of the dictionaries a and b \
do not match if halt_on_key_error is set respecively False or True \
(default: False).

'''

    # create an empty dictionary
    c_dict = {}
    
    # check on keys
    if len(a_dict) != len(b_dict):
        message_str = 'length of keys of dictionaries (%d, %d) do not match' % \
            (len(a_dict), len(b_dict))
        if halt_on_key_error:
            sys.exit('error: %s' % message_str)
        else:
            print ('warning: %s' % message_str)

    # extract common keys
    common_keys = []
    if len(a_dict) >= len(b_dict):
        keys = list(a_dict.keys())
    else:
        keys = list(b_dict.keys())
    for key in keys:
        if key in a_dict.keys() and key in b_dict.keys():
            common_keys.append(key)
    
    # sort the common keys
    common_keys.sort()
    
    # get the values
    for key in common_keys:
        c_dict[key] = a_dict[key] * b_dict[key]
    
    # and return the resulting dictionary
    return c_dict 

def get_decision(question_str, possible_outcomes):
    
    '''
get_decision: function that gets user input interactively.

    Input:
    ======
    question_str:       string specifying the options to the user.
                        possible answers are taken from the possible outcomes;
    possible_outcomes:  possible outcomes organized as a dictionary with
                        the answers as keys and the related outcome.
                        
    Output:
    =======
    outcome:            the resulting outcome.

    '''
    
    # add options to the question_str
    options = list(possible_outcomes.keys())
    option_str = '('
    for option in options:
        option_str = str.join('', \
                     (option_str, option, ', '))
    option_str = option_str.rstrip(', ')
    option_str = str.join('', \
                         (option_str, ')\n> '))
    question_str = str.join(' ', \
                            (question_str.rstrip(), option_str))

    # initialize the outcome and selected option
    outcome = None
    selected_option = ''
    while selected_option not in options:
        selected_option = input(question_str)

    # get the answer
    outcome = possible_outcomes[selected_option]

    # return the decision
    return outcome

#def create_list_constructor(s, separators):
#    
#    '''
#    
#create_list_constructor: function that returns the list constructor from a \
#string and list of separators, which is a dictionary object holding a unique \
#identifier as keyword, and two items identified by the keywords "entry", \
#holding the actual list entry, and "levelinfo" that holds information on the \
#levels and indices as a separate dictionary in which levels are used as keys \
#and indices as values, e.g.,  {'a': {0: 0, 1: 0}, 'b': {0: 0, 1: 1}}, from a \
#string organized in different levels by the separators that are listed in \
#descending order.
#  
#    '''
#
#    #-list_constructor is intialized as an empty dictionary with a known identifier
#    separators = separators[:]
#    identifier = 0
#    list_constructor = {}
#    list_constructor[identifier] = {}
#    list_constructor[identifier]['entry'] = s
#    list_constructor[identifier]['levelinfo'] = {}
#    level = 0
#    #-step through separators and keys in the list constructor
#    while len(separators) > 0:
#        #-get separator and list of current identifiers, including the maximum value
#        # to be used for adding new dictionary entries
#        separator = separators.pop()
#        ids = list_constructor.keys()
#        maxid = max(ids)
#        #-step through dictionary entries
#        for identifier in ids:
#            #-if the entry of the current dictionary entry contains the separator
#            # get entry and levelinfo, delete the present entry and process for all
#            # subsequent entries of increasing order at the given level
#            if separator in list_constructor[identifier]['entry']:
#                entry = list_constructor[identifier]['entry']
#                levelinfo = list_constructor[identifier]['levelinfo']
#                del list_constructor[identifier]
#                order = 0
#                #-for each element of the split entry, update the identifier and add
#                # the info to the new entry of the dictionary
#                for newentry in entry.split(separator):
#                    maxid = maxid + 1
#                    list_constructor[maxid] = {}
#                    list_constructor[maxid]['entry'] = newentry
#                    list_constructor[maxid]['levelinfo'] = levelinfo.copy()
#                    list_constructor[maxid]['levelinfo'][level] = order
#                    order = order + 1
#        #-increment level counter
#        level = level + 1
#    #-return list_constructor object
#    return list_constructor

#def construct_list_from_dictionary(list_constructor,result_list):
#    
#    '''
#
#construct_list_from_dictionary: function that can construct a list of \
#arbitrary form from a dictionary object holding a unique identifier \
#as keyword, and two items identified by the keywords "entry", holding the \
#actual list entry, and "levelinfo" that holds information on the levels and \
#indices as a separate dictionary in which levels are used as keys and indices \
#as values, e.g., {0: {'entry': 'a', 'levelInfo': {0: 0, 1: 0}}, \
#1: {'entry': 'b', 'levelInfo': {0: 0, 1: 1}}} which is equivalent with a \
#zero-order list that contains at position 0 the first-order list with the \
#elements a and b: [[a,b]].
#
#    '''
#    result_list= result_list[:]
#    assert isinstance(list_constructor,dict)
#    #-iterate over all list entries in the list_constructor object
#    for key, listinfo in list_constructor.iteritems():
#        entry= listinfo['entry']
#        levelinfo= listinfo['levelinfo']
#        #-get levels from levelinfo and sort them in ascending order
#        levels= levelinfo.keys()
#        levels.sort()
#        #-create dictionary of list contents and populate
#        list_contents= dict([(level,[]) for level in levels])
#        for level in levels:
#            index= levelinfo[level]
#            #-populate list_contents at lowest level with the sublist at index i
#            # otherwise
#            if level == 0:
#                #-get the contents of result_list at index, else insert the necessary elements as empty lists
#                if index >= len(result_list):
#                  result_list= expandlist(result_list,index,[])
#                list_contents[level]= result_list[:]
#            else:
#                list_contents[level]= list_contents[level-1][levelinfo[level-1]][:]
#                if index >= len(list_contents[level]):
#                  list_contents[level]= expandlist(list_contents[level],index,[])
#            #-at the highest level, insert entry
#            if level == max(levels):
#                list_contents[level][index]= entry
#        #-process the levels in reverse order and insert result from higher level into the underlying level
#        #-remove highest level first
#        level= levels.pop()
#        index= levelinfo[level]
#        while len(levels) > 0:
#            level= levels.pop()
#            index= levelinfo[level]
#            list_contents[level][index]= list_contents[level+1]
#        result_list[index]= list_contents[level][index]
#    #-return the updated list
#    return result_list


def convert_string_to_list(s, separators =  [',',';']):

    '''

convert_string_to_list: function that converts a string with separators into \
a (nested) list.

'''
    
    if not isinstance(s, str):
        
        sys.exit('function requires a string to split it in smaller parts')

    result_list = [s]
    sep_level = 0
    
    while len(separators) > 0:
        
        separator = separators.pop()
        
        # get each entry and split it in 
        # sub-levels
        for ix in range(len(result_list)):
            ss = result_list[ix]
            result_list[ix] = ss.split(sep = separator)
        
        # avoid nesting first list
        if sep_level == 0:
            result_list = result_list[0][:]
        
        # update sep_level
        sep_level = sep_level + 1
        
    # return the resulting list
    return result_list

#==============================================================================
# The following are additional PCRaster functions
#==============================================================================

def pcr_get_statistics (pcrfield, \
                        np_stat_funcs = [np.average, np.min, np.max], \
                        mv = -999.9):
    '''
pcr_get_statistics: returns the statistics of all values in a PCRaster field \
as specified by numpy functions in the np_stat_funcs list with the missing values \
masked out.

Returns a dictionary with the name of the numpy functions as keys and the count
    
'''
    a = pcr.pcr2numpy(pcr.scalar(pcrfield), mv).astype(np.float32)
    a = a[a != mv]
    
    if a.size > 0:
        stat_val = dict((str(f.__name__), f(a)) for f in np_stat_funcs)
    else:
        stat_val = dict((str(f.__name__), mv) for f in np_stat_funcs)
    stat_val['count'] = a.size

    return stat_val    
    
#== end of pcr_get_statistics =================================================

def pcr_sort_list(pcrfield_list, \
        remove_duplicates = False, \
        remove_empty_fields = True, \
        test_verbose = False, \
        ):
    '''
pcr_sort_list: function that sorts a list of PCRaster fields on a cell-by-cell 
basis in ascending order, where duplicates can be either kept or removed.

    Input:
    ======
    pcrfield_list:          list of scalar PCRaster fields;
    remove_duplicates:      boolean, default set to False, that indicates
                            whether duplicates should be removed or not;
    remove_empty_fields:    boolean, default set to True, that indicates
                            whether entries of fields that contain missing
                            values only should be removed or not;
    test_verbose:           optional, when set, information on the sorting
                            is written to screen.

    Output:
    =======
    pcr_sorted_field_list:  the resulting list with the sorted elements of the
                            input fields in place in which duplicates are
                            removed or not.

'''

    # Check and set data type of input fields.
    pcr_data_type = str(pcrfield_list[0].dataType()).lower()
    recast_type = pcr_data_type != 'scalar'

    # Create a copy of the list with original values, this is emptied
    # by the subsequent process and in its creation it considers the presence
    # and removal of duplicates if required.
    if remove_duplicates:

        # Create a new list to which fields with original values only will be
        # added.
        pcrfield_list_c = []

        # Duplicates are removed, iterate and compare.
        for new_field in pcrfield_list:

            # set the mask with duplicates to False
            duplicate_mask = pcr.boolean(0)

            # Compare this with any fields that were already added to the
            # copied list.
            for old_field in pcrfield_list_c:
                duplicate_mask = pcr.ifthenelse(pcr.defined(old_field) & 
                        pcr.defined(new_field), 
                        duplicate_mask | (old_field == new_field), 
                        duplicate_mask)

            # With the data all processed, remove the duplicates from new_field
            # and add this to the list.
            pcrfield_list_c.append(pcr.ifthen(pcr.pcrnot(duplicate_mask), 
                    new_field))

    else:
        # Duplicates do not have to be removed, just copy the list.
        pcrfield_list_c = pcrfield_list[:]

    if test_verbose:
        for ix in range(len(pcrfield_list_c)):
            print (ix, pcr.cellvalue(pcrfield_list_c[ix], 1) [0])

    # create the list of output
    pcrfield_sorted_list = []

    # The copy of the list of original values does not contain any duplicates
    # any more if so required but is not yet sorted. So, new fields are inserted
    # repeatedly at the beginning of the sorted list that is being composed and
    # moved iteratively. In this case, missing values are seen as a very high
    # value and always need propagation towards the end.
    # Set a counter to check progress and control the flow.
    icnt = 0
    while len(pcrfield_list_c) > 0:

        # Pop the last field from the list with copied fields and recast it
        # as a scalar map.
        new_field = pcr.spatial(pcr.scalar(pcrfield_list_c.pop()))

        # Iterate over the existing fields.
        for ix in range(len(pcrfield_sorted_list)):

            # Set the old_field on the basis of the counter in the existing list;
            # then use this later to update the actual entry
            old_field = pcrfield_sorted_list[ix]
            
            # Create a mask where the old field has to be updated with the
            # new value and an intermediate field holding the values to
            # be assigned to the current old field
            update_mask = pcr.ifthenelse(pcr.defined(old_field), \
                pcr.ifthenelse(pcr.defined(new_field), \
                        old_field > new_field, \
                        pcr.boolean(0)), \
                pcr.defined(new_field))

            if test_verbose:
                print (\
                        '\n', \
                        icnt, ix, \
                        pcr.cellvalue(new_field, 1)[0], \
                        pcr.cellvalue(old_field, 1)[0], \
                        pcr.cellvalue(update_mask, 1)[0], \
                        )
            
            x = pcr.ifthenelse(update_mask, new_field, old_field)
            new_field = pcr.ifthenelse(update_mask, old_field, new_field)
            old_field = x
            pcrfield_sorted_list[ix] = old_field

            if test_verbose:
                print ( \
                        icnt, ix, \
                        pcr.cellvalue(new_field, 1)[0], \
                        pcr.cellvalue(old_field, 1)[0], \
                        pcr.cellvalue(pcrfield_sorted_list[ix], 1)[0], \
                        '\n', \
                        )

            # And remove x and the mask
            x = None; update_mask = None; old_field = None
            del x, update_mask, old_field


        # Finally, add the new field with the highest value encountered to the list
        pcrfield_sorted_list.append( \
            pcr.ifthen(pcr.defined(new_field), new_field))

#        if icnt == 3: sys.exit()

        # Update counter
        icnt = icnt + 1


    # Once in place, remove any fields that contain only missing values;
    # this is only invoked if remove_empty_fields is True.
    while remove_empty_fields:
        remove_empty_fields = np.all( 
                pcr.pcr2numpy(pcr.defined(pcrfield_sorted_list[-1]), 0) == 0)
        if remove_empty_fields:
            pcrfield_sorted_list.pop()

    # And recast the type if necessary.
    if recast_type:
        func = getattr(pcr, pcr_data_type)
        for ix in range(len(pcrfield_sorted_list)):
            pcrfield_sorted_list[ix] = func(pcrfield_sorted_list[ix])

    # return the sorted list
    return pcrfield_sorted_list

#== end of pcr_sort_list function =============================================

def pcr_sign(x):
    '''returns the sign of a PCRaster value field as a boolean map that is True \
when the value in the field is positive.'''

    return pcr.ifthenelse(pcr.abs(pcr.scalar(x)) != pcr.scalar(x), \
        pcr.boolean(0), pcr.boolean(1))

#== end of pcr_sign function ==================================================

def pcr_get_map_value( \
        pcrfield, 
        location = 1, \
        pcrfunc = 'areaaverage', \
        mv = -999.9, \
        format_str = '%.3f', \
        message_str = '', \
        test_verbose = False):

    '''
pcr_print_cell_value: generic function to return the value from a PCRaster field \
at a specified location. The location specified may be a cell number (default), \
a tuple containing the row, column number or a classified PCRaster map identifying \
points or locations. Output in that case is then dependent on the PCRaster area ... \
function specified and consists of a dictionary of key, value pairs; \
otherwise, the value is returned.

    Input:
    ======
    pcrfield:           PCRaster field for which the values are extracted; cast
                        as scalar in the function;
    location:           optional argument, default value is 1 (top-left cell);
                        the location specified may be a cell number (default),
                        or a list of locations or tuples containing the row,
                        column number or a classified PCRaster map identifying
                        points or areas;
    pcrfunc:            PCRaster function or string of the function name, \
                        either being the areaaverage, areatotal, areaminimum or
                        areamaximum. Default value is areaaverage; if the loc-
                        ation is not a map, this argument is ignored;
    mv:                 standard missing value identifier, default = -999.9;
    format_str:         string of format, default is %.3f;
    message_str:        text that is added to the returned message string,
                        default value is an empty string;
    test_verbose:       boolean variable, that will print the message string to
                        the screen if True; default value is False.

    Output:
    =======
    value:              value (float) or dictionary of floats retrieved from
                        the map on the basis of the specified location or loc-
                        ations. A single value is returned if only a single
                        location is included;
    message_str:        the composed message_str.

'''

    # initialize
    # set the value
    value = {1: None}
    
    # cast all variables as fields
    pcrfield = pcr.spatial(pcr.scalar(pcrfield))

    # test if the location is a PCRaster field
    if type(location) is pcr.Field:

        # set the function
        if type(pcrfunc) is str and len(pcrfunc) > 0:
            pcrfunc = getattr(pcr, pcrfunc)
        else:
            pcrfunc = pcr.areaaverage
            
        pcrfield = pcr.cover(pcrfunc(pcr.spatial(pcrfield), \
            location), mv)

        # retrieve the locations
        loc_a = pcr.pcr2numpy(location, 0)
        loc_ids = np.unique(loc_a)
        loc_ids= (loc_ids[loc_ids != 0]).tolist()
        loc_ids.sort()
        
        # insert the values
        val_a = pcr.pcr2numpy(pcrfield, 0)
        for loc_id in loc_ids:
            value[loc_id] = val_a[loc_a == loc_id][0]
            message_str = str.join('\n', (message_str, \
                '%3d: %s' % (loc_id, \
                     format_str % value[loc_id])))

    # location is not a PCRaster field
    else:
        
        # cast location as a list
        if not type(location) is list:
            location = [location]

        # extract the location iteratively
        for loc_id in range(len(location)):
            if type(location[loc_id]) is tuple:
                # get the value
                valx, valid = pcr.cellvalue(pcrfield, \
                        location[loc_id][0], location[loc_id][1])
            else:
                # get the value
                valx, valid = pcr.cellvalue(pcrfield, \
                        location[loc_id])
            # value returned, process
            if not valid:
                valx = mv
            # add valx to value and update the message string
            value[loc_id + 1] = valx
            message_str = str.join('\n', (message_str, \
                '%3d: %s' % (loc_id + 1, format_str % value[loc_id + 1])))

    # all data added, print the message string if test_verbose is True
    if test_verbose:
        print (message_str)

    # return the direct value
    if len(value) == 1:
        key = list(value.keys())[0]
        value = value[key]

    # return the value and message_str
    return value, message_str

#== end of pcr_get_map_value function =========================================

def pcr_return_val_div_zero(x, y, y_lim,\
            z_def = 0.00, test_absolute = False):
    '''
pcr_return_val_div_zero: function that tests the denominator in a division of \
PCRaster fields on the occurrence of (small) values and returns a default \
answer where this condition is met:

    z = x / y           if y > y_lim
    z = z_def           if y <= y_lim

This function is typically intended to avoid errors when dividing by zero.

    Input:
    ======
    x_num:              numerator of the fraction of which result is z;
    y_denom:            denominator of the fraction of which the result is z;
    y_lim:              value against which the denominator y is tested;
    z_def:              value that is returned if y <= y_lim; default value is
                        zero;
    test_absolute:      boolean variable that tests absolute values of y; this
                        value should be set to True if the function crosses
                        zero. Default is False.

    Output:
    =======
    z:                  result of the fraction x / y.

'''

    # get the sign
    if test_absolute:
        # test the positive values ofx and y against their original functions
        z_sign = pcr.ifthenelse(pcr.abs(x) != x, \
                     pcr.scalar(-1), pcr.scalar(1)) *\
                pcr.ifthenelse(pcr.abs(y) != y, \
                     pcr.scalar(-1), pcr.scalar(1))
        # get the result of the division
        # note that this is done in absolute terms and the sign is reliant on
        # the value of z_sign
        z = z_sign * pcr.ifthenelse(pcr.abs(y) > pcr.abs(y_lim), \
                pcr.abs(x) / pcr.max(pcr.abs(y_lim), pcr.abs(y)), \
                pcr.abs(z_def))
    else:
        z = pcr.ifthenelse(y > y_lim,x/pcr.max(y_lim, y),z_def)

    # return the result, z
    return z

#== end of pcr_return_val_div_zero function ===================================

def pcr_tanh(x):
    '''
pcr_tanh: returns the hyperbolic tangen for a PCRaster field (x) as \
(exp(2 * x)-1)/(exp(2 * x) + 1)

'''
    return (pcr.exp(2.00 * x) - 1.00) / (pcr.exp(2.00 * x) + 1.00)

#== end of pcr_tanh function ==================================================

def pcr_intersect_linear_functions(x0, x1, \
                                   y0, y1, \
                                   z0, z1):

    '''
    
pcr_intersect_linear_functions: function that finds the point xi, yi where two \
linear functions intersect. If the functions are parallel, no values are returned.

The functions have a general shape of:

    y = y0 + (x - x0) * (y1 - y0) / (x1 - x0)
    z = z0 + (x - x0) * (z1 - z0) / (x1 - x0)

And:
    xi = x0 + (x1 - x0) / (1 + (y1 - z1) / (z0 - y0))

which has a solution if the functions y and z are not parallel, so:

    (1 + (y1 - z1) / (z0 - y0)) <> 0


    Input:
    ======
    x0, x1:             points of the independent variables at which the func-
                        tions y and z are defined;
    y0, y1,
    z0, z1:             the corresponding points of these functions, on the
                        same axis.


    Output:
    =======
    xi, yi (zi):        the corresponding point of intersection.

It is expected that all input is consistent with PCRaster scalar fields.
If y and z are parallel, missing values for xi and yi are returned.

'''

    # compute the intersection of the slopes of the functions
    # if z0 ~ y0, the term, which is the denominator, becomes very large
    ab_term = pcr.ifthenelse(z0 != y0, \
                             1 + pcr_return_val_div_zero(y1 - z1, \
                                                         z0 - y0, \
                                                         very_small_number, \
                                                         very_small_number ** -1, \
                                                         test_absolute = True), \
                             1 + very_small_number ** -1)

    # get the intersection if not parallel
    xi = pcr.ifthen(ab_term != 0, \
                    pcr.ifthenelse(z0 != y0, \
                                   x0 + pcr_return_val_div_zero( \
                                                                x1 - x0, \
                                                                ab_term, \
                                                                very_small_number), \
                                   x0))
    yi = y0 + (xi - x0) * (y1 - y0) / (x1 - x0)

    # return xi, yi
    return xi, yi


#== end of pcr_intersect_linear_functions =====================================

def pcr_hill_climb(func, \
                   y_estimates, \
                   x_values, \
                   convergence_limit     = convergence_limit, \
                   max_number_iterations = max_number_iterations):

    '''

pcr_hill_climb: hill climbing function in PCRaster that can estimate a single, \
optimal value for a dependent variable y of the function y = f(x = y_est, x', x").

Note: function can be made more generic if the type of the dependent output \
variable is tested and then the convergence retrieved as a float.

    Input:
    ======
    func:           a function that returns the dependent variable
                    y as a result of the independent variables that include as
                    the first argument an estimate of the dependent variable y
                    and subsequently all other independent variables;
                    the approach requires that the output is a PCRaster map 
                    (or at least can be cast as such);
    y_estimates:    a tuple with the lower and upper bound for the dependent
                    variable y; this should be a PCRaster map or at least com-
                    patible with it;
    x_values:       a list or tuple with the invariable values for the other
                    independent variables;
    convergence_limit:
                    limit below which absolute changes in the estimate of the
                    dependent variable are assumed to have converged. Default
                    value is 1.0e-12;
    max_number_iterations:
                    cut-off for the maximum number of iterations; set to 100
                    by default.

    Output:
    y_estimate:     the estimate of the dependent variable.

'''
    # set the independent variables as lists
    xvars0 = [y_estimates[0]]
    xvars1 = [y_estimates[1]]
    for xvar in x_values:
        xvars0.append(xvar)
        xvars1.append(xvar)

    # get the new y_estimates
    y_estimates[0] = func(*xvars0)
    y_estimates[1] = func(*xvars1)

    # initialize the number of iterations
    # and the convergence criterion
    number_iterations = 0
    global_convergence = False
    update_mask = xvars0[0] != xvars1[0]

    # iterate while global convergence has not yet been achieved
    while not global_convergence:

        # guess a new y to evaluate and compute the corresponding y;
        # propagate the estimate in the tuple of estimates and values
        y_guess = pcr.ifthenelse(update_mask, \
                                 xvars0[0] - (y_estimates[0] - xvars0[0]) * \
                                 (xvars1[0] - xvars0[0]) / (y_estimates[1] - y_estimates[0] - \
                                                            xvars1[0] + xvars0[0]), \
                                 xvars1[0])

        # update the values
        xvars0[0] = xvars1[0]
        xvars1[0] = y_guess
        y_estimates[0] = y_estimates[1]
        y_estimates[1] = func(*xvars1)

        # check on convergence
        # this has to be a mask for PCRaster maps
        delta_y = pcr.abs(y_estimates[1] - xvars1[0])

        # evaluate convergence
        update_mask = update_mask & (delta_y >= convergence_limit)
        number_iterations = number_iterations + 1
        global_convergence = (pcr.cellvalue(pcr.mapmaximum(pcr.scalar( \
                                           pcr.cover(update_mask, 0))), 1)[0] == 0) \
                             or (number_iterations >= max_number_iterations)

    # return the estimated y value and the number of iterations
    return y_estimates[1], number_iterations

#== end of pcr_hillclimb function =============================================

###############################################################################
# end of the module with additional functions                                 #
###############################################################################
