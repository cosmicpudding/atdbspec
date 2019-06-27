import os
import sys
from astropy.io import ascii
import datetime
from modules.visfunc import *

###################################################################
# RA/DEC conversions

def ra2dec(ra):
	if not ra:
		return None
	  
	r = ra.split(':')
	if len(r) == 2:
		r.append(0.0)

	# Deal with when RA is actually HA and negative
	if r[0].startswith('-') or float(r[0]) < 0: 
		return (float(r[0]) - float(r[1])/60.0 - float(r[2])/3600.0)*15
	else:
		return (float(r[0]) + float(r[1])/60.0 + float(r[2])/3600.0)*15

def dec2dec(dec):
    if not dec:
        return None
    d = dec.split(':')
    if len(d) == 2:
        d.append(0.0)
    if d[0].startswith('-') or float(d[0]) < 0:
        return float(d[0]) - float(d[1])/60.0 - float(d[2])/3600.0
    else:
        return float(d[0]) + float(d[1])/60.0 + float(d[2])/3600.0

###################################################################


def get_cal():

	# Get LST
	lon = 6.60334
	utc_now = str(datetime.datetime.utcnow())
	currdate = utc_now.split()[0]
	currtime = utc_now.split()[1]
	utdec = str2dec(currtime)
	jd = juliandate(currdate,currtime)
	gst = ut2gst(jd,utdec)
	lst = gst2lst(gst,lon)
#	print ('LST:',dec2str(lst))

	# Return calibrator based on LST
	if lst < 3:
		bestcal = '3C48'
		ra,dec = ra2dec('01:37:41.2994'),dec2dec('33:09:35.134')
	elif lst < 9:
		bestcal = '3C147' 
		ra,dec = ra2dec('05:42:36.1379'),dec2dec('49:51:07.234')
	elif lst < 19.5:
		bestcal = '3C286'
		ra,dec = ra2dec('13:31:08.2879'),dec2dec('30:30:32.958')
	else:
		bestcal = '3C48'
		ra,dec = ra2dec('01:37:41.2994'),dec2dec('33:09:35.134')

	return (bestcal,ra,dec)


def get_cal_arts():

	# Get LST
	lon = 6.60334
	utc_now = str(datetime.datetime.utcnow())
	currdate = utc_now.split()[0]
	currtime = utc_now.split()[1]
	utdec = str2dec(currtime)
	jd = juliandate(currdate,currtime)
	gst = ut2gst(jd,utdec)
	lst = gst2lst(gst,lon)
#	print ('LST:',dec2str(lst))

	# Return calibrator based on LST
	if lst < 5:
		bestcal = 'B0329+54'
		ra,dec = 53.247367,54.578769
	elif lst < 11:
		bestcal = 'B0531+21' 
		ra,dec = 83.633221,22.014461
	elif lst < 14:
		bestcal = 'B0950+08'
		ra,dec = 148.288790,7.926597
	elif lst < 22:
		bestcal = 'B1933+16'
		ra,dec = 293.949275,16.277774
	else:
		bestcal = 'B0329+54'
		ra,dec = 53.247367,54.578769

	return (bestcal,ra,dec)

