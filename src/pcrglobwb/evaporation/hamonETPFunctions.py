import math

import pcraster as pcr

# note: PCRaster computes trigonometric functions in degrees by default (unlike C and Python);
# convert all arguments to degrees using * 180 / pi


def HamonPotET(airT, doy, lat):

    reset_globaloption_to_radians = False
    if float(pcr.sin(90.0)) < 1.0:
        pcr.setglobaloption("degrees")
        reset_globaloption_to_radians = True

    rhoSat = 2.167 * satPressure(airT) / (airT + 273.15)

    dayLen = dayLength(doy, lat)

    # 2 * dayLen = day length as fraction
    pet = 165.1 * 2.0 * dayLen * rhoSat
    # mm to m
    pet = pet / 1000

    if reset_globaloption_to_radians:
        pcr.setglobaloption("radians")

    return pet


def dayLength(doy, lat):
    """daylength fraction of day"""
    lat = lat * pcr.scalar(math.pi) / 180.0
    M_PI_2 = pcr.spatial(pcr.scalar(math.pi / 2.0))
    dec = pcr.sin((6.224111 + 0.017202 * doy) * 180.0 / math.pi)
    dec = pcr.scalar(
        0.39785
        * pcr.sin(
            (4.868961 + 0.017203 * doy + 0.033446 * pcr.sin(dec * 180 / math.pi))
            * 180
            / math.pi
        )
    )
    dec = pcr.scalar(pcr.asin(dec))
    lat = pcr.ifthenelse(
        pcr.abs(lat) > M_PI_2,
        (M_PI_2 - pcr.scalar(0.01))
        * pcr.ifthenelse(lat > 0, pcr.scalar(1.0), pcr.scalar(-1.0)),
        lat,
    )
    arg = pcr.tan(dec) * pcr.tan(lat * 180.0 / math.pi) * -1.0
    h = pcr.scalar(pcr.acos(arg))
    h = h / 180.0 * math.pi
    # sun stays below horizon
    h = pcr.ifthenelse(arg > 1.0, 0.0, h)
    # sun stays above horizon
    h = pcr.ifthenelse(arg < -1.0, math.pi, h)
    return h / math.pi


def satPressure(airT):
    """calculates saturated vp from airt temperature Murray (1967)"""
    # airT: air temperature (degC)
    satPressure = pcr.ifthenelse(
        airT >= 0.0,
        0.61078 * pcr.exp(17.26939 * airT / (airT + 237.3)),
        0.61078 * pcr.exp(21.87456 * airT / (airT + 265.5)),
    )
    return satPressure
