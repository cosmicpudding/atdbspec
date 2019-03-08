# APERTIF PARSET GENERATOR ATDB VERSION 1.2 (atdb_parsets.py) - now with ARTS
# Input: source text file
# V.A. Moss 19/12/2018 (vmoss.astro@gmail.com)

__author__ = "V.A. Moss"
__date__ = "$19-dec-2018 17:00:00$"
__version__ = "1.2"

from datetime import datetime,timedelta
import sys
from astropy.io import ascii
from modules.visfunc import *
import numpy as np


###################################################################
# RA/DEC conversions

def ra2dec(ra):
    if not ra:
        return None
      
    r = ra.split(':')
    if len(r) == 2:
        r.append(0.0)
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
# Write source: Imaging

def writesource_imaging(date,stime,date2,etime,src,ra,dec,ints,weightpatt,refbeam,out,telescopes,observing_mode,parsetonly):

	# Write to file (not plus=)
	out.write("""atdb_service --field_name=%s --field_ra=%.6f --field_dec=%.6f --field_beam=%s --starttime='%s %s' --endtime='%s %s' --pattern=%s --observing_mode=%s --integration_factor=%s --telescopes=%s --central_frequency=1400 --data_dir=/data/apertif/ --operation=specification --atdb_host=prod %s\n\n""" % (src,ra,dec,refbeam,date,stime,date2,etime,weightpatt,observing_mode,ints,telescopes,parsetonly))
	out.flush()

###################################################################
# Write source: SC4

def writesource_sc4(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,telescopes,duration,parsetonly):


	# Write to file (not plus=)
	out.write("""atdb_service --field_name=%s --field_ra=%.6f --field_dec=%.6f --field_beam=%s --starttime='%s %s' --duration=%s --pattern=%s --integration_factor=%s --observing_mode=%s --telescopes=%s --central_frequency=1400 --data_dir=/data2/output/ --irods_coll=arts_main/arts_sc4 --science_mode=IAB --operation=specification --atdb_host=prod %s\n\n""" % (src,ra,dec,refbeam,date,stime,duration,weightpatt,ints,observing_mode,telescopes,parsetonly))
	out.flush()

	return scan

###################################################################
# Write source: SC1

def writesource_sc1(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,telescopes,sband,eband,parfile,duration,parsetonly):

	# Write to file (not plus=)
	out.write("""atdb_service --field_name=%s --field_ra=%.6f --field_dec=%.6f --field_beam=%s --starttime='%s %s' --duration=%s --pattern=%s --integration_factor=%s --observing_mode=%s --telescopes=%s --par_file_name=%s  --start_band=%s --end_band=%s --science_mode=TAB --number_of_bins=1024 --central_frequency=1400 --ndps=1 --irods_coll=arts_main/arts_sc1 --data_dir=/data/01/Timing --parset_location=/opt/apertif/share/parsets/parset_start_observation_atdb_arts_sc1.template --operation=specification --atdb_host=prod %s\n\n""" % (src,ra,dec,refbeam,date,stime,duration,weightpatt,ints,observing_mode,telescopes,parfile,sband,eband,parsetonly))
	out.flush()

	return scan


###################################################################
# Write source: SC4

def writesource_sc4_cluster(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,telescopes,sbeam,ebeam,pulsar,duration,cluster_mode,start_tid,start_tnum,parsetonly):

	# Cluster start time
	sdate_dt = datetime.strptime(str(date)+str(stime),'%Y-%m-%d%H:%M:%S')
	stime_cluster = (sdate_dt - timedelta(minutes=5)).time()

	# Write to file (not plus=)
	if pulsar.lower() == 'true':
		cmd = ("""sleepuntil_utc %s %s
start_obs --mac --obs_mode survey --proctrigger --source %s --ra %s --dec %s --tstart "%sT%s" --duration %s --sbeam %s --ebeam %s --pulsar %s""" % (date,stime_cluster,src,ra,dec,date,stime,duration,sbeam,ebeam,parsetonly))
	else:
		cmd = ("""sleepuntil_utc %s %s
start_obs --mac --obs_mode survey --proctrigger --source %s --ra %s --dec %s --tstart "%sT%s" --duration %s --sbeam %s --ebeam %s %s""" % (date,stime_cluster,src,ra,dec,date,stime,duration,sbeam,ebeam,parsetonly))

	# Cluster mode hack
	if cluster_mode == 'ATDB':

		#make the date format
		tid_date = datetime.strftime(sdate_dt,'%y%m%d')
		cmd = cmd + ' --atdb --taskid %s%.3d\n\n' % (tid_date,start_tid+start_tnum) 
	else:
		cmd = cmd + '\n\n'

	# Write out at the end
	out.write(cmd)
	out.flush()


	return scan

###################################################################
# Convert pointing observation into a series of observations
def make_pointing(sdate_dt,edate_dt,ints,weightpatt,out,telescopes,observing_mode,parsetonly):

	# Location (WSRT)
	lat = 52.91474
	lon = 6.60334

	print(sdate_dt,edate_dt,ints,weightpatt)
	
	# Read the pointing table
	d = ascii.read('modules/stfma_v3.t')
	print(d.keys())
	
	chosen_sources = []

	# Find the closest match
	src_index = d['OBS']
	lst1 = [ra2dec(d['STIM'][i])/15. for i in range(0,len(d))]
	lst2 = [ra2dec(d['ETIM'][i])/15. for i in range(0,len(d))]
	src = d['FIELD']
	ra = d['RA']
	dec = d['DEC']
	#average_ha = 0.5 * (ha1+ha2) 
	
	# Datestamps 
	points_time = [calcUT(lst1[i],str(sdate_dt.date()),lon) for i in range(0,len(lst1))]
	points_dt = [datetime.strptime(str(sdate_dt.date())+points_time[i],'%Y-%m-%d%H:%M:%S') for i in range(0,len(points_time))]
	#print(points_dt)

	diff = np.array([abs(points_dt[i]-sdate_dt) for i in range(0,len(points_dt))])
	min_diff = min(diff)
	min_index = np.argmin(diff)
	print(src_index[min_index],min_index,diff[min_index],points_dt[min_index],sdate_dt)
	print(src[min_index],ra[min_index],dec[min_index])

	# Change if not quite right
	if points_dt[min_index] < sdate_dt:
		min_index+=1

		print(min_index,diff[min_index],points_dt[min_index],sdate_dt)
		print(src[min_index],ra[min_index],dec[min_index])

	# append the first
	src_start_dt = datetime.strptime(str(sdate_dt.date())+calcUT(lst1[min_index],str(sdate_dt.date()),lon),'%Y-%m-%d%H:%M:%S')
	src_end_dt = datetime.strptime(str(sdate_dt.date())+calcUT(lst2[min_index],str(sdate_dt.date()),lon),'%Y-%m-%d%H:%M:%S')
	currdate = str(src_start_dt.date())

	old_src_start_dt = None
	old_src_end_dt = None

	while src_end_dt <= edate_dt and src_start_dt <= edate_dt:


		src_start_dt = datetime.strptime(currdate+calcUT(lst1[min_index],currdate,lon),'%Y-%m-%d%H:%M:%S')
		src_end_dt = datetime.strptime(currdate+calcUT(lst2[min_index],currdate,lon),'%Y-%m-%d%H:%M:%S')

		# need to modify these to be round numbers of 10s... 
		if src_start_dt.second % 10 !=  0:
			remainder = src_start_dt.second % 10

			if remainder <= 5: 
				src_start_dt = src_start_dt - timedelta(seconds=remainder)
			else:
				src_start_dt  = src_start_dt + timedelta(seconds=(10 - remainder))

		src_end_dt = src_start_dt + timedelta(minutes=16, seconds=10) 

		if src_start_dt > edate_dt or src_end_dt > edate_dt:
			break

		if old_src_end_dt != None:
			if src_end_dt.date() > old_src_end_dt.date():
				#src_end_dt = src_end_dt + timedelta(days=1)
				currdate = str(src_end_dt.date())

		chosen_sources.append([min_index+1,src[min_index],(ra[min_index]),(dec[min_index]),src_start_dt,src_end_dt,src_index[min_index]])
		min_index+=1

		if min_index >= len(d):
			min_index = 0

		old_src_start_dt = src_start_dt
		old_src_end_dt = src_end_dt 

	for x in chosen_sources:
		print(x[6],x[0],x[1],x[2],x[3],'s',x[4],x[5])
		refbeam = '0'

		writesource_imaging(x[4].date(),x[4].time(),x[5].date(),x[5].time(),x[1],x[2],x[3],ints,weightpatt,refbeam,out,telescopes,observing_mode,parsetonly)


###################################################################
# Create test observations
def generate_tests(src,ra,dec,duration,patterns,beams,sdate_dt,ints,out,telescopes,observing_mode,parsetonly):

	start = sdate_dt
	end = sdate_dt + timedelta(seconds=int(duration))

	for i in range(0,len(beams)):

		for j in range(0,len(patterns)):

			beam = beams[i]
			pattern = patterns[j]
			print(beam,pattern)

			if beam != 0:
				name = src + '_%i' % beam
			else:
				name = src

			writesource_imaging(start.date(),start.time(),end.date(),end.time(),name,ra,dec,ints,pattern,beam,out,telescopes,observing_mode,parsetonly)

			start = end + timedelta(seconds=120)
			end = start + timedelta(seconds=int(duration))







