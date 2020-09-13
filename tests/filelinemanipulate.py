#!/usr/bin/env python3
# Manipulate each file line
# HanishKVC, 2020
#

import sys

f = open(sys.argv[1])

for l in f:
	print("={}".format(l))

f.close()

