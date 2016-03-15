#CONFIG FILE

dummy = 0 #Use dummy telem data (for testing)
gdummy = 0 #Use dummy GPS data (for testing)

CallSign = "$$AGENA2" #Probe callsign. Always include $$ if you want to comply to UK-HAS telemetry requirements
modemsw = 1 #Is 3G modem on or off at system start? (0 = if no modem present)
seq = 0 #Telem string sequence number start point
logFile = "outtt.txt" #Logfile name
QNH = 1026.00 #QNH of current location. If none given then software will calculate it.
elev = 120 #Elevation of launch location in meters above sea level (MSL)

#FTP data require to upload telemetry to your server if you have a 3G dongle installed.
ftp_server = ''
ftp_username = ''
ftp_password = ''
