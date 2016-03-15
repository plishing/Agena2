#!/usr/bin/python

import os
import time
from subprocess import check_output

def get_pid(name):

	return check_output(["pidof",name])



time.sleep(25)


while True:
	f = open('tstamp.txt','r')
	tstamp = f.readline()
	nowtime = time.time()
	tdiff = nowtime - float(tstamp)
	f.close()

	with open('imagelog.txt') as f:
		last = None
		for last in (line for line in f if line.rstrip('\n')):
			pass
	last = last.rstrip()
	f.close()
		
	if tdiff > 240:
		if not last == "ssdv":
			print "Limit!"
			os.system("sudo reboot")
	time.sleep(20)
