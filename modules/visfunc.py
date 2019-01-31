from math import *

# String time to dec time
def str2dec(time):

    dectime = float(time.split(':')[0]) + float((time.split(':')[1]))/60.0 + float((time.split(':')[2]))/3600.0

    return dectime

def dec2str(dec):
    #if not dec:
    #    return None
    neg = 0
    if dec < 0:
        dec *= -1
        neg = 1
    dd = int(dec)
    diff = dec - dd
    mm = int(diff*60)
    diff = diff - (mm/60.0)
    ss = diff*3600
    if ss >= 59.995:
        ss = 00.0
        mm += 1

    if neg:
        str = '-%02d:%02d:%05.2f' % (dd, mm, abs(ss))
    else:
        str = '%02d:%02d:%05.2f' % (dd, mm, abs(ss))
    return str

def ra2str(ra):

    ra = ra/15.0
    hh = int(ra)
    diff = ra - hh
    mm = int(diff*60)
    diff = abs(diff - (mm/60.0))
    ss = diff*3600
    if ss >= 59.995:
        ss = 0
        mm += 1

    str = '%02d:%02d:%05.2f' % (hh, mm, ss)
    return str


# def dec2str(time):

#     strtime = str(dectime.split('.')[0]) + ':' + 

# convert to UT
def aest2ut(aest):

    hr = int(aest.split(':')[0])
    uthr = hr - 10
    if uthr < 0:
        uthr = uthr + 24
    ut = '%s:%s:%s' % (uthr,aest.split(':')[1],aest.split(':')[2])

    return ut

# Define equatorial to horizon
def eq2hor(ra,dec,UT,date,lon,lat):

    rahr = ra/15.
    hr = ra2hr(rahr,date,UT,lon)

    # Turn to degrees
    hrdeg = hr*15.

    # Get altitude
    alt = asin( sin(dec*pi/180.)*sin(lat*pi/180.) + cos(dec*pi/180.)*cos(lat*pi/180.)*cos(hrdeg*pi/180.))

    # Get azimuth
    az = acos( (sin(dec*pi/180.)-sin(lat*pi/180.)*sin(alt)) / (cos(lat*pi/180.)*cos(alt)))

    # Convert to degrees
    alt = alt*180/pi
    az = az*180/pi

    # Check sign
    if sin(hrdeg*pi/180.) > 0:
        az = 360 - az

    return alt,az

# Define equatorial to horizon
def hr2hor(hr,dec,lon,lat):

    # Turn to degrees
    hrdeg = hr*15.

    # Get altitude
    alt = asin( sin(dec*pi/180.)*sin(lat*pi/180.) + cos(dec*pi/180.)*cos(lat*pi/180.)*cos(hrdeg*pi/180.))

    # Get azimuth
    az = acos( (sin(dec*pi/180.)-sin(lat*pi/180.)*sin(alt)) / (cos(lat*pi/180.)*cos(alt)))

    # Convert to degrees
    alt = alt*180/pi
    az = az*180/pi

    # Check sign
    if sin(hrdeg*pi/180.) > 0:
        az = 360 - az

    return alt,az


def ra2hr(ra,date,UT,lon):
     # Note -- assume you enter in UT 
    utdec = float(UT.split(':')[0]) + float(UT.split(':')[1])/60. + float(UT.split(':')[2])/3600.

    # Get Julian date
    JD = juliandate(date,'00:00:00.0')

    # Now find Greenwich Sidereal Time
    gst = ut2gst(JD,utdec)
    lst = gst2lst(gst,lon)

    # Subtract
    hr = lst - ra
    if hr < 0:
        hr  = hr + 24

    return hr

# Define horizon to equatorial
def hor2eq(az,alt,UT,date):
    delta = asin( sin(alt*pi/180)*sin(lat*pi/180) + cos(alt*pi/180)*cos(lat*pi/180)*cos(az*pi/180) )
    Hdash = acos( (sin(alt*pi/180) - sin(lat*pi/180)*sin(delta))/(cos(lat*pi/180)*cos(delta)) )

    # Check sin(az)
    if sin(az*pi/180) > 0:
        H = 360 - Hdash*180/pi
    else:
        H = Hdash*180/pi
    H = H / 15.0

    # Get RA
    ra = hr2ra(H,date,UT)

    ra = ra * 15.
    dec = delta*180/pi
    return ra,dec

def juliandate(date,UT):
    [y,m,d] = [float(x) for x in date.split('-')]

    # Add time
    utdec = float(UT.split(':')[0]) + float(UT.split(':')[1])/60. + float(UT.split(':')[2])/3600.
    uthr = utdec/24.
    d = d+uthr

    # Find Julian Date
    if m == 1 or m == 2:
        ydash = y-1
        mdash = m+12
    else:
        ydash = y
        mdash = m

    # Calc A,B 
    if y > 1582:
        A = trunc(ydash/100.)
        B = 2 - A + trunc(A/4.)
    
    # Calc C
    if ydash < 0:
        C = trunc(365.25*ydash - 0.75)
    else:
        C = trunc(365.25*ydash)

    # Calc D
    D = trunc(30.6001 * (mdash+1))

    # Return date
    JD = B + C + D + d + 1720994.5
    return JD

def ut2gst(JD,utdec):

    # Calc variables
    S = JD - 2451545.0
    T = S/36525.0
    T0 = (6.697374558 + (2400.051336 * T) + (0.000025682 * T**2)) 
  
    # Get to the range 0-24
    if T0 > 0:
        while T0 > 24:
            T0 = T0 - 24
    if T0 < 0:
        while T0 < 0:
            T0 = T0 + 24

    utdec = utdec * 1.002737909

    # Update T0
    T0 = T0 + utdec 

    # Make sure in range 24
    if T0 > 0:
        while T0 > 24:
            T0 = T0 - 24
    if T0 < 0:
        while T0 < 0:
            T0 = T0 + 24

    gst = T0
    return gst

def gst2lst(gst,lon):
    # Note: GST in hr, lon in deg

    lonh = lon / 15.
    gst = gst + lonh

    # Range 0-24
    if gst < 0:
        gst = gst + 24
    elif gst > 24:
        gst = gst - 24
   
    # This is LST
    lst = gst
    return lst


def hr2ra(hr,date,UT):
    # Note -- assume you enter in UT 
    utdec = float(UT.split(':')[0]) + float(UT.split(':')[1])/60. + float(UT.split(':')[2])/3600.

    # Get Julian date
    JD = juliandate(date,'00:00:00.0')

    # Now find Greenwich Sidereal Time
    gst = ut2gst(JD,utdec)
    lst = gst2lst(gst,lon)

    # Subtract
    alpha = lst - hr
    if alpha < 0:
        alpha  = alpha + 24

    ra = alpha
    return ra


# Define UT calculation (needed?)
def calcUT(lst,date,lon):
    # Calculate GST
    # Longitude in decimal form (hours)
    # West = negative, east = positive
    lonh = lon / 15.
    gst = lst - lonh
    if gst < 0:
        gst = gst + 24
    elif gst > 24:
        gst = gst - 24
    # H:M:S mode
    gststr = ra2str(gst*15)
    [year,month,day] = [float(x) for x in date.split('-')]
    # Correction
    if month == 1 or month == 2:
        year = year - 1
        month = month + 12
    A = int(year/100)
    B = 2 - A + int(A/4)
    if year < 0:
        C = int((365.25 * year) - 0.75)
    else:
        C = int(365.25 * year)
    D = int(30.6001 * (month + 1))
    JD = B + C + D + day + 1720994.5
    S = JD - 2451545.0
    T = S/36525.0
    T0 = (6.697374558 + (2400.051336 * T) + (0.000025682 * T**2)) 
    # Get to the range 0-24
    if T0 > 0:
        while T0 > 24:
            T0 = T0 - 24
    if T0 < 0:
        while T0 < 0:
            T0 = T0 + 24
    E = gst - T0
    # Get in the range 0-24
    if E < 0:
        E = E + 24
    elif E > 24:
        E = E - 24
    UT = E * 0.9972695663
    UTstr = ra2str(UT*15)

    return(UTstr[0:8])
