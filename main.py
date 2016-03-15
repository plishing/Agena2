#!/usr/bin/python

#Main sequence file
#import gpst
import functions as sensors
from time import *
import telem as telem
from config import *
import subprocess
import os
import serial
import datetime
import re

initTime = int(time()) #Define start time of script. Used to time things like TX, imaging etc and uptime
camStamp = initTime + 10 #Camera will commence 120s after powering script. 
vidStamp = initTime + 20
counter = 0
#telem.modem(1)
#======= END OF CONFIG ===========
elevft = elev * 3.28084
MS = sensors.MS5611(1,0x77,120) #Init MS5611 press sensor with i2C 1, addr: 0x78 and elevation 120m
MS.setElevationFt(elevft)

from geographiclib.geodesic import Geodesic

#=============#
# TX FUNCTION #
#=============#

def NTXSend(data,baud=50,par=0,stop=1,size=8,ssdv=0):
#Sends datastring to Serial port TX (NTX)
#If SSDV is 1 then we are going to send a SSDV image using 150 baud
        parset = serial.PARITY_NONE
        stopset = serial.STOPBITS_ONE
        sizeset = serial.EIGHTBITS

        if par == 1:
                parset = serial.PARITY_ODD
        elif par == 2:
                parset = serial.PARITY_EVEN
        if stop == 2:
                stopset = serial.STOPBITS_TWO
        if size == 7:
                sizeset = serial.SEVENBITS

# configure the serial connections (the parameters differs on the device you are connecting to)
        if ssdv == 1:
    
                ser = serial.Serial(
                        port='/dev/ttyAMA0',
                        baudrate = 600,
                        parity = serial.PARITY_NONE,
                        stopbits = serial.STOPBITS_ONE,
                        bytesize = serial.EIGHTBITS
                        )   
                sdv = subprocess.Popen('ssdv -e imgs/ssdv.jpg > /dev/ttyAMA0', stdout=subprocess.PIPE, shell=True)
                if sdv.stdout.readlines() == "Resource busy":
                        print "Error TTY resource reported busy"
                ser.close()

        else:
                ser = serial.Serial(
                        port='/dev/ttyAMA0',
                        baudrate = baud,
                        parity = parset,
                        stopbits = stopset,
                        bytesize = sizeset
                        )   
                ser.write(data)
                ser.close() #Close and release socket for GPS to communicate to it. 


#===============#
# GPS FUNCTIONS #
#===============#


# byte array for a UBX command to set flight mode
setNav = bytearray.fromhex("B5 62 06 24 24 00 FF FF 06 03 00 00 00 00 10 27 00 00 05 00 FA 00 FA 00 64 00 2C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 16 DC")
# byte array for UBX command to disable automatic NMEA response from GPS
setNMEA_off = bytearray.fromhex("B5 62 06 00 14 00 01 00 00 00 D0 08 00 00 80 25 00 00 07 00 01 00 00 00 00 00 A0 A9")


# function to disable all NMEA sentences
def disable_sentences():

    GPS = serial.Serial('/dev/ttyAMA0', 9600, timeout=1) # open serial to write to GPS

    # Disabling all NMEA sentences 
    GPS.write("$PUBX,40,GLL,0,0,0,0*5C\r\n")
    GPS.write("$PUBX,40,GSA,0,0,0,0*4E\r\n")
    GPS.write("$PUBX,40,RMC,0,0,0,0*47\r\n")
    GPS.write("$PUBX,40,GSV,0,0,0,0*59\r\n")
    GPS.write("$PUBX,40,VTG,0,0,0,0*5E\r\n")
    GPS.write("$PUBX,40,GGA,0,0,0,0*5A\r\n")

    GPS.close() # close serial

###DISABLE SENTS
disable_sentences()


# fucntion to send commands to the GPS 
def sendUBX(MSG, length):
        ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1) # open serial
        ser.flush()
        print "Sending UBX Command: "
        ubxcmds = ""
        for i in range(0, length):
                ser.write(chr(MSG[i])) #write each byte of ubx cmd to serial port
                ubxcmds = ubxcmds + str(MSG[i]) + " " # build up sent message debug output string
        ser.write("\r\n") #send newline to ublox
        ser.flush()
        ser.close()
        print ubxcmds #print debug message
        print "UBX Command Sent..."
        sleep(3)


def cstat( ):
        ntxstat = open('ntx.txt','r')
        sendstat = ntxstat.read()
        sendstat = sendstat.rstrip()
        ntxstat.close()
        return sendstat

def gps(mode="A",dummy=0):
        readprev = open('gpsout.txt','r')
        deta = readprev.read()
        deta = deta.split(',')
        counter = 0
        prevlat = deta[0]
        prevlon = deta[1]
        prevalt = deta[3]
        prevtime = deta[2]
        sendstat = "1"

        if dummy == 1:
                lat = float(prevlat) + .0017
                lon = float(prevlon) - .0002
                time = time.time()
                if mode == "A":
                        alt = float(prevalt) + 23
                else:
                        alt = float(prevalt) - 47
                #vs = 2.4
                sats = "7"
                stat = "OK"
                dt = strptime(time,'%H:%M:%S')
                dtp =strptime(prevtime,'%H:%M:%S')
                dts = datetime.timedelta(hours=dt.tm_hour,minutes=dt.tm_min,seconds=dt.tm_sec).total_seconds()
                dtps = datetime.timedelta(hours=dtp.tm_hour,minutes=dtp.tm_min,seconds=dtp.tm_sec).total_seconds()
                dtime = dts - dtps
                gt = Geodesic.WGS84.Inverse(float(prevlat), float(prevlon), float(lat), float(lon))
                trk = gt['azi1']
                trk = format(float(trk), '.2f')

                dist = gt['s12']
                gspeedms = format((float(dist) / dtime), '.2f')
                gspeedkph = format(float(gspeedms)*3.6, '.2f')

                vs = (float(alt) - float(prevalt)) / dtime
                vs = format(vs, '.1f')
        else:
                #Set GPS to NAV Mode in order to enable functions > 12000 m     
                sendUBX(setNav, len(setNav)) # send command to enable flightmode
                print "sendUBX_ACK function complete"
                #sendUBX(setNMEA_off, len(setNMEA_off)) # turn NMEA sentences off
                ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)
                ser.write("$PUBX,00*33\n") # reuest a PUBX sentence
                line =  ser.readline()
                ser.flush()

                if line.startswith("$PUBX"):
                        ser.write("$PUBX,00*33\n")
                        line = ser.readline()

                        ser.close()
                        line = line.split(',')
			try:
	                        if line[8] == "NF" or None:
       			                print "GPS NONE"
                                	stat = "ACQFAIL"
                                	line[2] = 0
                                	line[4] = 0
                                	line[6] = 0
                                	line[7] = 0
					line[8] = "ACQFAIL"
					line[9] = 0
                        	else:
                                	stat = "OK"
			except:
				stat = "ACQFAIL"
				line = ["0","0","0","0","0","0","0","0","ACQFAIL","0","0","0"]
				pass

			if line[8] == "DR":
				stat = "DEADR"

                        if stat == "ACQFAIL":
                                time = "00:00:00"
                                longitudefull = "0"
                                latitudefull = "0"
                                lat = "0.0000"
                                lon = "0.0000"
                                gt = "0.0"
                                vs = "0.0"
                                alt = "0.0"
                                gspeedkph = "0.0"
                                sats = "0.0"
                                trk = "0.0"
                                dtime = "0"
                                dist = "0"
                        else:
                                print "GPS VALID"
                                time = line[2]
                                time = time[0:6]
                                time = datetime.datetime(*strptime(time, "%H%M%S")[0:6]).strftime("%H:%M:%S")
                                latitude = line[3].replace(".","")
                                latitudefull = latitude[:2] + "." + latitude[2:]
                      	        latitude = format(float(latitudefull), '.4f') 
			        longitude = line[5].replace(".","")
                                longitudefull = longitude[:3] + "." + longitude[3:]
                                longitude  = format(float(longitudefull), '.4f')
                                lon = float(longitude)
                                lat = float(latitude)
                                if line[6] == "W":
                                        longitude = "-"+longitude
                                if line[4] == "S":
                                        latitude = "-"+latitude
				decCoord = sensors.convCoord(str(lat),str(lon))

				lat = decCoord[0]
				lon = decCoord[1]

                                trk = format(float(line[12]), '.0f')
                                sats = line[18]
                                alt = format(float(line[7]),'.1f')

                                dt = strptime(time,'%H:%M:%S')
                                dtp = strptime(prevtime,'%H:%M:%S')
                                dts = datetime.timedelta(hours=dt.tm_hour,minutes=dt.tm_min,seconds=dt.tm_sec).total_seconds()
                                dtps = datetime.timedelta(hours=dtp.tm_hour,minutes=dtp.tm_min,seconds=dtp.tm_sec).total_seconds()
                                dtime = dts - dtps

				gspeedkph = format(float(line[11]), '.1f')	  
                       	        vs = format(float(line[13]), '.1f')
                        print "sats is " + sats
                        write = open('gpsout.txt','w')
                        strGPS = str(lat) + "," +  str(lon) + "," + str(time) + "," + str(alt) + "," + str(vs) + "," + str(gspeedkph) + "," + str(sats) + "," + str(trk) + "," + str(line[8])
                        write.write(strGPS)
                        write.close()

                        prevlon = longitudefull
                        prevlat = latitudefull
                        prevalt = alt
                        prevtime = time
                        sleep(3)
                        counter = counter + 1

#START UP SCRIPT
while True:
	sensors.tstamp()
	while time() - initTime < 3:
		print "Idling"
		delta = time() - initTime - 30
		delta = int(delta)
		NTXSend(baud="150",data="$$AGENA2 - Welcome :) - Script commencing in "+ str(delta) + " seconds. \n")	
		sleep(4)
	Err = ""
	MSErr = 0 #Error state for MS5611 sensor array
	seq = seq + 1
	strSeq = str(seq)


	if dummy == 1: #Do we use dummy data for testing? 
		strDHTT = "22.6"
		strDHTH = "93"
		intTemp = "25.2"
		abPress = "992.12"
		QNH = "1013.25"
		bAlt = "120.2"
		GPSData = "50.923601667,5.977618333,2016-02-26T14:01:48.000Z,47.7,0.0,0.129,12,323.6,OK"
		
		CPUInfo = ["32.6","3.3","34324","1.05"]
		CTemp = str(CPUInfo[0])
		CVin = str(CPUInfo[1])
		CUp = str(int(CPUInfo[2]))
		CLoad = str(CPUInfo[3])
		strCPU = [CTemp,CVin,CUp,CLoad]
		Err = "DUMMY" 	
		
	else:
		DHTRead = sensors.dht(22,5) #DHT22 temp [0] and humidity sensor [1] and Error flags [2].
		DHTRead = sensors.DHT()
	
		strDHTT = str(DHTRead[0].rstrip())
		strDHTH = str(DHTRead[1].rstrip())
		#str(sensors.DHT())
		if MS.read() == 1: #Whoops MS fail detected; Fillout data with usable info. QNH to 1013 (ISA)
			intTemp = "0"
			abPress = "0"
			QNH = "1013"
			bAlt = "SensErr"
			MSErr = 1 #Let errorsystem know.. 
		else:
			intTemp = str(round(MS.getTempC(),1))
			abPress = str(round(MS.getPressure(),2))
			if QNH == None:
				QNH = str(MS.getPressureAdj())
			bAlt = str(round(sensors.baroAlt(DHTRead[0],abPress,QNH),2))
		
		if gdummy == 0:
			gps()
			print "Sleeping"
			sleep(5)
			print "Sleeping complete"
			f = open('gpsout.txt','r') #gpst.py is dumping GPS NMEA lines into this file. We read out the last update and use this for our telemetry.
			GPSData = f.readline()
			GPSData = GPSData.replace('nan','0')
			f.close()
		else:
			GPSData = "50.923601667,5.977618333,2016-02-26T14:01:48.000Z,47.7,0.0,0.129,12,323.6,OK"
			Err = "GDUMMY"
		print GPSData #test
		
		
		if QNH == 0 or QNH == None: #If for whatever reason the sea level pressure is 0 or invalid, we will use ISA pressure settings. This have cause a BAlt inaccuracy of up to +/- 350m. 
		       	QNH = 1013.25
		print bAlt
		#Get some RPI health info
	
		CPUInfo = sensors.CPU() #[0] = temp [1] = Vin CPU [2] = uptime in seconds [3] = current systen load
		CTemp = str(CPUInfo[0])
		CVin = float(CPUInfo[1])
		CVin = str(round(CVin,1))
		CUp = str(CPUInfo[2])
		CLoad = str(CPUInfo[3])
	
		strCPU = [CTemp,CVin,CUp,CLoad]
		print CUp
	if counter == 0:
		first = 1
	else:
		first = 0
	
	DataStream = telem.writeData(first,CallSign,strSeq,GPSData,strDHTT,strDHTH,intTemp,abPress,bAlt,strCPU,Err,tosend="1") #Sorts out data stream and saves it to telemetry logs. 
	useStream = DataStream.split(',')

	#Populate Err string with any prevailing error 
        if CTemp < 0:
        	Err = Err + "CPUCRIT"
        if float(CTemp) > 85: 
        	Err = Err + "CPUTEMP"
	if MSErr == 1:
       		Err = Err + "MSENSIO"
        if useStream[10] == "ACQFAIL":
                Err = Err + "NAVERR"
	if useStream[10] == "DEADR":
		Err = Err + "NAVWARN"
	if Err == "" or None:
		Err = "OK"

		
	#Prepare string first before sending. Attach XOR checksum and then pass it the good string on to NTX TX hardware. 
	telemData = telem.prepareStr(DataStream,Err)
	sleep(3)
	NTXSend(baud=150,data=telemData)
	print telemData
	sleep(3)
	
	if useStream[10] == "ACQFAIL" or None: #If GPS is inop, we will use the barometric altitude for altitude information. 
		planalt = bAlt
	else:
		planalt = useStream[5]

	#Swithc on/off modem
	if planalt > "1500" and modemsw == 1:  
		telem.modem(0)
		modemsw == 0
	
	if planalt < "1500" and modemsw == 0:
		print "PLANALT < 1500"
		telem.modem(1)
		modemsw == 1
	
	#cam - make photo every 30 seconds. 
	if time() - camStamp > 30:
	#Make pic
		sensors.PiCam()
		camStamp = time()


	#SSDV timing
	if time() - vidStamp > 600:
		NTXSend(baud=150,data="SSDV ARRIVING SWITCH TO 600 BAUD\n")
		sleep(5)
		sensors.tstamp()
		sensors.SSDV_cam()
		sleep(5)
		NTXSend(data="",ssdv=1)
		sleep(5)
		vidStamp = time()
	counter = counter + 1	
	sleep(5) #5 seconds pause to let the RTTY TX finish before restarting loop. 
