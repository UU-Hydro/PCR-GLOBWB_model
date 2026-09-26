import calendar
import datetime
import logging
from copy import deepcopy

import numpy as np

logger = logging.getLogger(__name__)


def get_weights_from_dates(dates):

    # weights of the time increments of dates over the total length; input is a
    # sequence of dates (list, numpy array), output is a dictionary with the dates
    # as keys

    seq_type = type(dates)

    d = deepcopy(dates)

    if seq_type == list:
        d = np.array(d)

    # flatten and sort the dates
    d = d.ravel()
    d.sort()

    w = np.zeros(d.size)

    # add a final date
    d = np.append(d, datetime.datetime(d[0].year + 1, d[0].month, d[0].day))

    # iterate over the weights to get the date differences
    delta_d = d[-1] - d[0]
    for ix in range(w.size):

        w[ix] = (d[ix + 1] - d[ix]) / delta_d

    # cast the weights to the desired type
    if seq_type == list:
        w = w.tolist()

    return dict((d[ix], w[ix]) for ix in range(len(w)))


def get_julian_daynumber(date):

    # integer julian day number of a date

    return int((date - datetime.datetime(date.year, 1, 1)).days)


def match_date_by_julian_number(date, dates, within_same_month=True):
    """
    Output:
    =======
match_date_by_julian_number: function that allows for date substitution in the water management \
module.

    Input:
    ======
    date:                   date provided;
    dates:                  array of available dates to which the provided
                            dates should be matched;
    date_selection_method:  date selection method, default value is 'exact';
                            can be 'exact', 'before', or 'after'.

    Output:
    =======
    date_index:             date index matching the sought date to the av-
                            ailable dates;
    matched_date:           the date in the available dates that matches the
                            date index;
    message_str:            message string on the date selction for subsequent
                            logging.

"""

    message_str = ""

    julian_day = get_julian_daynumber(date)
    month = date.month
    year = date.year

    if isinstance(dates, list):
        dates = np.array(dates)

    julian_days = np.zeros(dates.shape, dtype=int)
    months = np.zeros(dates.shape, dtype=int)
    years = np.zeros(dates.shape, dtype=int)
    ix = 0
    for sdate in dates:
        julian_days[ix] = get_julian_daynumber(sdate)
        months[ix] = sdate.month
        years[ix] = sdate.month
        ix = ix + 1

    ixs = np.arange(dates.size, dtype=int)
    ixs.shape = dates.shape

    devs = np.abs(julian_days - julian_day)

    if within_same_month and np.any(months == month):
        mask = months == month
    else:
        mask = months != 13
        if within_same_month:
            message_str = (
                "; Warning: month %d is not present in the provided dates" % month
            )

    if year in years:
        mask = mask & (years == year)

    # halt if the mask selects nothing
    if np.size(devs[mask]) > 0:

        devs = devs[mask]
        ixs = ixs[mask]

        min_dev = devs.min()
        date_index = int(ixs[devs == min_dev][0])

    matched_date = dates[date_index]
    message_str = str.join(
        "",
        (
            "date %s is matched with %s in the available dates" % (date, matched_date),
            message_str,
        ),
    )

    return date_index, matched_date, message_str


def is_last_day_month(date):
    """returns if it is thelast of of the month"""
    today = date.day
    last_day = calendar.monthrange(date.year, date.month)[1]
    return today == last_day


class model_time(object):
    # timer of the model: initializes and updates the continuous timer and
    # julian day number

    def __init__(
        self,
        startyear,
        endyear,
        time_increment,
        time_step_length=1.00,
    ):

        object.__init__(self)

        self.seconds_per_day = 86400

        self.time_step_length = time_step_length
        self.startyear = startyear
        self.endyear = endyear
        self.time_increment = time_increment
        self.startdate = datetime.datetime(self.startyear, 1, 1)
        self.enddate = datetime.datetime(self.endyear, 12, 31)
        self.date = self.startdate

        # length of the simulation
        if self.time_increment == "daily":
            self.number_time_steps = (
                int(((self.enddate - self.date).days) / self.time_step_length) + 1
            )
        elif self.time_increment == "monthly":
            self.number_time_steps = int((endyear - startyear) + 1) * 12
        else:
            raise ValueError(
                "time increment %s cannot be used; use daily or monthly"
                % self.time_increment
            )

        self.report_flags = {}.fromkeys(["daily", "monthly", "yearly"], False)

        # special markers, all False by default
        self.last_day_of_month = False
        self.last_day_of_year = False
        self.last_time_step = False

    def __repr__(self):
        return (
            "this is an instance of the Caleros time class object with date %s"
            % self.__str__
        )

    def __str__(self):
        return self.date

    def update(self, increment):
        # increment the date by one time step
        if self.time_increment == "daily":
            self.time_step_length = 1
            self.date = self.startdate + datetime.timedelta(
                days=(increment - 1) * self.time_step_length
            )
        elif self.time_increment == "monthly":
            year = self.startdate.year + (increment - 1) // 12
            if increment % 12 == 0:
                month = 12
            else:
                month = increment % 12
            self.date = datetime.datetime(year, month, 1)
            self.time_step_length = calendar.monthrange(year, month)[1]
        else:
            raise ValueError(
                "time increment %s cannot be used; use daily or monthly"
                % self.time_increment
            )

        self.year = self.date.year
        month = self.date.month
        day = self.date.day

        self.julianday = get_julian_daynumber(self.date)

        # special markers for daily time increments
        if self.time_increment == "daily":
            self.report_flags["daily"] = True
            number_days = calendar.monthrange(self.year, month)[1]
            self.report_flags["monthly"] = day == number_days
            if self.report_flags["monthly"] and month == 12:
                self.last_day_of_year = True
            else:
                self.last_day_of_year = False
        elif self.time_increment == "monthly":
            self.report_flags["daily"] = False
            self.report_flags["monthly"] = True
            self.last_day_of_year = month == 12
        else:
            # should not happen; all flags disabled
            self.report_flags = {}.fromkeys(["daily", "monthly", "yearly"], False)
        self.report_flags["yearly"] = self.last_day_of_year

        self.last_time_step = increment == self.number_time_steps

        message_str = "processing %s" % self.date
        logger.info(message_str)
