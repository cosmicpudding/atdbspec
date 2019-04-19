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
			default='input/ARTS_Survey_20190420-20190423.csv',
			help='Specify the input file location (default: %(default)s)')	
	parser.add_argument('-m', '--mode',
			default='SC4',
			help='Specify whether mode is imaging/SC1/SC4 (default: %(default)s)')
	parser.add_argument('-t', '--telescopes',
			default='2345679',
			help='Specify which telescopes to include (default: %(default)s)')
	parser.add_argument('-c', '--cluster_mode',
		default='ATDB',
		help='Specify which ARTS cluster mode, either standard/ATDB (default: %(default)s)')
	parser.add_argument('-u', '--upload',
		default=True,
		action='store_true',
		help='Specify whether to automatically upload to wcudata1 (default: %(default)s)')
	parser.add_argument('-p', '--parset_only',
		default=False,
		action='store_true',
		help='Specify whether to only make a parset and not submit it (default: %(default)s)')
	parser.add_argument('-v', '--verification',
		default=False,
		help='Specify whether to send a verification/test observation for specified mode (default: %(default)s)')

	# Parse the arguments above
	args = parser.parse_args()

	# Weight pattern dictionary
	weightdict = {'compound': 'square_39p1',
				  'XXelement': 'central_element_beams_x',
				  'YYelement': 'central_element_beams_y',
				  'XXelement40': 'central_element_beams_x',
				  'YYelement40': 'central_element_beams_y',
				  'hybrid': 'hybridXX_20180928_8bit'}


	# hack for ARTS cluster mode
	start_tid = 49
	start_tnum = 0

	# beam switching time (only relevant for imaging)
	#swtime_set = 15 # min
	swtime_set = 5 # min
	bttime_set = 2 # min
	rndbm_set = list(np.arange(0,40)) # list(np.arange(0,40))

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

	# parsetonly string
	if args.parset_only:
		parsetonly = '--parset_only'
	else:
		parsetonly = ''

	################################################

	# Read file (either tab or comma separated)
	try:
		d = ascii.read(fname,delimiter=',',guess=False)
	except:
		d = ascii.read(fname,delimiter='\t',guess=True)

	print(list(d.keys())) 

	# Start the file
	outname = '%s_%s.sh' % (fname.split('.')[0],args.mode)
	out = open(outname,'w')
	out.write('#!/bin/bash\n# Script to create commands for Apertif ATDB\n# Automatic generation script by V.A. Moss 04/10/2018\n# Last updated by V.A. Moss 11/02/2019\n# Schedule generated: %s UTC\n\n' % datetime.utcnow())
	out.flush()

	if args.mode == 'SC4':

		# Start the file
		outname2 = '%s_%s_cluster.sh' % (fname.split('.')[0],args.mode)
		out2 = open(outname2,'w')
		out2.write('#!/bin/bash\n# Script to create commands for ARTS SC4 cluster\n# Automatic generation script by V.A. Moss 07/12/2018\n# Last updated by V.A. Moss 11/02/2019\n\nsource $HOME/ARTS-obs/setup_env.sh\n\n')
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

			# Added by LO
			duration = int((etime_dt - stime_dt).total_seconds())
			 # nasty duration hack to avoid crazy values
			while duration > 86400:
				duration -= 86400
			if duration < 0:
				duration = 86400 + duration


		elif 'duration' in d.keys():
			etime_dt = stime_dt + timedelta(seconds=float(d['duration'][i]))
			etime = str(etime_dt.time())
			duration = d['duration'][i]

		# do a check for the end time
		if etime_dt <= stime_dt:
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

		# Try to find central frequency
		if 'centfreq' in d.keys():
			centfreq = int(d['centfreq'][i])
		else:
			centfreq = 1400

		# Parse the Position coordinates (accounting now for ha)
		hadec = ''
		try: 
			ra = float(d['ra'][i])
			dec = float(d['dec'][i])
		except:
			if 'ha' in d.keys() and d['ha'][i] != '-':
				print('Detecting an HADEC observation!')
				try:
					ra = float(d['ha'][i])
					dec = float(d['dec'][i])
				except:
					ra = float(ra2dec(d['ha'][i]))
					dec = float(dec2dec(d['dec'][i]))
				hadec = '--parset_location=/opt/apertif/share/parsets/parset_start_observation_driftscan_atdb.template '

			elif d['ra'][i] == '-':
				print('No coordinates specified... maybe a pointing observation?')

			elif 'deg' in d['ra'][i]:
				ra = float(d['ra'][i].split('deg')[0])
				dec = float(d['dec'][i].split('deg')[0])

			# With :
			elif ':' in d['ra'][i]:
				ra = ra2dec(d['ra'][i])
				dec = dec2dec(d['dec'][i])

			# With HMS
			elif 'h' in d['ra'][i]: 
				ra = ra2dec(d['ra'][i].replace('h',':').replace('m',':').replace('s',''))
				dec = dec2dec(d['dec'][i].replace('d',':').replace('m',':').replace('s',''))

			else:
				print('Error parsing coordinates!')
				sys.exit()	

		# Imaging specific things
		if args.mode == 'imaging':
			src_obstype = d['type'][i]

			if 'freqmode' in d.keys():
				if d['freqmode'][i] == 300:
					extra = '--end_band=24'
				elif d['freqmode'][i] == 200:
					extra = ''
			else:
				extra = '--end_band=24'
			#lo = d['lo'][i]
			#sub1 = d['sub1'][i]
			#field = d['intent'][i].upper()

			# Go into pointing mode
			if src_obstype == 'P':

				print('Pointing observation identified!')

				# Send the relevant data to the pointing function
				observing_mode = 'imaging_pointing'
				make_pointing(sdate_dt,edate_dt,ints,weightpatt,out,args.telescopes,observing_mode,parsetonly,hadec)

				# We don't want to proceed with the code once the pointing is done!
				break

			elif src_obstype == 'O':
				print('Operations tests mode identified!')

				# Determine if offset beam is chosen or random
				if d['beam'] != 0:
					offbeam = d['beam'][i]
				else:
					offbeam = randint(1,40)

				beamname = 'B0%.2d' % offbeam
				beams = [0,offbeam]#,0]
				ra_new1,dec_new1 = calc_pos_compound(ra,dec,beamname)
				ra_new2,dec_new2 = calc_pos(ra,dec,beamname)
				ras = [ra,ra,[ra_new1,ra_new2]]
				decs = [dec,dec,[dec_new1,dec_new2]]
				names = [src,src + '_%i' % offbeam,src + '_%i' % offbeam]
				patterns = [weightdict['compound'],weightdict['XXelement']]#,weightdict['YYelement']]
				generate_tests(names,ras,decs,duration,patterns,beams,sdate_dt,ints,out,args.telescopes,observing_mode,parsetonly,extra,hadec)


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

			elif d['switch_type'][i] == '-' or d['switch_type'][i] == -1.0:
				print('No switching!')
			else:
				print('Switch type error!')
				sys.exit()


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
			swtime = (obslength * 60. - 2 * (nbeams-1)) / nbeams
			step = swtime/60.

			# Step should not have microseconds!
			step = int(step*3600.)/3600.

			# Cal scans
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
					scannum = writesource_imaging(sdate.date(),sdate.time(),edate.date(),edate.time(),src,ra,dec,ints,weightpatt,refbeam,out,args.telescopes,observing_mode,parsetonly,extra,hadec)		
				else:
					scannum = writesource_imaging(sdate.date(),sdate.time(),edate.date(),edate.time(),src,ra_new,dec_new,ints,weightpatt,refbeam,out,args.telescopes,observing_mode,parsetonly,extra,hadec)		

				# update parameters
				old_etime = str(edate.time())
				old_date = str(edate.date())
				j+=1

		# Standard observation otherwise
		elif src_obstype != 'O':	

			# Write sources to file
			if args.mode == 'imaging':
				scannum = writesource_imaging(str(sdate_dt.date()),str(sdate_dt.time()),str(edate_dt.date()),str(edate_dt.time()),src,ra,dec,ints,weightpatt,refbeam,out,args.telescopes,observing_mode,parsetonly,extra,hadec)
				j+=1
			elif args.mode == 'SC4':

				# Reset the tid if needed
				if str(old_date) != str(date) and old_date != None:
					start_tid = 1
					start_tnum = 0

				scannum = writesource_sc4(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,args.telescopes,duration,parsetonly,hadec)		
				scannum2 = writesource_sc4_cluster(i,j,scan,date,stime,date2,etime,src,d['ra'][i],d['dec'][i],old_date,old_etime,ints,weightpatt,refbeam,renum,out2,observing_mode,args.telescopes,start_beam,end_beam,pulsar,duration,args.cluster_mode,start_tid,start_tnum,parsetonly)		
				j+=1
				start_tnum+=1

			elif args.mode == 'SC1':
				scannum = writesource_sc1(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,args.telescopes,sband,eband,parfile,duration,parsetonly)		
				j+=1

		# update parameters
		old_etime = etime
		old_date = date2

	# Close the outfile
	out.close()

	# Make the resultting file executables
	os.system('chmod oug+x %s' % outname)

	# If SC4, then cluster file exists
	if args.mode == 'SC4':
		os.system('chmod oug+x %s' % outname2)

	if args.upload:

		# Upload the file automatically to wcudata1
		# Note: this assumes you have ssh key forwarding activated for apertif user account
		cmd = "rsync -avzP %s apertif@wcudata1.apertif:~/atdb_client/scripts/" % outname
		os.system(cmd)

		#if args.mode == 'SC4':

			# Also do the same for SC4 cluster
			# Note: this assumes you have ssh key forwarding activated for arts user account
			#cmd = 'rsync -avzP %s arts@arts041.apertif:~/observations/scripts/' % outname2
			#os.system(cmd)		


if __name__ == '__main__':
    main()

