import unittest
import sys
import difflib

class TestATDBParsets(unittest.TestCase):

	def test_main_imagingtests(self):

		import atdb_parsets
		sys.argv[1:] = ('-f test_tmp/test_20190408_v2.csv -m imaging -t 23456789ABCD').split()
		atdb_parsets.main()

		with open('test_tmp/test_20190408_v2_imaging.sh') as infile1:
			gen_file = [x for x in infile1.readlines() if x[0] != '#']
		
		with open('test_tmp/test_20190408_v2_imaging_reference.sh') as infile2:
			ref_file = [x for x in infile2.readlines() if x[0] != '#']

		self.assertEqual(gen_file,ref_file)