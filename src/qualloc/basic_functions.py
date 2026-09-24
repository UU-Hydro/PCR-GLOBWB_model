""" """

import sys

import numpy as np
import pcraster as pcr

critical_improvements = str.join("\n\t", ("",))

development = str.join(
    "\n\t",
    (
        "",
        "include generic function to split string to lists",
        "",
    ),
)

print("\nDevelopmens for basic functions:")

if len(critical_improvements) > 0:
    print("Critical improvements: \n%s" % critical_improvements)

if len(development) > 0:
    print("Ongoing: \n%s" % development)

if len(critical_improvements) > 0:
    sys.exit()


very_small_number = 1.0e-12
convergence_limit = 1.0e-12
max_number_iterations = 100


# generic functions to process lists


def sum_list(list_in):
    """
sum_list: generic function that returns the sum of a list of which \
the entries can be summed (integers, floats, arrays etc.).

"""
    # sum all entries of a list-like object
    return sum(list_in)


def max_dicts(dict_in):
    """
max_dicts: generic function that returns the maximum pcr map from a collection \
of arrays contained in a dictionary.

"""
    map_maximum = None

    # maximum, comparing maps in pairs
    for key, values in dict_in.items():
        if isinstance(map_maximum, type(None)):
            map_maximum = values

        else:
            map_maximum = pcr.max(values, map_maximum)

    return map_maximum


def get_decision(question_str, possible_outcomes):
    """
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

    """

    options = list(possible_outcomes.keys())
    option_str = "("
    for option in options:
        option_str = str.join("", (option_str, option, ", "))
    option_str = option_str.rstrip(", ")
    option_str = str.join("", (option_str, ")\n> "))
    question_str = str.join(" ", (question_str.rstrip(), option_str))

    outcome = None
    selected_option = ""
    while selected_option not in options:
        selected_option = input(question_str)

    outcome = possible_outcomes[selected_option]

    return outcome


def convert_string_to_list(s, separators=[",", ";"]):
    """

convert_string_to_list: function that converts a string with separators into \
a (nested) list.

"""

    if not isinstance(s, str):

        sys.exit("function requires a string to split it in smaller parts")

    result_list = [s]
    sep_level = 0

    while len(separators) > 0:

        separator = separators.pop()

        # split each entry into sub-levels
        for ix in range(len(result_list)):
            ss = result_list[ix]
            result_list[ix] = ss.split(sep=separator)

        # avoid nesting the first list
        if sep_level == 0:
            result_list = result_list[0][:]

        sep_level = sep_level + 1

    return result_list


# additional PCRaster functions


def pcr_get_statistics(pcrfield, np_stat_funcs=[np.average, np.min, np.max], mv=-999.9):
    """
pcr_get_statistics: returns the statistics of all values in a PCRaster field \
as specified by numpy functions in the np_stat_funcs list with the missing values \
masked out.

Returns a dictionary with the name of the numpy functions as keys and the count
    
"""
    a = pcr.pcr2numpy(pcr.scalar(pcrfield), mv).astype(np.float32)
    a = a[a != mv]

    if a.size > 0:
        stat_val = dict((str(f.__name__), f(a)) for f in np_stat_funcs)
    else:
        stat_val = dict((str(f.__name__), mv) for f in np_stat_funcs)
    stat_val["count"] = a.size

    return stat_val


def pcr_return_val_div_zero(x, y, y_lim, z_def=0.00, test_absolute=False):
    """
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

"""

    if test_absolute:
        # test the positive values of x and y against their original functions
        z_sign = pcr.ifthenelse(
            pcr.abs(x) != x, pcr.scalar(-1), pcr.scalar(1)
        ) * pcr.ifthenelse(pcr.abs(y) != y, pcr.scalar(-1), pcr.scalar(1))
        # the division is done in absolute terms; the sign follows from z_sign
        z = z_sign * pcr.ifthenelse(
            pcr.abs(y) > pcr.abs(y_lim),
            pcr.abs(x) / pcr.max(pcr.abs(y_lim), pcr.abs(y)),
            pcr.abs(z_def),
        )
    else:
        z = pcr.ifthenelse(y > y_lim, x / pcr.max(y_lim, y), z_def)

    return z
