# Drift scan calculations
__author__ = "L.C. Oostrum"
__date__ = "$06-may-2019 12:00:00$"
__version__ = "1.0"


import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation, SkyCoord, Angle, FK5


# Location of WSRT
WSRT = EarthLocation(lat=52.91460037 * u.deg, lon=6.60449982 * u.deg, height=16.8 * u.m)
# Size of one compound beam (value from K.M. Hess)
CBSIZE = Angle("33.7'")


def calc_drift(coord, tstart, num_beam=1, margin="60'"):
    """
    Generate a drift scan observation
    :param coord: (ra, dec) in decimal degrees (float, float)
    :param tstart: Start time of observation (convertible to astropy.time.Time)
    :param num_beam: Number of compound beam sizes to drift through (int) [optional, default: 1]
    :param margin: Offset from center of beam to start drift at (convertible to astropy angle) [optional, default: 60 arcmin]

    returns:
    start_ha: hour angle at start time of observation in hh:mm:ss (str)
    duration: duration of observation in seconds (str)

    """

    # convert coord to SkyCoord
    source = SkyCoord(*coord, unit=(u.degree, u.degree))

    # ensure tstart is astropy time object
    if not isinstance(tstart, Time):
        tstart = Time(tstart)

    # ensure margin is angle
    if not isinstance(margin, Angle):
        margin = Angle(margin)

    # get the duration of from the source dec and scan size
    duration = calc_duration(source.dec, num_beam, margin)

    # calculate start RA:
    # margin is offset from center of first beam to start of observation
    # take care of cos(Dec) factor
    shift = margin / np.cos(source.dec)
    # starting point is source RA minus the shift
    start_ra = (source.ra - shift)

    # convert to hour angle
    start_ha = ra_to_ha(start_ra, tstart)

    # format return values
    # HA to hh:mm:ss.sss
    start_ha_formatted = start_ha.to_string(unit=u.hourangle, sep=':', pad=True, precision=3)
    # duration to string of integer
    duration_formatted = str(int(np.ceil(duration.to(u.second).value)))

    return start_ha_formatted, duration_formatted


def ra_to_ha(ra, time):
    """
    Convert Right Ascension to Hour angle at given time
    :param ra: Right Ascension (astropy quantity)
    :param time: Time (astropy.time.Time)
    
    returns:
    ha: Hour angle (astropy quantity)
    """

    # Convert J2000 to RA at start time
    equinox = 'J{}'.format(time.decimalyear)
    tmpcoord = SkyCoord(ra, 0*u.deg)
    ra_apparent = tmpcoord.transform_to(FK5(equinox=equinox)).ra

    # get LST at WSRT
    lst = time.sidereal_time('apparent', WSRT.lon)
    # Convert HA to RA
    ha = lst - ra_apparent
    # wrap in range [-180, 180] deg
    ha.wrap_at('180d', inplace=True)

    return ha


def calc_duration(dec, num_beam, margin):
    """
    Calculate required duration of drift scan and associated size on sky
    :param dec: Source declination (astropy quantity)
    :param num_beam: Number of compound beam sizes to drift through (int)
    :param margin: Extra margin on either size of the scan in arcmin (astropy quantity)

    returns:
    duration: scan duration in seconds (astropy quantity)
    size: total size of scan in arcmin (astropy quantity)
    """

    # calculate total size of scan
    # margin already includes first half of first beam and last half of last beam, 
    # so lower num_beam by one
    size = ((num_beam-1) * CBSIZE + 2*margin).to(u.arcmin) / np.cos(dec)
    # convert to duration using Earth drift rate of 360 deg / 24 hour
    duration = (size / (15*u.arcmin/u.minute)).to(u.second)

    return duration
    
