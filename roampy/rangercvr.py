from xbee import ZigBee
import serial
import time
import sys

ser = serial.Serial('COM3', 115200)

def receive_packet(data):
	if(data['id'] == 'rx'):
		xbee.at(frame='A', command="DB")
	else:
		rssi = ord(data['parameter'])
		print "Packet received:\t{0}".format(rssi)

xbee = ZigBee(ser, callback=receive_packet)

while(1):
	try:
		time.sleep(.01)
	except:
		print "DONE"
		ser.close()
		sys.exit(0)
