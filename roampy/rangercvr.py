from xbee import ZigBee
import serial
import time
import sys
import math

comport = "COM3"

# From excel: fit = a*ln(x)+b
fit_a = 10.322
fit_b = 30.382

ser = serial.Serial('COM3', 115200)
print "Listening on " + comport + "..."

def rssi_to_distance(rssi, a, b):
        return math.pow(math.e, ((rssi - b)/a))

class moving_average(object):
        def __init__(self, size):
                self.samples = [0] * size

        def sample(self, data):
                self.samples.append(data)
                del self.samples[0]

        @property
        def average(self):
                avg = 0
                for sample in self.samples:
                        avg += sample
                avg = float(avg) / len(self.samples)
                return avg

ma = moving_average(10)

def receive_packet(data):
	if(data['id'] == 'rx'):
		xbee.at(frame='A', command="DB")
	else:
		ma.sample(ord(data['parameter']))
		ma_dist = rssi_to_distance(ma.average, fit_a, fit_b)
		print "Packet received:\tMA_RSSI {0}\tMA_DIST {1}".format(ma.average, ma_dist)        
                

xbee = ZigBee(ser, callback=receive_packet)

while(1):
	try:
		time.sleep(.01)
	except:
		print "DONE"
		xbee.halt()
		ser.close()
		sys.exit(0)
