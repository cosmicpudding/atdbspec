# APERTIF PARSET GENERATOR ATDB VERSION 1.2 (atdb_parsets.py) - now with ARTS
# Input: source text file
# V.A. Moss 19/12/2018 (vmoss.astro@gmail.com)

__author__ = "V.A. Moss"
__date__ = "$19-dec-2018 17:00:00$"
__version__ = "1.2"

from datetime import datetime,timedelta


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

def writesource_imaging(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,telescopes):

	# Write to file (not plus=)
	out.write("""atdb_service --field_name=%s --field_ra=%.6f --field_dec=%.6f --field_beam=%s --starttime='%s %s' --endtime='%s %s' --pattern=%s --integration_factor=%s --telescopes=%s --central_frequency=1400 --data_dir=/data/apertif/ --operation=specification --atdb_host=prod \n\n""" % (src,ra,dec,refbeam,date,stime,date2,etime,weightpatt,ints,telescopes))
	out.flush()

	return scan

###################################################################
# Write source: SC4

def writesource_sc4(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,telescopes,duration):


	# Write to file (not plus=)
	out.write("""atdb_service --field_name=%s --field_ra=%.6f --field_dec=%.6f --field_beam=%s --starttime='%s %s' --duration=%s --pattern=%s --integration_factor=%s --observing_mode=%s --telescopes=%s --central_frequency=1400 --data_dir=/data2/output/ --science_mode=IAB --operation=specification --atdb_host=prod --skip_auto_ingest\n\n""" % (src,ra,dec,refbeam,date,stime,duration,weightpatt,ints,observing_mode,telescopes))
	out.flush()

	return scan

###################################################################
# Write source: SC1

def writesource_sc1(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,telescopes,sband,eband,parfile,duration):

	# Write to file (not plus=)
	out.write("""atdb_service --field_name=%s --field_ra=%.6f --field_dec=%.6f --field_beam=%s --starttime='%s %s' --duration=%s --pattern=%s --integration_factor=%s --observing_mode=%s --telescopes=%s --par_file_name=%s  --start_band=%s --end_band=%s --science_mode=TAB --number_of_bins=1024 --central_frequency=1400 --ndps=1 --irods_coll=arts_main/arts_sc1 --data_dir=/data/01/Timing --parset_location=/opt/apertif/share/parsets/parset_start_observation_atdb_arts_sc1.template --operation=specification --atdb_host=prod \n\n""" % (src,ra,dec,refbeam,date,stime,duration,weightpatt,ints,observing_mode,telescopes,parfile,sband,eband))
	out.flush()

	return scan


###################################################################
# Write source: SC4

def writesource_sc4_cluster(i,j,scan,date,stime,date2,etime,src,ra,dec,old_date,old_etime,ints,weightpatt,refbeam,renum,out,observing_mode,telescopes,sbeam,ebeam,pulsar,duration,cluster_mode,start_tid):

	# Cluster start time
	sdate_dt = datetime.strptime(str(date)+str(stime),'%Y-%m-%d%H:%M:%S')
	stime_cluster = (sdate_dt - timedelta(minutes=5)).time()

	# Write to file (not plus=)
	if pulsar.lower() == 'true':
		cmd = ("""sleepuntil_utc %s %s
start_obs --mac --ingest_to_archive --obs_mode survey --proctrigger --source %s --ra %s --dec %s --tstart "%sT%s" --duration %s --sbeam %s --ebeam %s --pulsar""" % (date,stime_cluster,src,ra,dec,date,stime,duration,sbeam,ebeam))
	else:
		cmd = ("""sleepuntil_utc %s %s
start_obs --mac --ingest_to_archive --obs_mode survey --proctrigger --source %s --ra %s --dec %s --tstart "%sT%s" --duration %s --sbeam %s --ebeam %s""" % (date,stime_cluster,src,ra,dec,date,stime,duration,sbeam,ebeam))

	# Cluster mode hack
	if cluster_mode == 'ATDB':
		cmd = cmd + ' --atdb --taskid %i\n\n' % (start_tid + j) 
	else:
		cmd = cmd + '\n\n'

	# Write out at the end
	out.write(cmd)
	out.flush()


	return scan

