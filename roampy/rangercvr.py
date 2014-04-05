from xbee import ZigBee
import serial
import time
import sys
import math
import os.path

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

samples_rcvd = 0

def receive_packet(data):
        if(data['id'] == 'rx'):
                xbee.at(frame='A', command="DB")
        else:
                try:
                        global samples_rcvd
                        ma.sample(ord(data['parameter']))
                        ma_dist = rssi_to_distance(ma.average, fit_a, fit_b)
                        print "Packet received:\tMA_RSSI {0}\tMA_DIST {1}".format(ma.average, ma_dist)
                        samples_rcvd += 1
                except:
                        pass
                
print "Starting serial..."

while(1):
        try:
                sample_count = int(raw_input("Samples: ")) 
                ma = moving_average(sample_count)
                global samples_rcvd
                samples_rcvd = 0

                ser.flushInput()
                xbee = ZigBee(ser, callback=receive_packet)
                
                while(samples_rcvd < sample_count):
                        time.sleep(.01)

                xbee.halt()
                filename = "samples/sample{0}.csv"
                file_ext = 0
                while(True):
                        csvfile = filename.format(file_ext)
                        if not os.path.isfile(filename.format(file_ext)):
                                print "Saving samples as " + csvfile
                                csv = open(csvfile, "w")

                                for sample in ma.samples:
                                        print sample
                                        csv.write( str(sample) + "\n" )
                                csv.close()
                                break
                        file_ext += 1
        except:
                ser.close()
                sys.exit(0)
