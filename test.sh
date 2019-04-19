#!/bin/bash
rm -rf test_tmp
mkdir test_tmp
cp test/fixtures/* test_tmp/
python -m unittest discover