#!/usr/bin/python

#Functions file to call different sensors

from datetime import timedelta
import sys
import os
import subprocess
from time import *
import time
import threading
import picamera
import dhtreader

#BMP180 sensor. icaddr = i2c bus address, mode = resulution mode, qnh is air pressure at sealevel. 
#Returns an array with the following values in order: temp, press, sealevel press, altitude.

def bmp ( icaddr, mode, qnh) :
	if mode > 3:
		print "Mode does not exist"
		return;

	press = qnh*100;

	import logging
	#logging.basicConfig(level=logging.DEBUG)
	import Adafruit_BMP.BMP085 as BMP085
	
	bmp_sensor = BMP085.BMP085(mode=mode, busnum=icaddr)
	alt = round(bmp_sensor.read_altitude(press), 2);
	ReturnList = [ bmp_sensor.read_temperature(),bmp_sensor.read_pressure(),bmp_sensor.read_sealevel_pressure(),alt ];

	return;

def dht(t=22,pin=5):
        dhtreader.init()
        DHTSensData = dhtreader.read(t,pin)
        return DHTSensData 


def DHT( ):
	count = 0
#DHT sensors readout for 2302 sensor on pin #5
	DHT = subprocess.Popen("./DHT.sh", stdout=subprocess.PIPE, shell=True)
	wait_timeout(DHT, 3)
	DHTOut = DHT.stdout.readlines()
       	
	while len(DHTOut) == 0:
		DHT = subprocess.Popen("./DHT.sh", stdout=subprocess.PIPE, shell=True)
		wait_timeout(DHT, 3)
		DHTOut = DHT.stdout.readlines()
		count = count + 1
		if count > 3:
			DHTSens = "SensFail" #was DHTSens[2])
			return DHTSens
			break
	DHTSens = DHTOut #.rstrip()
	if DHTSens[0].rstrip() ==  None:
		DHTSens[2] = "TFail"
	elif DHTSens[1].rstrip() == None:
		DHTSens[2] = "HFail"
	elif DHTSens[0].rstrip() == None and DHTSens[1].rstrip() == None:
		DHTsens[2] = "SensFail"
	return DHTSens

def wait_timeout(proc, seconds):
    """Wait for a process to finish, or raise exception after timeout"""
    start = time.time()
    end = start + seconds
    interval = min(seconds / 1000.0, .25)

    while True:
        result = proc.poll()
        if result is not None:
            return result
        if time.time() >= end:
            continue #raise RuntimeError("Process timed out")
        time.sleep(interval)


import time
import math

## Import Libraries that let python talk to I2C devices
from smbus import SMBus
reg = 0x77

class MS5611:
    """Driver for reading temperature/pressure MS5611 Pressure Sensor."""

    def __init__(self, bus = 1, i2c = reg, elevation = 0):
        """Initialize the Driver.
        Default bus is 1.  If you have a Rev 1 RPi then you will need to use bus 0.
        A bus object can also be passed in if you are sharing it among other modules
        
        Arguments (All optional):
        bus -- 0, 1, or a bus object
        i2c -- I2C address
        elevation -- Elevation in meters"""
        if(bus == 0 or bus == 1):
                self.bus = SMBus(bus)
        else:
                self.bus = bus
                self.i2c = i2c
                self.elevation = elevation


    def setElevation(self, elevation):
        self.elevation = elevation


    def setElevationFt(self, elevation):
        self.elevation = elevation / 3.2808


    def setI2c(self, i2c):
        self.i2c = i2c


    def read(self):
	try:
        	## Get raw pressure
	       	self.bus.write_byte(reg, 0x48)
	except (IOError,RuntimeError, TypeError, NameError):
		return 1 #Sensor unreachable - exit process and let main know
        time.sleep(0.05)

        D1 = self.bus.read_i2c_block_data(reg, 0x00)
        D1 = D1[0] * 65536 + D1[1] * 256.0 + D1[2]
        time.sleep(0.05)

        ## Get raw temperature
        self.bus.write_byte(reg, 0x56)
        time.sleep(0.05)
        D2 = self.bus.read_i2c_block_data(reg, 0x00)
        D2 = D2[0] * 65536 + D2[1] * 256.0 + D2[2]
        time.sleep(0.05)


        ## Read Constants from Sensor
        if hasattr(self, 'C1'):
            C1 = self.C1
        else:
            C1 = self.bus.read_i2c_block_data(reg, 0xA2) #Pressure Sensitivity
            C1 = C1[0] * 256.0 + C1[1]
            self.C1 = C1
            time.sleep(0.05)

        if hasattr(self, 'C2'):
            C2 = self.C2
        else:
            C2 = self.bus.read_i2c_block_data(reg, 0xA4) #Pressure Offset
            C2 = C2[0] * 256.0 + C2[1]
            self.C2 = C2
            time.sleep(0.05)

        if hasattr(self, 'C3'):
            C3 = self.C3
        else:
            C3 = self.bus.read_i2c_block_data(reg, 0xA6) #Temperature coefficient of pressure sensitivity
            C3 = C3[0] * 256.0 + C3[1]
            self.C3 = C3
            time.sleep(0.05)

        if hasattr(self, 'C4'):
            C4 = self.C4
        else:
            C4 = self.bus.read_i2c_block_data(reg, 0xA8) #Temperature coefficient of pressure offset
            C4 = C4[0] * 256.0 + C4[1]
            self.C4 = C4
            time.sleep(0.05)
        if hasattr(self, 'C5'):
            C5 = self.C5
        else:
            C5 = self.bus.read_i2c_block_data(reg, 0xAA) #Reference temperature
            C5 = C5[0] * 256.0 + C5[1]
            self.C5 = C5
            time.sleep(0.05)
        if hasattr(self, 'C6'):
            C6 = self.C6
        else:
            C6 = self.bus.read_i2c_block_data(reg, 0xAC) #Temperature coefficient of the temperature
            C6 = C6[0] * 256.0 + C6[1]
            self.C6 = C6
            time.sleep(0.05)


        ## These are the calculations provided in the datasheet for the sensor.
        dT = D2 - C5 * 2**8
        TEMP = 2000 + dT * C6 / 2**23

        ## Set Values to class to be used elsewhere
        self.tempC = TEMP/100.0
        self.tempF = TEMP/100.0 * 9.0/5 + 32
        self.tempK = TEMP/100.0 + 273.15

        ## These calculations are all used to produce the final pressure value
        OFF = C2 * 2**16 + (C4 * dT) / 2**7
        SENS = C1 * 2**15 + (C3 * dT) / 2**8
        P = (D1 * SENS / 2**21 - OFF) / 2**15
        self.pressure = P/100.0

        ## Calculate an offset for the pressure.  This is required so that the readings are correct.
        ##   Equation can be found here: http://en.wikipedia.org/wiki/Barometric_formula
        altOffset = math.exp( (-9.80665 * 0.0289644 * self.elevation) / (8.31432 * self.tempK) )
        self.pressureAdj = ( P/altOffset ) / 100.0

    def getTempC(self):
	try:
        ## Get raw pressure
		self.bus.write_byte(reg, 0x48)
		return self.tempC
	except (IOError,AttributeError,RuntimeError, TypeError, NameError):
		self.tempC = 0
       	
    def getTempF(self):
        return self.tempF

    def getPressure(self):
	try:
       		return self.pressure
	except (IOError,AttributeError,RuntimeError, TypeError, NameError):
                self.pressure = 0 

    def getPressureAdj(self):
       try:
		return self.pressureAdj
       except (IOError,AttributeError,RuntimeError, TypeError, NameError):
		self.pressureAdj = 0

    def getBus(self):
        return self.bus

    def printResults(self):
        print ("Temperature:", round(self.tempC, 2), "C")
        print ("            ", round(self.tempF, 2), "F")

        print ("Pressure Absolute:", round(self.pressure, 2), "hPa")
        print ("         Adjusted:", round(self.pressureAdj, 2), "hPa")
        print ("         Adjusted:", round(self.convert2In(self.pressureAdj), 2), "in")

    def convert2In(self, pressure):
        return pressure * 0.0295301


def baroAlt(temp, abpress, qnh): #self, abpress, adjpress, temp, elevation,qnh):
	gasConst = -8.31432
	tempLapse = -0.0065
	try:
	    temp = float(temp)
	except ValueError:
    		temp = 0
	temp = float(temp) + 273 #Kelvin please
	abpress = float(abpress)
	qnh = float(qnh)
	barAlt = (temp / -0.0065) * ((abpress/qnh)**((-8.31432*-0.0065)/(9.80665*0.0289644)) - 1)

#If altitude is above 11.0000 m we need to use a slightly different formula due to changing properties of the atmosphere
	if int(barAlt) > 11000:
		barAlt = barAlt + ((8.31432 * 231 * math.log(122.00/988.00)) / -9.80665 * 0.028964)

	return int(barAlt)

def PiCam(filename=0, mode=0, location=0, quality=100, amount=1, duration=10, pause=3, w=2592, h=1944, log=1):
#filename = If no name is given, Ill assign the current UNIX epoch date
#Mode = photo (0) or video (1)
#Flip = No flip (0), Horizontal (1) or Vertical (2)
#Amount = unlimited (0)
#Pause = seconds between images if amount is > 1
	flip = 2
	fileGiven = 0
	qual = quality

	if filename == 0 or amount == 0 or amount > 1:
		tstamp = int(time.time())
		fstamp = str(tstamp)
		filename = [fstamp,"jpg"]
		filename = '.'.join(filename)
		filename = 'imgs/'+filename
	else:
		filename = "imgs/"+filename
		fileGiven = 1
	
	with picamera.PiCamera() as cam:
		cam.resolution = (w,h)
		if flip == 1:
			cam.hflip = True
		if flip == 2:
			cam.vflip = True
		if mode == 0:
			#cam.quality = quality
			#if amount > 1 or amount < 0:
			if amount == 0:
				amount = 50000
			i = 0
			while i < amount:
				cam.capture(filename, format='jpeg',quality=qual)
				sleep(pause)
				i = i + 1
		elif mode == 1:
			cam.start_recording(filename)
			sleep(duration)
			cam.stop_recording()
	if mode == 0:
		fopen = open('imagelog.txt', 'a')
	else:
		fopen = open('videolog.txt', 'a')

	if fileGiven == 1:
		fopen.write(filename[5:-4] + "\n")
	else:
		fopen.write(fstamp + "\n")
	fopen.close()
	return filename
			
def SSDV_cam( ):
	PiCam("ssdv.jpg",quality=35,w=416,h=304)

def CamStamp( ):
	tstamp = int(time.time())
	tstamp = str(tstamp)
	tstamp = [tstamp,"jpg"]
	camfile = '.'.join(tstamp)
	return camfile

def CPU( ): #Reads out RPI CPU temp and voltage and removes unnecessary stuff
	cpu = subprocess.Popen("./cpu.sh", stdout=subprocess.PIPE, shell=True)
        cpuInfo = cpu.stdout.readlines()
	cpuInfo[0] = cpuInfo[0].lstrip('temp=')
	cpuInfo[0] = cpuInfo[0].rstrip()
	cpuInfo[0] = cpuInfo[0].rstrip("'C")

        cpuInfo[1] = cpuInfo[1].lstrip('-e volt=')
        cpuInfo[1] = cpuInfo[1].rstrip()
        cpuInfo[1] = cpuInfo[1].rstrip("V")
	
	with open('/proc/uptime', 'r') as f:
		uptaim = float(f.readline().split()[0])
		m, s = divmod(uptaim, 60)
		h, m = divmod(m, 60)
		uptaimm =  "%d:%02d:%02d" % (h, m, s)

	with open('/proc/loadavg', 'r') as g:
		loot = g.readline()[:4]
	
	retCPU = [cpuInfo[0],cpuInfo[1],uptaimm,loot]
	return retCPU

def tstamp( ):
	f = open('tstamp.txt','w')
	stmp = time.time()
	f.write(str(stmp))
	f.close()


def convCoord(lat,lon): #Converts minute coords to decimals coords.
	uselat = lat.split('.')
	ladsec = "."+uselat[1][2:]
	ladsec = float(ladsec)*60
	ladmin = float(uselat[1][:2]) * 60

	latotdec = (ladmin + ladsec) / 3600
	declat = float(uselat[0]) + latotdec

        uselon = lon.split('.')
        lodsec = "."+uselon[1][2:]
        lodsec = float(lodsec)*60
        lodmin = float(uselon[1][:2]) * 60

        lototdec = (lodmin + lodsec) / 3600
	if float(uselon[0]) < 0:
		declon = float(uselon[0]) - lototdec
	else:
	        declon = float(uselon[0]) + lototdec
	
	coords = [declat,declon]

	return coords

