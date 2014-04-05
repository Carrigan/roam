from xbee import ZigBee
import serial
import time
import sys
import math
import os.path
import Queue
import threading

# From excel: fit = a*ln(x)+b
fit_a = 10.322
fit_b = 30.382

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

MODE_SOUND = "K"
MODE_VIBRATE = "L"
MODE_SOUND_AND_VIBRATE = "J"
MODE_MUTE = "M"

STATE_DISCONNECTED = 0
STATE_CONNECTED = 1
STATE_WAITING_FOR_LINK = 2

states = {STATE_DISCONNECTED: "DISCONNECTED",
          STATE_CONNECTED: "CONNECTED",
          STATE_WAITING_FOR_LINK: "WAITING FOR LINK",
          }

class roam_app(object):
        def __init__(self, size, com):
                self.comport = com
                self.ma = moving_average(size)
                self.dest = "\x00\x13\xa2\x00\x40\x9b\xb8\x48"
                self.ser = None
                self.xbee = None
                self.queue = []
                self.status = STATE_DISCONNECTED
                self.connect()

        @property
        def state(self):
                return states[self.status]

        def __exit__(self):
                self.disconnect()

        def connect(self):
                if not self.xbee:
                        self.ser = serial.Serial(self.comport, 115200)
                        self.xbee = ZigBee(self.ser, callback=self.receive_handler)
                        print "App started on " + self.comport + "..."

        def disconnect(self):
                if self.xbee:
                        self.scanning = False
                        
                        self.xbee.halt()
                        self.ser.close()
                        self.xbee = None
                        self.ser = None
                        print "App ended."

        def send(self, data):
                if not self.xbee:
                        self.connect()
                self.xbee.send('tx', dest_addr_long = self.dest, dest_addr = "\xFF\xFE", data = data)

        def link(self):
                self.send('$')
                self.status = STATE_WAITING_FOR_LINK

        def process(self):
                for entry in self.queue:
                        self.state_handle(entry)
                self.queue = []

        def state_handle(self, packet):
                if self.status == STATE_WAITING_FOR_LINK:
                        if packet['id'] == 'tx_status':
                                status = packet['deliver_status']
                                if status == '\x00':
                                        self.status = STATE_CONNECTED
                                else:
                                        self.status = STATE_DISCONNECTED

        def receive_handler(self, data):
                self.queue.append(data)

        def scan(self):
                self.scanning = True
                self.scan_handler()

        def scan_end(self):
                self.scanning = False

        def scan_handler(self):
                if not self.scanning:
                        return
                
                self.process()
                
                if self.status == STATE_DISCONNECTED:
                        self.link()
                        
                if self.status == STATE_CONNECTED:
                        print "Link successful!"
                else:
                        print "No device found. Waiting..."
                        threading.Timer(1, self.scan_handler).start()                
                
                

roam = roam_app(10, 'COM3')

