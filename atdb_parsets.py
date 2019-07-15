# APERTIF PARSET GENERATOR ATDB VERSION 1.5 (atdb_parsets.py) - now with ARTS
# Input: source text file
# V.A. Moss 19/12/2018 (vmoss.astro@gmail.com)
__author__ = "V.A. Moss"
__date__ = "$07-jun-2019 17:00:00$"
__version__ = "1.5.1"

import os
import sys
from modules.beamcalc import *
from astropy.io import ascii
import numpy as np
from argparse import ArgumentParser, RawTextHelpFormatter
from modules.functions import *
from modules.drift import calc_drift
from datetime import datetime,timedelta
import time
import getpass

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
		default='input/drift_20190715.csv',
		help='Specify the input file location (default: %(default)s)')	
	parser.add_argument('-m', '--mode',
		default='imaging',
		type = str.lower,
		help='Specify whether mode is imaging/sc1/sc4 (default: %(default)s)')
	parser.add_argument('-t', '--telescopes',
		default='23456789ABCD',
		help='Specify which telescopes to include (default: %(default)s)')
	parser.add_argument('-u', '--upload',
		default=False,
		action='store_true',
		help='Specify whether to automatically upload to wcudata1 (default: %(default)s)')
	parser.add_argument('-p', '--parset_only',
		default=False,
		action='store_true',
		help='Specify whether to only make a parset and not submit it (default: %(default)s)')
	parser.add_argument('-v', '--verification',
		default=False,
		action='store_true',
		help='Specify whether to send a verification/test observation for specified mode (default: %(default)s)')
	parser.add_argument('-a', '--artsmode',
		default='TAB',
		help='Specify which mode to record for ARTS SC4, either incoherent IAB or tied-array TAB (default: %(default)s)')
	parser.add_argument('-n', '--numofobs',
		default=4,
		type = int,
		help='Specify how many verification observations to do, in imaging mode (default: %(default)s)')
	parser.add_argument('-s', '--selobs',
		default=None,
		type = int,
		help='Specify which verification observation to do, in imaging mode (default: %(default)s)')
	parser.add_argument('-c', '--centfreq',
		default=1370,
		type = int,
		help='Specify which central frequency, in imaging mode (default: %(default)s)')


	# Parse the arguments above
	args = parser.parse_args()

	# Weight pattern dictionary
	weightdict = {'compound': 'square_39p1',
				  'XXelement': 'central_element_beams_x',
				  'YYelement': 'central_element_beams_y',
				  'XXelement40': 'central_element_beams_x',
				  'YYelement40': 'central_element_beams_y',
				  'hybrid': 'hybridXX_20180928_8bit',
				  'compound_element_x_subset' : 'compound_element_x_subset'}

	# Expected telescopes
	scopesdict = {'imaging':'23456789ABCD',
				  'sc1': '23456789',
				  'sc4': '23456789'}

	# Check if default doesn't match and warn user
	expected_scopes = scopesdict[args.mode]
	if args.telescopes != expected_scopes:
		print('WARNING!!!\nExpected telescopes: %s\nSpecified telescopes: %s\n' % (expected_scopes,args.telescopes))

		try: 
			# Python 3
			proceed = input('Do you want to proceed? (y/n) ')
		except:
			# Python 2
			proceed = raw_input('Do you want to proceed? (y/n) ')

		if proceed != 'y':
			print('... exiting!')
			sys.exit()
		else:
			print('Okay, I will continue with the telescopes you specified...')

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
		#parsetonly = '--parset_only'
		obs.parsetonly = '--parset_only '
	else:
		#parsetonly = ''
		obs.parsetonly = ''

	# Consider also ARTS mode
	obs.artsmode = args.artsmode

	# Verification observation
	if args.verification:
		obs.numofobs = args.numofobs
		obs.selobs = args.selobs
		obs.centfreq = args.centfreq
		out,outname = make_verification(obs,args.mode)
		obs.out = out
		obs.outname = outname

	################################################
	
	else:
		# Read file (either tab or comma separated)
		try:
			d = ascii.read(fname,delimiter=',',guess=False)
		except:
			d = ascii.read(fname,delimiter='\t',guess=True)

		print(list(d.keys())) 

		# Start the file
		outname = '%s_%s.sh' % (fname.split('.csv')[0],args.mode)
		out = open(outname,'w')
		out.write(make_header())
		out.flush()

		# Add to the class definition
		obs.out = out
		obs.outname = outname

		# Loop through sources
		for i in range(0,len(d)):

			# Check for delay offset 
			if 'delayoffset' in d.keys():
				obs.delayoffset = '--delay_center_offset=%s ' % d['delayoffset'][i]
			else:
				obs.delayoffset = ''

			# Check for template specification
			if 'template' in d.keys():
				obs.template = '--parset_location=%s ' % d['template'][i]
			else:
				obs.template = ''

			# Get the common parameters for all
			#src = d['source'][i]
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

			elif 'duration' in d.keys() and d['duration'][i] != '-':
				edate_dt = sdate_dt + timedelta(seconds=float(d['duration'][i]))
				etime = str(edate_dt.time())
				duration = d['duration'][i]
			else:
				edate_dt = None
				duration = None

			# Assign the results to the class
			obs.sdate = sdate_dt
			obs.edate = edate_dt
			obs.duration = duration

			# Define the obs type (not needed really?)
			src_obstype = obs.obstype

			# Observing mode
			if args.mode == 'sc4':
				#observing_mode = 'arts_sc4_survey'
				#start_beam = d['sbeam'][i]
				#end_beam = d['ebeam'][i]
				#pulsar = d['pulsar'][i]

				# Class replacements
				obs.obsmode = 'arts_sc4_survey'
				obs.sbeam = d['sbeam'][i]
				obs.ebeam = d['ebeam'][i]
				obs.pulsar = d['pulsar'][i]

			elif args.mode == 'sc1':

				obs.skipingest = ''

				if d['mode'][i] == 'timing':
					#observing_mode = 'arts_sc1_timing'
					obs.obsmode = 'arts_sc1_timing'
				elif d['mode'][i] == 'baseband':
					#observing_mode = 'arts_sc1_baseband'
					obs.obsmode = 'arts_sc1_baseband'

					# for arts_sc1_baseband no dataproducts are created for ALTA
					# add the --skip_auto_ingest flag to let baseband observations end in a 'completed' state in ATDB.
					obs.skipingest = '--skip_auto_ingest '

			#	sband = d['sband'][i]
		#		eband = d['eband'][i]
	#			parfile = d['par'][i]

				# Class replacements
				obs.sband = d['sband'][i]
				obs.eband = d['eband'][i]
				obs.parfile = d['par'][i]

			else:
				#observing_mode = 'imaging'

				# Class replacements
				obs.obsmode = 'imaging'

			# Get ref beam
			try:
				#refbeam = d['beam'][i]

				# Class replacements
				obs.refbeam = d['beam'][i]
			except:
				#refbeam = '0'

				# Class replacements
				obs.refbeam = '0'

			# Determine the integration factor in seconds
			try:
				#ints = d['int'][i]
				obs.intfac = d['int'][i]
			except: 
				if args.mode == 'sc4':
					#ints = 30
					obs.intfac = 30
				elif args.mode == 'sc1':
					#ints = 20
					obs.intfac = 20
					obs.template = '/opt/apertif/share/parsets/parset_start_observation_atdb_arts_sc1.template'

			# Define weight pattern
			try:
				#weightpatt = weightdict[d['weight'][i]]
				obs.weightpatt = weightdict[d['weight'][i]]
			except:
				#weightpatt = 'square_39p1'
				obs.weightpatt = 'square_39p1'

			# Try to find central frequency
			if 'centfreq' in d.keys():
				#centfreq = int(d['centfreq'][i])
				obs.centfreq = int(d['centfreq'][i])
			else:
				#centfreq = 1400
				obs.centfreq = 1370 # new default

			# Parse the Position coordinates (accounting now for ha)
			# note that HA is stored as RA in the Obs class, even if it is HA
			#hadec = ''
			obs.hadec = ''

			try: 
				if 'ha' in d.keys() and d['ha'][i] != '-':

					print('Detecting an HADEC observation!')
					ra = float(d['ha'][i])
					dec = float(d['dec'][i])

					obs.ratype = 'field_ha'

				else:
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
					#hadec = '--parset_location=/opt/apertif/share/parsets/parset_start_observation_driftscan_atdb.template '
					#obs.hadec = '--parset_location=/opt/apertif/share/parsets/parset_start_observation_driftscan_atdb.template '

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
				#src_obstype = d['type'][i]
				obs.obstype = d['type'][i]

				if 'freqmode' in d.keys():
					if d['freqmode'][i] == 300:
						#extra = '--end_band=24'
						obs.extra = '--end_band=24 '
					elif d['freqmode'][i] == 200:
						#extra = ''
						obs.extra = ''
				else:
					#extra = '--end_band=24'
					obs.extra = '--end_band=24 '

				# Go into pointing mode
				if obs.obstype == 'P':

					print('Pointing observation identified!')

					# Send the relevant data to the pointing function
					#observing_mode = 'imaging_pointing'
					obs.obsmode = 'imaging_pointing'

					#make_pointing(sdate_dt,edate_dt,ints,weightpatt,out,args.telescopes,observing_mode,parsetonly,hadec)
					make_pointing(obs)

					# We don't want to proceed with the code once the pointing is done!
					break

				elif obs.obstype == 'O':
					print('Operations tests mode identified!')

					# Determine if offset beam is chosen or random
					if obs.refbeam != 0:
						offbeam = obs.refbeam
					else:
						offbeam = randint(1,40)

					beamname = 'B0%.2d' % offbeam
					beams = [0,offbeam]#,0]
					ra_new1,dec_new1 = calc_pos_compound(obs.ra,obs.dec,beamname)
					ra_new2,dec_new2 = calc_pos(ra,dec,beamname)
					ras = [obs.ra,obs.ra,[ra_new1,ra_new2]]
					decs = [obs.dec,obs.dec,[dec_new1,dec_new2]]
					names = [obs.src,obs.src + '_%i' % offbeam,obs.src + '_%i' % offbeam]
					patterns = [weightdict['compound'],weightdict['XXelement']]#,weightdict['XXelement']]#, weightdict['YYelement']]
					generate_tests(names,ras,decs,patterns,beams,obs)

					break

				elif obs.obstype == 'D' or obs.obstype == 'D*':
					print('Drift mode identified!')

					# Single drift through a row
					if obs.obstype == 'D':
						try:
							n_drift = d['n_drift'][i]
						except:
							n_drift = 1

						ha,duration = calc_drift((obs.ra,obs.dec),obs.sdate,n_drift)
						print(ra2dec(ha),duration)

						# Deal with ref beam 					
						beamname = 'B0%.2d' % obs.refbeam
						ra_new1,dec_new1 = calc_pos_compound(obs.ra,obs.dec,beamname)
						offset = '%+.2d' % ((obs.dec - dec_new1)*60.)

						# Change the variables
						obs.ratype='field_ha'
						obs.ra = ra2dec(ha) # Note: it intentionally goes to ra!
						obs.duration = duration
						obs.edate = sdate_dt + timedelta(seconds=int(duration))
						obs.src = obs.src+'drift'+offset
		
						# Write to the outfile
						writesource_imaging(obs)

					elif obs.obstype == 'D*':
						refbeams = [0,7,14,20,26,32,39]
						nbeams = [1,7,7,6,6,6,7]
						currdate_dt = obs.sdate
						truename = obs.src
						truera = obs.ra
						truedec = obs.dec

						for ii in range(0,len(refbeams)):
							
							obs.refbeam = refbeams[ii]
							n_drift = nbeams[ii]
							obs.ra = truera
							obs.dec = truedec

							#print(obs.ra,obs.dec)
							ha,duration = calc_drift((truera,truedec),currdate_dt,n_drift)
							print(ra2dec(ha),duration)

							# Change the variables
							obs.ratype='field_ha'
							obs.ra = ra2dec(ha) # Note: it intentionally goes to ra!
							obs.duration = duration
							obs.sdate = currdate_dt
							obs.edate = currdate_dt + timedelta(seconds=int(duration))

							# Deal with ref beam 
							beamname = 'B0%.2d' % obs.refbeam
							ra_new1,dec_new1 = calc_pos_compound(obs.ra,obs.dec,beamname)
							offset = '%+.2d' % ((obs.dec - dec_new1)*60.)
							obs.src = truename+'drift'+offset

							# Write to the outfile
							writesource_imaging(obs)

							# update the time
							currdate_dt = obs.edate + timedelta(seconds=120)

					continue


				# System offset stuff
				if d['switch_type'][i] == 'system':
					#system_offset = True
					obs.systemoffset = True

				elif d['switch_type'][i] == 'manual':
					#system_offset = False
					obs.systemoffset = False

					if 'S' not in src_obstype:
						beamname = 'B0%.2d' % refbeam
						if d['weight'][i] == 'XXelement' or d['weight'][i] == 'YYelement':
							ra_new,dec_new = calc_pos(obs.ra,obs.dec,beamname)
						elif d['weight'][i] == 'compound':
							ra_new,dec_new = calc_pos_compound(obs.ra,obs.dec,beamname)
						else:
							print (weightpatt)
						#print(beamname,ra_new,dec_new,ra,dec)
						obs.ra,obs.dec = ra_new,dec_new
						obs.refbeam = '0'

				elif d['switch_type'][i] == '-' or d['switch_type'][i] == -1.0:
					print('No switching!')
				else:
					print('Switch type error!')
					sys.exit()

			# Account for beam switching (imaging only)
			if obs.obstype and 'S' in obs.obstype:
				make_beamswitch(obs)

			# Standard observation otherwise
			else:	

				# Write sources to file
				if args.mode == 'imaging':
					writesource_imaging(obs)

				elif args.mode == 'sc4':

					# # Reset the tid if needed
					# if str(old_edate) != str(date) and old_edate != None:
					# 	start_tid = 1
					# 	start_tnum = 0

					writesource_sc4(obs)		

				elif args.mode == 'sc1':
					writesource_sc1(obs)		


	# Close the outfile
	out.close()

	# Make the resultting file executables
	os.system('chmod oug+x %s' % obs.outname)

	if args.upload:

		# Upload the file automatically to wcudata1
		# Note: this assumes you have ssh key forwarding activated for apertif user account
		cmd = "rsync -avzP %s apertif@wcudata1.apertif:~/atdb_client/scripts/" % obs.outname
		os.system(cmd)

		#if args.mode == 'SC4':

			# Also do the same for SC4 cluster
			# Note: this assumes you have ssh key forwarding activated for arts user account
			#cmd = 'rsync -avzP %s arts@arts041.apertif:~/observations/scripts/' % outname2
			#os.system(cmd)		


if __name__ == '__main__':
    main()

