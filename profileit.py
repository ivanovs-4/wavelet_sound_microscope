#!/usr/bin/env python
import pstats
import sys
from subprocess import check_call


stat_file = '/tmp/profile_data'

check_call(['python', '-m', 'cProfile', '-o', stat_file] + sys.argv[1:])

p = pstats.Stats(stat_file)

p.sort_stats('cumulative').print_stats(8)
