#Script to parse telemetry and control TX (NTX and Dongle) 

from datetime import * 
from time import *
import serial
import subprocess
import os
import datetime
import re
import ftplib
from config import *

def getData(filename="telem.txt"):
	data = open('telem.txt')
	lastData = data.readlines()
	lastData = lastData[-1]
	return lastData

def checksum(sentence):
    """ Remove any newlines """
    sentence = sentence[2:]
    if re.search("\n$", sentence):
        sentence = sentence[:-1]

    nmeadata,cksum = re.split('\*', sentence)

    calc_cksum = 0 
    for s in nmeadata:
        calc_cksum ^= ord(s)

    """ Return the nmeadata, the checksum from
        sentence, and the calculated checksum
    """
#    return nmeadata,'0x'+cksum,hex(calc_cksum)
    return hex(calc_cksum)


def typecasting(crc):
    msb = hex(crc >> 8)
    lsb = hex(crc & 0x00FF)
    return lsb + msb

def prepareStr(lastLine,Err="OK"):
	lastLine = lastLine + Err + "*" + "\n"
	crcCode = str(checksum(lastLine))
	crcCode = crcCode[2:]
	sendLine = lastLine[:-1] + crcCode + "\n"

	return sendLine

#def NTXSend(data,baud=50,par=0,stop=1,size=8,ssdv=0):
#Sends datastring to Serial port TX (NTX)
##If SSDV is 1 then we are going to send a SSDV image using 150 baud
#	parset = serial.PARITY_NONE
#	stopset = serial.STOPBITS_ONE
#	sizeset = serial.EIGHTBITS
#
#	if par == 1:
#		parset = serial.PARITY_ODD
#	elif par == 2:
#		parset = serial.PARITY_EVEN
#	if stop == 2:
#		stopset = serial.STOPBITS_TWO
#	if size == 7:
#		sizeset = serial.SEVENBITS
#
# configure the serial connections (the parameters differs on the device you are connecting to)
#	if ssdv == 1:
#	
#		ser = serial.Serial(
#			port='/dev/ttyAMA0',
#			baudrate = 600,
#			parity = serial.PARITY_NONE,
#			stopbits = serial.STOPBITS_ONE,
#			bytesize = serial.EIGHTBITS
#			)
#		sdv = subprocess.Popen('ssdv -e imgs/ssdv.jpg > /dev/ttyAMA0', stdout=subprocess.PIPE, shell=True)
#		ser.flush()
#		if sdv.stdout.readlines() == "Resource busy":
#			print "Error TTY resource reported busy"
#		ser.flush()
#		ser.close()
#
#	else:
#		ser = serial.Serial(
#			port='/dev/ttyAMA0',
#			baudrate = baud,
#			parity = parset,
#			stopbits = stopset,
#			bytesize = sizeset
#			)
#		ser.flush()	
#		ser.open()
#	#	ser.isOpen()
#		ser.write(data)
#		sleep(3)
#		ser.flush()
#		ser.close() #Close and release socket for GPS to communicate to it. 

def writeData(first,CallSign,Seq,GPS,DHTT,DHTH,inTemp,abPress,bAlt,CPUInfo,Err,tosend):
	newStamp = "=== BEGINNING OF LOG: "+ strftime("%d %b %Y - %H:%M:%S", gmtime()) + " ===\n"
	corrGPS = GPS.split(',')
	print corrGPS[2]
        #Change UNIX gps time to human-readable time..
	print corrGPS[2]
	if corrGPS[2] == None or "0":
		print "COMPUTER TIME!"
		gpTime = strftime("%H:%M:%S", gmtime())
	else:
		print "GPSTIME"
		gpTime = datetime.datetime(*strptime(corrGPS[2], "%H:%M:%S")[0:6]).strftime("%H:%M:%S")
	
	corrGPS[0] = format(float(corrGPS[0]), '.4f')
	corrGPS[1] = format(float(corrGPS[1]), '.4f')
	CPUInfo[1] = format(float(CPUInfo[1]), '.2f')
	txstream = CallSign + "," + Seq + "," + corrGPS[0] + "," + corrGPS[1] + "," + gpTime + "," + corrGPS[3] + "," + corrGPS[4] + "," + corrGPS[5] + "," + corrGPS[6] + "," + corrGPS[7] + "," + corrGPS[8] + "," + bAlt + "," +  DHTT + "," + DHTH + "," + inTemp + "," + abPress + "," + CPUInfo[0] + "," + CPUInfo[1] + "," + CPUInfo[2] + "," + CPUInfo[3] + "," + Err
	print txstream
	target = open("outtt.txt", 'a')
	if first == 1:
		target.write(newStamp)
	else:	
		target.write(txstream)
		target.write("\n")
		target.close()

	return txstream	


def modem(toggle=1):
	if toggle == 1:
		POn = subprocess.Popen("./hub.sh" ' 4' ' 1', stdout=subprocess.PIPE, shell=True)	
		PAct = subprocess.Popen("sudo dhclient eth1", stdout=subprocess.PIPE, shell=True)
	else:
		POn = subprocess.Popen("./hub.sh" ' 4' ' 0', stdout=subprocess.PIPE, shell=True)

def lastPicFile():
	with open('imagelog.txt','r') as f:
        	last = None
        	for line in (line for line in f if line.rstrip('\n')):
                        last = line.rstrip('\n')
			last = last + ".jpg"
	return last
	
def check_ping():
	hostname = "google.com"
	response = os.system("ping -c 1 " + hostname)
	# and then check the response...
	if response == 0:
		pingstatus = 1
	else:	
		pingstatus = 0
	
	return pingstatus

def webUp(stat):
	myFTP = ftplib.FTP(ftp_server, ftp_username, ftp_password)

	if stat == "A":
	#Ascend mode: Just a pic every 30 seconds
		lastfile = lastPicFile()
		lastfile2 = "imgs/" + lastfile
		fname = open(lastfile2, 'rb')
		tfile = open('outtt.txt', 'rb')
		myFTP.storbinary('STOR %s' % lastfile, fname)
		myFTP.storbinary('STOR %s' % 'outtt.txt', tfile)
		fname.close()

	if stat == "D":
		telemfile = open('outtt.txt', 'rb')
		myFTP.storbinary('STOR %s' % 'outtt.txt', telemfile)

	#Descent mod: Send telemetry log + all pics/videos as long as connection is maintained
		myPath = r'imgs'
		uploadThis(myPath)



def uploadThis(path):
        myFTP = ftplib.FTP(server, username, password)
	files = os.listdir(path)
        os.chdir(path)
        for f in files:
        	if os.path.join(path + r'/{}'.format(f)):
        		fh = open(f, 'rb')
        		myFTP.storbinary('STOR %s' % f, fh) 
        		fh.close()
        	elif os.path.join(path + r'/{}'.format(f)):
        		myFTP.mkd(f)
        		myFTP.cwd(f)
        		uploadThis(path + r'/{}'.format(f))
	myFTP.cwd('..')
	os.chdir('..')

def ttystat(toggle=1):
	statfile = open('ntx.txt','w')
	
	if toggle == 1:
		statfile.write("1")
	else:
		statfile.write("0")
	statfile.close()


	
