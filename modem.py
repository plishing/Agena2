#!/usr/bin/python


import telem as telem
import time as time
time.sleep(15)
m_active = 1
connection = 0
initTime = time.time() + 60
count = 1
telem.modem(1)
time.sleep(30)
while True:      
	mode = None
        #We need to know if probe is in ascend or descend mode
        with open('outtt.txt','r') as f:
                last = None
                for line in (line for line in f if line.rstrip('\n')):
                        last = line.split(',')
        vspeed = float(last[6])
	alt = float(last[5])
	delta = time.time() - initTime
        while  delta < 120:
		delta = time.time() - initTime
		time.sleep(2)
	while alt < 1500 and delta < 1200 and vspeed > 0:
       		print "Ascending!"
	 #Probe is in ascend mode
        #Modem should already be active because of startup so no need to redo this..
	        telem.webUp("A") #SEND TELEM STRING + OCCASSIONAL IMG
                mode = "A" 
		time.sleep(20)
        while alt < 1000 and vspeed < 0 and delta > 1500:
		print "Descending"
		if m_active == 0:
			telem.modem(1)
			m_active = 1
		time.sleep(30) #Especially at altitude, the modem requires time to get a usable connection so wait..
		while connection == 0:
			if telem.check_ping() == 1:
				connection = 1
			time.sleep(5)
                telem.webUp("D")
		mode = "D" 
        
	print "Nothing to do - waiting for clue" 
	time.sleep(10)
