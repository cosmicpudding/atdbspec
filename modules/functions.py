# APERTIF PARSET GENERATOR ATDB VERSION 1.2 (atdb_parsets.py) - now with ARTS
# Input: source text file
# V.A. Moss 19/12/2018 (vmoss.astro@gmail.com)

__author__ = "V.A. Moss"
__date__ = "$19-dec-2018 17:00:00$"
__version__ = "1.2"

import sys
from astropy.io import ascii
from modules.visfunc import *
from modules.beamcalc import *
from datetime import datetime,timedelta
import numpy as np

###################################################################
class Observation:

	def __init__(self):

		self.src = None
		self.ra = None
		self.ratype = 'field_ra'
		self.dec = None
		self.refbeam = None
		self.sdate = None
		self.edate = None
		self.weightpatt = None
		self.obsmode = None
		self.intfac = None
		self.telescopes = None
		self.centfreq = None
		self.obstype = None
		self.systemoffset = None
		self.parsetonly = None
		self.extra = None
		self.hadec = None

		# SC4 specific parameters
		self.sbeam = None
		self.ebeam = None
		self.pulsar = None

		# SC1 specific parameters
		self.sband = None
		self.eband = None
		self.parfile = None

		self.out = None


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
# Write source: Imaging

def writesource_imaging(obs):

	# Write to file (not plus=)
	obs.out.write("""atdb_service --field_name={obs.src} --{obs.ratype}={obs.ra:.6f} --field_dec={obs.dec:.6f} --field_beam={obs.refbeam} --starttime='{obs.sdate}' --endtime='{obs.edate}' --pattern={obs.weightpatt} --observing_mode={obs.obsmode} --integration_factor={obs.intfac} --telescopes={obs.telescopes} --central_frequency={obs.centfreq} --data_dir=/data/apertif/ --operation=specification --atdb_host=prod {obs.parsetonly} {obs.extra} {obs.hadec}\n\n""".format(**locals()))
	obs.out.flush()

###################################################################
# Write source: SC4

def writesource_sc4(obs):

	# Write to file (not plus=)
	obs.out.write("""atdb_service --field_name={obs.src} --{obs.ratype}={obs.ra:.6f} --field_dec={obs.dec:.6f} --field_beam={obs.refbeam} --starttime='{obs.sdate}' --duration={obs.duration} --pattern={obs.weightpatt} --integration_factor={obs.intfac} --observing_mode={obs.obsmode} --telescopes={obs.telescopes} --central_frequency={obs.centfreq} --data_dir=/data2/output/ --irods_coll=arts_main/arts_sc4 --science_mode=TAB --operation=specification --atdb_host=prod {obs.parsetonly} {obs.extra} {obs.hadec}\n\n""".format(**locals()))
	obs.out.flush()


###################################################################
# Write source: SC1

def writesource_sc1(obs):

	# Write to file (not plus=)
	obs.out.write("""atdb_service --field_name={obs.src} --{obs.ratype}={obs.ra:.6f} --field_dec={obs.dec:.6f} --field_beam={obs.refbeam} --starttime='{obs.sdate}' --duration={obs.duration} --pattern={obs.weightpatt} --integration_factor={obs.intfac} --observing_mode={obs.obsmode} --telescopes={obs.telescopes} --central_frequency={obs.centfreq} --par_file_name={obs.parfile} --start_band={obs.sband} --end_band={obs.eband} --data_dir=/data/01/Timing --irods_coll=arts_main/arts_sc1 --science_mode=TAB --number_of_bins=1024 --ndps=1 --parset_location=/opt/apertif/share/parsets/parset_start_observation_atdb_arts_sc1.template --operation=specification --atdb_host=prod {obs.parsetonly} {obs.extra} {obs.hadec}\n\n""".format(**locals()))
	obs.out.flush()

###################################################################
# Write source: SC4 (depreciated)

def writesource_sc4_cluster(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,out,observing_mode,telescopes,sbeam,ebeam,pulsar,duration,cluster_mode,start_tid,start_tnum,parsetonly):

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
def make_pointing(sdate_dt,edate_dt,ints,weightpatt,out,telescopes,observing_mode,parsetonly,hadec):

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

		writesource_imaging(x[4].date(),x[4].time(),x[5].date(),x[5].time(),x[1],x[2],x[3],ints,weightpatt,refbeam,out,telescopes,observing_mode,parsetonly,hadec)


###################################################################
# Create test observations
def generate_tests(names,ras,decs,patterns,beams,obs):

	start = obs.sdate
	end = obs.sdate + timedelta(seconds=int(obs.duration))

	for i in range(0,len(beams)):

		for j in range(0,len(patterns)):
			beam = beams[i]
			pattern = patterns[j]
			if i == (len(beams)-1) and len(beams) > 2:
				if pattern == 'square_39p1':
					ra = ras[i][0]
					dec = decs[i][0]
				else:
					ra = ras[i][1]
					dec = decs[i][1]									
			else:
				ra = ras[i]
				dec = decs[i]
			print(beam,pattern,ra,dec)

			name = names[i]

			# Update the values
			obs.sdate = start
			obs.edate = end
			obs.ra = ra
			obs.dec = dec
			obs.src = name
			obs.refbeam = beam 
			obs.weightpatt = pattern

			writesource_imaging(obs)

			start = end + timedelta(seconds=120)
			end = start + timedelta(seconds=int(obs.duration))

###################################################################
# Beam switching functionality

def make_beamswitch(obs):

	# Initialise
	old_edate = None
	old_etime = None
	srcname = obs.src
	total_sdate = obs.sdate
	total_edate = obs.edate

	# beam switching time (only relevant for imaging)
	bttime_set = 2 # min
	rndbm_set = list(np.arange(0,40)) # list(np.arange(0,40))

	# Randomise beams if there is a ? in the specification
	if '?' in obs.obstype:
		rndbm = [0]
		bm = 0
		for jj in range(0,int(numscans)):
			print('Finding beams...')

			# Note: this cannot handle 37 beams yet...
			while bm in rndbm:
				bm = int(rand()*36)
			rndbm.append(bm)
	elif obs.obstype == 'Ss':
		rndbm = rndbm_subset
		bttime = bttime_subset
	elif obs.obstype == 'S*':
		rndbm = rndbm_set	
		bttime = bttime_set				
	else:
		rndbm = rndbm_set	
		bttime = bttime_set
	nbeams = len(rndbm)
	print('Selected beams: ',rndbm)
	print('Number of beams: ',nbeams)	

	swtime = ((obs.duration / 60.) - 2 * (nbeams-1)) / nbeams
	step = swtime/60.

	# Step should not have microseconds!
	step = int(step*3600.)/3600.

	# Cal scans
	numscans = (obs.duration / 3600.) / (step + bttime/60.)# + 1 # edge effect
	print(step, step*60.,numscans,obs.duration / 60.)
	
	# Write the observations to a file:
	for k in range(0,int(numscans)+1):

		# Need to divide by num beams to decide which beam it will do?
		print(k)
		print(k % len(rndbm))
		chosenbeam = rndbm[k % len(rndbm)]
		print('chosen beam:',chosenbeam)

		beamname = 'B0%.2d' % chosenbeam
		obs.src = '%s_%s' % (srcname,chosenbeam)

		print(beamname,obs.src)

		# Calculate the new position for that given beam
		# Note: using compound beam positions
		ra_new,dec_new = calc_pos_compound(obs.ra,obs.dec,beamname)
		print(ra_new,dec_new)

		# New execute time
		print(old_edate,old_etime)

		# Recalculate the start and end time
		if k == 0:

			try:
				exectime = obs.sdate
			except ValueError:
				exectime = datetime.strptime(sdate+stime,'%Y-%m-%d%H:%M')

			sdate = exectime
			edate = exectime + timedelta(minutes=step*60.)

		else:
			try:
				exectime = datetime.strptime(old_edate+old_etime,'%Y-%m-%d%H:%M:%S')#+timedelta(seconds=15)
			except ValueError:
				exectime = datetime.strptime(old_edate+old_etime,'%Y-%m-%d%H:%M')
			sdate = exectime + timedelta(minutes=bttime)
			edate = exectime + timedelta(minutes=step*60.+bttime)

		# Check if the time has reached the right place
		if edate > total_edate or k > nbeams-1:
			continue

		# Update the obs class values
		obs.sdate = sdate
		obs.edate = edate
		obs.refbeam = chosenbeam

		# Write sources to file
		if obs.systemoffset == True:
			refbeam = str(chosenbeam)
			writesource_imaging(obs)		
		else:
			writesource_imaging(obs)		

		# update parameters
		old_etime = str(edate.time())
		old_edate = str(edate.date())
		print(old_edate,old_etime)



