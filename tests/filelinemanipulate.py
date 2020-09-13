#!/usr/bin/env python3
# Manipulate each file line
# HanishKVC, 2020
#


import sys
import random


f = open(sys.argv[1])

for l in f:
	if l[-1] == '\n':
		l = l[:-1]
	aRand1 = random.randint(0,26)
	aRand2 = random.randint(0,26)
	iCellAddrs = (aRand1%4)
	if iCellAddrs == 0:
		print("={}".format(l))
		continue
	lLen = len(l)
	iOffset = int(lLen/iCellAddrs)
	lOut = ""
	for i in range(iCellAddrs):
		lOut += (l[iOffset*i:iOffset*(i+1)] + " {}{}{} ".format(chr(ord('A')+aRand1), chr(ord('A')+aRand2), aRand1))
	lOut += l[iOffset*(i+1):]
	print("={}".format(lOut))

f.close()

