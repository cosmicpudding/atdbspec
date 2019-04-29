# APERTIF PARSET GENERATOR ATDB VERSION 1.2 (atdb_parsets.py) - now with ARTS
# Input: source text file
# V.A. Moss 19/12/2018 (vmoss.astro@gmail.com)
__author__ = "V.A. Moss"
__date__ = "$19-dec-2018 17:00:00$"
__version__ = "1.2"

import os
import sys
from modules.beamcalc import *
from astropy.io import ascii
import numpy as np
from argparse import ArgumentParser, RawTextHelpFormatter
from modules.functions import *
from datetime import datetime,timedelta
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
			default='input/sched_190428_LH.csv',
			help='Specify the input file location (default: %(default)s)')	
	parser.add_argument('-m', '--mode',
			default='imaging',
			help='Specify whether mode is imaging/SC1/SC4 (default: %(default)s)')
	parser.add_argument('-t', '--telescopes',
			default='23456789ABCD',
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

	# Initialise the class to store variables
	obs = Observation()
	obs.telescopes = args.telescopes

	# This determines whether to use the system offset for calculating offset beams or not
	system_offset = False # default should be True when we completely trust the system

	# specify the filename
	fname = args.filename

	# offset (if local time is specified in the parset)
	# This should depreciate when we trust the input specification
	offset = 0 # hours

	# parsetonly string
	if args.parset_only:
		parsetonly = '--parset_only'
		obs.parsetonly = '--parset_only'
	else:
		parsetonly = ''
		obs.parsetonly = ''

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

	# Add to the class definition
	obs.out = out

	# Loop through sources
	for i in range(0,len(d)):

		# Get the common parameters for all
		src = d['source'][i]
		obs.src = d['source'][i]

		# Get the pieces of date time
		stime = d['time1'][i]
		sdate = d['date1'][i]

		# Fix times if they aren't the right length
		if len(stime.split(':')[0]) < 2:
			stime = '0'+stime

		# Form the datetime object
		try:
			sdate_dt = datetime.strptime(sdate+stime,'%Y-%m-%d%H:%M:%S')
		except ValueError:
			sdate_dt = datetime.strptime(sdate+stime,'%Y-%m-%d%H:%M')
		sdate_dt = sdate_dt + timedelta(hours=offset)		

		# Endtime or duration
		if 'time2' in d.keys():
			etime = d['time2'][i]
			edate = d['date2'][i]

			# Fix times if they aren't the right length
			if len(etime.split(':')[0]) < 2:
				etime = '0'+etime

			# Form the datetime object
			try:
				edate_dt = datetime.strptime(edate+etime,'%Y-%m-%d%H:%M:%S')
			except ValueError:
				edate_dt = datetime.strptime(edate+etime,'%Y-%m-%d%H:%M')
			edate_dt = edate_dt + timedelta(hours=offset)

			# Check for mistaken date
			if edate_dt <= sdate_dt:
				print('End date is further in the past than start date... adding a day!')
				edate_dt = edate_dt + timedelta(days=1)

			# Added by LO
			duration = int((edate_dt - sdate_dt).total_seconds())

			# nasty duration hack to avoid crazy values (LO)
			# Note from VM: I think this depreciates with proper datetime objects
			# while duration > 86400:
			# 	duration -= 86400
			# if duration < 0:
			# 	duration = 86400 + duration

		elif 'duration' in d.keys():
			edate_dt = sdate_dt + timedelta(seconds=float(d['duration'][i]))
			etime = str(edate_dt.time())
			duration = d['duration'][i]

		# Assign the results to the class
		obs.sdate = sdate_dt
		obs.edate = edate_dt
		obs.duration = duration

		# Define the obs type (not needed really?)
		src_obstype = obs.obstype

		# Observing mode
		if args.mode == 'SC4':
			observing_mode = 'arts_sc4_survey'
			start_beam = d['sbeam'][i]
			end_beam = d['ebeam'][i]
			pulsar = d['pulsar'][i]

			# Class replacements
			obs.obsmode = 'arts_sc4_survey'
			obs.sbeam = d['sbeam'][i]
			obs.ebeam = d['ebeam'][i]
			obs.pulsar = d['pulsar'][i]

		elif args.mode == 'SC1':
			observing_mode = 'arts_sc1_timing'
			sband = d['sband'][i]
			eband = d['eband'][i]
			parfile = d['par'][i]

			# Class replacements
			obs.obsmode = 'arts_sc1_timing'
			obs.sband = d['sband'][i]
			obs.eband = d['eband'][i]
			obs.parfile = d['par'][i]

		else:
			observing_mode = 'imaging'

			# Class replacements
			obs.obsmode = 'imaging'

		# Get ref beam
		try:
			refbeam = d['beam'][i]

			# Class replacements
			obs.refbeam = refbeam
		except:
			refbeam = '0'

			# Class replacements
			obs.refbeam = refbeam

		# Determine the integration factor in seconds
		try:
			ints = d['int'][i]
			obs.intfac = d['int'][i]
		except: 
			if args.mode == 'SC4':
				ints = 30
				obs.intfac = 30
			elif args.mode == 'SC1':
				ints = 20
				obs.intfac = 20

		# Define weight pattern
		try:
			weightpatt = weightdict[d['weight'][i]]
			obs.weightpatt = weightdict[d['weight'][i]]
		except:
			weightpatt = 'square_39p1'
			obs.weightpatt = 'square_39p1'

		# Try to find central frequency
		if 'centfreq' in d.keys():
			centfreq = int(d['centfreq'][i])
			obs.centfreq = int(d['centfreq'][i])
		else:
			centfreq = 1400
			obs.centfreq = 1400

		# Parse the Position coordinates (accounting now for ha)
		# note that HA is stored as RA in the Obs class, even if it is HA
		hadec = ''
		obs.hadec = ''

		try: 
			ra = float(d['ra'][i])
			dec = float(d['dec'][i])
			obs.ratype = 'field_ra'
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
				obs.hadec = '--parset_location=/opt/apertif/share/parsets/parset_start_observation_driftscan_atdb.template '

				obs.ratype = 'field_ha'

			elif d['ra'][i] == '-':
				print('No coordinates specified... maybe a pointing observation?')

			elif 'deg' in d['ra'][i]:
				ra = float(d['ra'][i].split('deg')[0])
				dec = float(d['dec'][i].split('deg')[0])
				obs.ratype = 'field_ra'

			# With :
			elif ':' in d['ra'][i]:
				ra = ra2dec(d['ra'][i])
				dec = dec2dec(d['dec'][i])
				obs.ratype = 'field_ra'

			# With HMS
			elif 'h' in d['ra'][i]: 
				ra = ra2dec(d['ra'][i].replace('h',':').replace('m',':').replace('s',''))
				dec = dec2dec(d['dec'][i].replace('d',':').replace('m',':').replace('s',''))
				obs.ratype = 'field_ra'

			else:
				print('Error parsing coordinates!')
				sys.exit()	

		# Assign these to the class
		obs.ra = ra
		obs.dec = dec
		obs.extra = ''

		# Imaging specific things
		if args.mode == 'imaging':
			src_obstype = d['type'][i]
			obs.obstype = d['type'][i]

			if 'freqmode' in d.keys():
				if d['freqmode'][i] == 300:
					extra = '--end_band=24'
					obs.extra = '--end_band=24'
				elif d['freqmode'][i] == 200:
					extra = ''
					obs.extra = ''
			else:
				extra = '--end_band=24'
				obs.extra = '--end_band=24'

			# Go into pointing mode
			if src_obstype == 'P':

				print('Pointing observation identified!')

				# Send the relevant data to the pointing function
				observing_mode = 'imaging_pointing'
				obs.obsmode = 'imaging_pointing'

				make_pointing(sdate_dt,edate_dt,ints,weightpatt,out,args.telescopes,observing_mode,parsetonly,hadec)
				#make_pointing(obs)

				# We don't want to proceed with the code once the pointing is done!
				break

			elif src_obstype == 'O':
				print('Operations tests mode identified!')

				# Determine if offset beam is chosen or random
				if obs.refbeam != 0:
					offbeam = obs.refbeam
				else:
					offbeam = randint(1,40)

				beamname = 'B0%.2d' % offbeam
				beams = [0,offbeam]#,0]
				ra_new1,dec_new1 = calc_pos_compound(ra,dec,beamname)
				ra_new2,dec_new2 = calc_pos(ra,dec,beamname)
				ras = [ra,ra,[ra_new1,ra_new2]]
				decs = [dec,dec,[dec_new1,dec_new2]]
				names = [src,src + '_%i' % offbeam,src + '_%i' % offbeam]
				patterns = [weightdict['compound'],weightdict['XXelement']]#, weightdict['YYelement']]
				generate_tests(names,ras,decs,patterns,beams,obs)

				break


			# System offset stuff
			if d['switch_type'][i] == 'system':
				system_offset = True
				obs.systemoffset = True

			elif d['switch_type'][i] == 'manual':
				system_offset = False
				obs.systemoffset = False

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
		if src_obstype and 'S' in src_obstype:
			make_beamswitch(obs)

		# Standard observation otherwise
		else:	

			# Write sources to file
			if args.mode == 'imaging':
				scannum = writesource_imaging(obs)

			elif args.mode == 'SC4':

				# # Reset the tid if needed
				# if str(old_edate) != str(date) and old_edate != None:
				# 	start_tid = 1
				# 	start_tnum = 0

				scannum = writesource_sc4(obs)		

			elif args.mode == 'SC1':
				scannum = writesource_sc1(obs)		


	# Close the outfile
	out.close()

	# Make the resultting file executables
	os.system('chmod oug+x %s' % outname)

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

