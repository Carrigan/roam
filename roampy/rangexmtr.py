import serial
import time
import sys

ser = serial.Serial('COM5', 115200)
print "SERIAL OPEN. CTRL+C TO EXIT"

while(True):
	try:
		ser.write("A")
		time.sleep(1)
	except:
		print "DONE"
		ser.close()
		sys.exit(0)
