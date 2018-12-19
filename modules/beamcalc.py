# Visualisation of APERTIF MS: beam position calculations for compound beams
# V.A. Moss (vmoss.astro@gmail.com)
__author__ = "V.A. Moss"
__date__ = "$03-may-2018 00:00:00$"
__version__ = "0.1"

import os
import sys
from numpy import *
from math import *
from pylab import *
from astropy.io import ascii


beam_elements = 'B000 = 27X,B001 = 3X,B002 = 5X,B003 = 7X,B004 = 13X,B005 = 15X,B006 = 17X,B007 = 19X,B008 = 12X,B009 = 14X,B010 = 16X,B011 = 18X,B012 = 20X,B013 = 24X,B014 = 26X,B015 = 28X,B016 = 30X,B017 = 23X,B018 = 25X,B019 = 29X,B020 = 31X,B021 = 35X,B022 = 37X,B023 = 39X,B024 = 41X,B025 = 34X,B026 = 36X,B027 = 38X,B028 = 40X,B029 = 42X,B030 = 46X,B031 = 48X,B032 = 50X,B033 = 52X,B034 = 47X,B035 = 49X,B036 = 51X'.split(',')
beam_dict = dict((k.strip(), v.strip()) for k,v in (item.split('=') for item in beam_elements))

def calc_pos(src_ra,src_dec,beam):

	print(beam[-2:])
	bm_nr = int(beam[-2:])

	# ra offsets (hour angles) -- degrees change based on declination!!
	cbm_dHA = np.array([0.00,1.50,1.50,1.50,1.05,1.05,1.05,1.05,0.75,0.75,0.75,0.75,0.75,0.375,0.375,0.375,0.375,0.00,0.00,0.00,0.00,-0.375,-0.375,-0.375,-0.375,-0.75,-0.75,-0.75,-0.75,-0.75,-1.05,-1.05,-1.05,-1.05,-1.50,-1.50,-1.50])

	# dec offsets (degrees)
	cbm_dDec = np.array([0.00,0.75,0.00,-0.75,1.05,0.3,-0.3,-1.05,1.50,0.75,0.00,-0.75,-1.50,1.05,0.3,-0.3,-1.05,1.50,0.75,-0.75,-1.50,1.05,0.3,-0.3,-1.05,1.50,0.75,0.00,-0.75,-1.50,1.05,0.3,-0.3,-1.05,0.75,0.00,-0.75])

	# supposedly this undoes the phase sign flip but don't think it works
	# Modify this: not offsets, so signs should be reversed 25/01/17
	# Reverse again thanks to system changes... 02/11/18
	bm_dHA = 1.0 * cbm_dHA[bm_nr]
	bm_dDec = 1.0 * cbm_dDec[bm_nr]  # Remove the minus sign, it seems to have crept back in... 01/06/18

	# Add the offsets
	phc_ra = src_ra + bm_dHA / np.cos(np.deg2rad(src_dec))
	phc_dec = src_dec + bm_dDec

	return phc_ra,phc_dec

def calc_offset(beam):

	bm_nr = int(beam[-2:])

	# ra offsets (hour angles) -- degrees change based on declination!!
	cbm_dHA = np.array([0.00,1.50,1.50,1.50,1.05,1.05,1.05,1.05,0.75,0.75,0.75,0.75,0.75,0.375,0.375,0.375,0.375,0.00,0.00,0.00,0.00,-0.375,-0.375,-0.375,-0.375,-0.75,-0.75,-0.75,-0.75,-0.75,-1.05,-1.05,-1.05,-1.05,-1.50,-1.50,-1.50])

	# dec offsets (degrees)
	cbm_dDec = np.array([0.00,0.75,0.00,-0.75,1.05,0.3,-0.3,-1.05,1.50,0.75,0.00,-0.75,-1.50,1.05,0.3,-0.3,-1.05,1.50,0.75,-0.75,-1.50,1.05,0.3,-0.3,-1.05,1.50,0.75,0.00,-0.75,-1.50,1.05,0.3,-0.3,-1.05,0.75,0.00,-0.75])

	# supposedly this undoes the phase sign flip but don't think it works
	# Modify this: not offsets, so signs should be reversed 25/01/17
	# Reverse again thanks to system changes... 02/11/18
	bm_dHA = 1.0 * cbm_dHA[bm_nr]
	bm_dDec = 1.0 *cbm_dDec[bm_nr] # Remove the minus sign, it seems to have crept back in... 01/06/17

	return bm_dHA,bm_dDec

def calc_offset_eq(src_ra,src_dec,beam):

	bm_nr = int(beam[-2:])

	# ra offsets (hour angles) -- degrees change based on declination!!
	cbm_dHA = np.array([0.00,1.50,1.50,1.50,1.05,1.05,1.05,1.05,0.75,0.75,0.75,0.75,0.75,0.375,0.375,0.375,0.375,0.00,0.00,0.00,0.00,-0.375,-0.375,-0.375,-0.375,-0.75,-0.75,-0.75,-0.75,-0.75,-1.05,-1.05,-1.05,-1.05,-1.50,-1.50,-1.50])

	# dec offsets (degrees)
	cbm_dDec = np.array([0.00,0.75,0.00,-0.75,1.05,0.3,-0.3,-1.05,1.50,0.75,0.00,-0.75,-1.50,1.05,0.3,-0.3,-1.05,1.50,0.75,-0.75,-1.50,1.05,0.3,-0.3,-1.05,1.50,0.75,0.00,-0.75,-1.50,1.05,0.3,-0.3,-1.05,0.75,0.00,-0.75])

	# supposedly this undoes the phase sign flip but don't think it works
	# Modify this: not offsets, so signs should be reversed 25/01/17
	bm_dHA = -1.0 * cbm_dHA[bm_nr]
	bm_dDec = -1.0 *cbm_dDec[bm_nr]

	return  (bm_dHA / np.cos(np.deg2rad(src_dec))),bm_dDec

def calc_pos_compound(src_ra,src_dec,beam):

	# Read in beams 
	d = ascii.read('modules/pattern39+1.txt')

	print(beam[-2:])
	bm_nr = int(beam[-2:])

	# ra offsets (hour angles) -- degrees change based on declination!!
	cbm_dHA = d['dHA']
	# dec offsets (degrees)
	cbm_dDec = d['dDec']

	# supposedly this undoes the phase sign flip but don't think it works
	# Modify this: not offsets, so signs should be reversed 25/01/17
	bm_dHA = 1.0 * cbm_dHA[bm_nr] # Changing minus sign to deal with system issues 14/12/2018
	bm_dDec = -1.0 * cbm_dDec[bm_nr] 

	# Add the offsets
	phc_ra = src_ra + bm_dHA / np.cos(np.deg2rad(src_dec))
	phc_dec = src_dec + bm_dDec

	return phc_ra,phc_dec

