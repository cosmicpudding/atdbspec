# APERTIF PARSET GENERATOR ATDB VERSION 1.2 (atdb_parsets.py) - now with ARTS
# Input: source text file
# V.A. Moss 19/12/2018 (vmoss.astro@gmail.com)
__author__ = "V.A. Moss"
__date__ = "$19-dec-2018 17:00:00$"
__version__ = "1.2"

import os
import sys
from modules.beamcalc import *
from datetime import datetime,timedelta
from astropy.io import ascii
import numpy as np
from argparse import ArgumentParser, RawTextHelpFormatter
from modules.functions import *
import time

def main():
	"""
    The main program to be run.
    :return:
    """

    # Time the total process length
	start = time.time()

	# Parse the relevant arguments
	parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
	parser.add_argument('-f', '--filename',
			default='input/ARTS_SC4_20190115.csv',
			help='Specify the input file location (default: %(default)s)')	
	parser.add_argument('-m', '--mode',
			default='SC4',
			help='Specify whether mode is imaging/SC1/SC4 (default: %(default)s)')
	parser.add_argument('-t', '--telescopes',
			default='23568ABCD',
			help='Specify which telescopes to include (default: %(default)s)')

	# Parse the arguments above
	args = parser.parse_args()


	# Weight pattern dictionary
	weightdict = {'compound': 'square_39p1',
				  'XXelement': 'central_element_beams_x_37beams',
				  'YYelement': 'central_element_beams_y_37beams',
				  'hybrid': 'hybridXX_20180928_8bit'}

	# beam switching time (only relevant for imaging)
	#swtime_set = 15 # min
	swtime_set = 5 # min
	bttime_set = 2 # min
	rndbm_set = list(np.arange(0,40))

	# Other case
	swtime_subset = 15 # min
	bttime_subset = 10 # min
	rndbm_subset = [0,10,16,17,23]

	# renumber scans
	renum = False 
	system_offset = False # default

	# specify the filename
	fname = args.filename

	# offset (if local time)
	offset = 0 # hours

	################################################

	# Read file (either tab or comma separated)
	try:
		d = ascii.read(fname,delimiter=',',guess=False)
	except:
		d = ascii.read(fname,delimiter='\s',guess=False)

	print(list(d.keys())) 

	# Start the file
	outname = '%s_%s.sh' % (fname.split('.')[0],args.mode)
	out = open(outname,'w')
	out.write('#!/bin/bash\n# Script to create commands for Apertif ATDB\n# Automatic generation script by V.A. Moss 04/10/2018\n# Last updated by V.A. Moss 03/01/2019\n\n')
	out.flush()

	if args.mode == 'SC4':

		# Start the file
		outname2 = '%s_%s_cluster.sh' % (fname.split('.')[0],args.mode)
		out2 = open(outname2,'w')
		out2.write('#!/bin/bash\n# Script to create commands for ARTS SC4 cluster\n# Automatic generation script by V.A. Moss 07/12/2018\n# Last updated by V.A. Moss 07/12/2018\n\nsource $HOME/ARTS-obs/setup_env.sh\n\n')
		out2.flush()


	# Task ID counter
	j = 0
	sendcmd = 'send_file -t 0'

	# Initialise
	old_date = None
	old_etime = None

	# Loop through sources
	for i in range(0,len(d)):

		# Get the common parameters for all
		src = d['source'][i]
		stime = d['time1'][i]
		try:
			stime_dt = datetime.strptime(stime,'%H:%M:%S')
		except ValueError:
			stime_dt = datetime.strptime(stime,'%H:%M')
		stime_dt = stime_dt + timedelta(hours=offset)

		date = d['date1'][i]
		scan = 0 #  d['scan'][i]
		src_obstype = '-'

		# Observing mode
		if args.mode == 'SC4':
			observing_mode = 'arts_sc4_survey'
			start_beam = d['sbeam'][i]
			end_beam = d['ebeam'][i]
			pulsar = d['pulsar'][i]

		elif args.mode == 'SC1':
			observing_mode = 'arts_sc1_timing'
			sband = d['sband'][i]
			eband = d['eband'][i]
			parfile = d['par'][i]
		else:
			observing_mode = 'imaging'

		# Fix times if they aren't the right length
		if len(stime.split(':')[0]) < 2:
			stime = '0'+stime

		# Get ref beam
		try:
			refbeam = d['beam'][i]
		except:
			refbeam = '0'

		# Endtime or duration
		if 'time2' in d.keys():
			etime = d['time2'][i]

			if len(etime.split(':')[0]) < 2:
				etime = '0'+etime
			try:
				etime_dt = datetime.strptime(etime,'%H:%M:%S')
			except ValueError:
				etime_dt = datetime.strptime(etime,'%H:%M')
			etime_dt = etime_dt + timedelta(hours=offset)

		elif 'duration' in d.keys():
			etime_dt = stime_dt + timedelta(seconds=float(d['duration'][i]))
			etime = str(etime_dt.time())
			duration = d['duration'][i]

		try:
			ints = d['int'][i]
		except: 
			if args.mode == 'SC4':
				ints = 30
			elif args.mode == 'SC1':
				ints = 20

		# Define weight pattern
		try:
			weightpatt = weightdict[d['weight'][i]]
		except:
			weightpatt = 'square_39p1'

		# Parse the Position coordinates
		if 'deg' in d['ra'][i]:
			ra = float(d['ra'][i].split('deg')[0])
			dec = float(d['dec'][i].split('deg')[0])

		# With :
		elif ':' in d['ra'][i]:
			ra = ra2dec(d['ra'][i])
			dec = dec2dec(d['dec'][i])

		# With HMS
		else:
			ra = ra2dec(d['ra'][i].replace('h',':').replace('m',':').replace('s',''))
			dec = dec2dec(d['dec'][i].replace('d',':').replace('m',':').replace('s',''))		

		# Imaging specific things
		if args.mode == 'imaging':
			src_obstype = d['type'][i]
			#lo = d['lo'][i]
			#sub1 = d['sub1'][i]
			#field = d['intent'][i].upper()

			# System offset stuff
			if d['switch_type'][i] == 'system':
				system_offset = True
			elif d['switch_type'][i] == 'manual':
				system_offset = False

				if 'S' not in src_obstype:
					beamname = 'B0%.2d' % refbeam
					if d['weight'][i] == 'XXelement' or d['weight'][i] == 'YYelement':
						ra_new,dec_new = calc_pos(ra,dec,beamname)
					elif d['weight'][i] == 'compound':
						ra_new,dec_new = calc_pos_compound(ra,dec,beamname)
					else:
						print (weightpatt)
					#print(beamname,ra_new,dec_new,ra,dec)
					ra,dec = ra_new,dec_new
					refbeam = '0'

			elif d['switch_type'][i] == '-':
				print('No switching!')
			else:
				print('Switch type error!')
				sys.exit()

		# do a check for the end time
		if etime_dt < stime_dt:
			date2 = datetime.strptime(date,'%Y-%m-%d')+timedelta(days=1)
			date2 = datetime.strftime(date2,'%Y-%m-%d')
		else:
			date2 = date

		# total date time
		try:
			sdate_dt = datetime.strptime(date+stime,'%Y-%m-%d%H:%M:%S')
		except ValueError:
			sdate_dt = datetime.strptime(date+stime,'%Y-%m-%d%H:%M')
		try:
			edate_dt = datetime.strptime(date2+etime,'%Y-%m-%d%H:%M:%S')
		except ValueError:
			edate_dt = datetime.strptime(date2+etime,'%Y-%m-%d%H:%M')

		sdate_dt = sdate_dt + timedelta(hours=offset)
		edate_dt = edate_dt + timedelta(hours=offset)

		# Account for beam switching (imaging only)
		if 'S' in src_obstype:

			# Randomise beams if there is a ? in the specification
			if '?' in src_obstype:
				rndbm = [0]
				bm = 0
				for jj in range(0,int(numscans)):
					print('Finding beams...')

					# Note: this cannot handle 37 beams yet...
					while bm in rndbm:
						bm = int(rand()*36)
					rndbm.append(bm)
			elif src_obstype == 'Ss':
				rndbm = rndbm_subset
				swtime = swtime_subset
				bttime = bttime_subset
			elif src_obstype == 'S*':
				rndbm = rndbm_set	
				swtime = swtime_set
				bttime = bttime_set				
			else:
				rndbm = rndbm_set	
				swtime = swtime_set
				bttime = bttime_set
			nbeams = len(rndbm)
			print('Selected beams: ',rndbm)
			print('Number of beams: ',nbeams)	

			obslength = (etime_dt-stime_dt).seconds/3600.
			step = swtime/60.
			numscans = obslength / (step + bttime/60.)# + 1 # edge effect
			print(step, step*60.,numscans,obslength)
			
			# Write the observations to a file:
			for k in range(0,int(numscans)+1):

				# Need to divide by num beams to decide which beam it will do?
				print(k)
				print(k % len(rndbm))
				chosenbeam = rndbm[k % len(rndbm)]
				print('chosen beam:',chosenbeam)

				# Update the scan
				#scan = str(d['scan'][i])[:-2]+ '%.3d' % (j+1)
				scan = '000000' + '%.3d' % (j+1)
				print(scan)

				beamname = 'B0%.2d' % chosenbeam
				src = '%s_%s' % (d['source'][i],chosenbeam)

				print(beamname,src)

				# Calculate the new position for that given beam
				# Note: using compound beam positions
				ra_new,dec_new = calc_pos_compound(ra,dec,beamname)
				print(ra_new,dec_new)

				# New execute time
				print(old_date,old_etime)

				# Recalculate the start and end time
				if k == 0:

					try:
						exectime = datetime.strptime(date+stime,'%Y-%m-%d%H:%M:%S')#+timedelta(seconds=15)
					except ValueError:
						exectime = datetime.strptime(date+stime,'%Y-%m-%d%H:%M')

					exectime = exectime + timedelta(hours=offset)

					sdate = exectime
					edate = exectime + timedelta(minutes=step*60.)
				else:
					try:
						exectime = datetime.strptime(old_date+old_etime,'%Y-%m-%d%H:%M:%S')#+timedelta(seconds=15)
					except ValueError:
						exectime = datetime.strptime(old_date+old_etime,'%Y-%m-%d%H:%M')
					sdate = exectime + timedelta(minutes=bttime)
					edate = exectime + timedelta(minutes=step*60.+bttime)

				if edate > edate_dt or k > nbeams-1:
					continue

				# Write sources to file
				if system_offset == True:
					refbeam = str(chosenbeam)
					scannum = writesource_imaging(i,j,scan,sdate.date(),sdate.time(),edate.date(),edate.time(),src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,args.telescopes)		
				else:
					scannum = writesource_imaging(i,j,scan,sdate.date(),sdate.time(),edate.date(),edate.time(),src,ra_new,dec_new,old_date,old_etime,ints,weightpatt,refbeam,renum,out,args.telescopes)		

				# update parameters
				old_etime = str(edate.time())
				old_date = str(edate.date())
				j+=1

		# Standard observation otherwise
		else:	

			# Write sources to file
			if args.mode == 'imaging':
				scannum = writesource_imaging(i,j,scan,str(sdate_dt.date()),str(sdate_dt.time()),str(edate_dt.date()),str(edate_dt.time()),src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,args.telescopes)
				j+=1
			elif args.mode == 'SC4':
				scannum = writesource_sc4(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,args.telescopes,duration)		
				scannum2 = writesource_sc4_cluster(i,j,scan,date,stime,date2,etime,src,d['ra'][i],d['dec'][i],old_date,old_etime,ints,weightpatt,refbeam,renum,out2,observing_mode,args.telescopes,start_beam,end_beam,pulsar,duration)		
			elif args.mode == 'SC1':
				scannum = writesource_sc1(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,args.telescopes,sband,eband,parfile,duration)		
				
				j+=1

		# update parameters
		old_etime = etime
		old_date = date2

	# Make the resultting file executable
	os.system('chmod oug+x %s' % outname)

if __name__ == '__main__':
    main()

