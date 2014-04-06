from xbee import ZigBee
import serial
import time
import sys
import math
import os.path
import Queue
import threading
import datetime
import Tkinter as tk

MODE_SOUND = "K"
MODE_VIBRATE = "L"
MODE_SOUND_AND_VIBRATE = "J"
MODE_MUTE = "M"

STATE_DISCONNECTED = 0
STATE_CONNECTED = 1
STATE_WAITING_FOR_LINK = 2

LENGTH = 1600
HEIGHT = 900

class roam_app(object):
        def __init__(self, size, com):
                self.comport = com
                self.dest = "\x00\x13\xa2\x00\x40\x9b\xb8\x48"
                self.ser = None
                self.xbee = None
                self.queue = []
                self.status = STATE_DISCONNECTED
                self.connect()
                self.pings = []
                self.get_rssi = False

        @property
        def state(self):
                states = {STATE_DISCONNECTED: "DISCONNECTED",
                          STATE_CONNECTED: "CONNECTED",
                          STATE_WAITING_FOR_LINK: "WAITING FOR LINK",
                          }
                return states[self.status]

        def __exit__(self):
                self.disconnect()

        def connect(self):
                if not self.xbee:
                        self.kill = False
                        self.ser = serial.Serial(self.comport, 115200)
                        self.xbee = ZigBee(self.ser, callback=self.receive_handler)
                        print "App started on " + self.comport + "..."

        def disconnect(self):
                if self.xbee:
                        self.ser.close()
                        self.xbee = None
                        self.ser = None
                        print "App ended."

        def send(self, data):
                self.response = False
                if not self.xbee:
                        self.connect()
                self.xbee.send('tx', dest_addr_long = self.dest, dest_addr = "\xFF\xFE", data = data)
                while not self.response:
                        self.process()

        def link(self):
                self.status = STATE_WAITING_FOR_LINK
                self.send('$')
                
        def process(self):
                try:
                        current_op = self.queue[0]
                        del self.queue[0]
                        self.state_handle(current_op)
                except:
                        pass

        def state_handle(self, packet):
                if not packet:
                        return
                
                if packet['id'] == 'tx_status':
                        self.response = True
        
                if self.status == STATE_WAITING_FOR_LINK:
                        if packet['id'] == 'tx_status':
                                status = packet['deliver_status']
                                if status == '\x00':
                                        print "CONNECTED"
                                        self.status = STATE_CONNECTED
                                else:
                                        self.status = STATE_DISCONNECTED
                                return

                if packet['id'] == 'at_response' and packet['frame_id'] == "A":
                        self.rssi = packet['parameter']
                        self.pings.append([datetime.datetime.now(), ord(packet['parameter'])])
                        return

                if packet['id'] == 'rx':
                        if packet['rf_data'][0] == "A":
                                self.get_rssi = True     


        def receive_handler(self, data):
                self.queue.append(data)

        def scan(self):
                while self.status != STATE_CONNECTED:
                        time.sleep(.1)
                        self.link()
                print "Link successful."
                    
        def get_last_rssi(self):
                self.rssi = None
                self.xbee.at(frame_id='A', command="DB")
                while not self.rssi:
                        self.process()
                self.get_rssi = False
                return self.rssi

        def start_alarm(self):
                self.send("N")

        def end_alarm(self):
                self.send("P")

        def alarm_for(self, seconds):
                self.start_alarm()
                threading.Timer(seconds, self.end_alarm).start()

        def clean_pings(self, seconds):
                new_pings = []
                ping_diff = False
                for ping in self.pings:
                        if datetime.datetime.now() < (ping[0] + datetime.timedelta(seconds = seconds)):
                                new_pings.append(ping)
                        else:
                                ping_diff = True
                self.pings = new_pings
                return ping_diff

        def caution_handler(self):
                total_rssi = 0

                if len(self.pings) == 0:
                        return [0, len(self.pings), 0]
                
                for ping in self.pings:
                        total_rssi += ping[1]
                current_avg_rssi = float(total_rssi)/len(self.pings)

                if( len(self.pings) > 20 and current_avg_rssi < 70):
                        return [3, len(self.pings), current_avg_rssi]

                if( len(self.pings) > 10 and current_avg_rssi < 75):
                        return [2, len(self.pings), current_avg_rssi]

                if( len(self.pings) > 8):
                        return [1, len(self.pings), current_avg_rssi]

                return [0, len(self.pings), current_avg_rssi]
                

        def mainloop(self):
                try:
                        master = tk.Tk()
                        can = tk.Canvas(master, width = LENGTH, height = HEIGHT)
                        can.pack()
                        
                        status_count = 0
                        
                        while(self.status == STATE_CONNECTED):
                                self.process()
                                
                                if self.get_rssi:
                                        self.get_last_rssi()
                                        
                                self.clean_pings(4)

                                status_count = status_count + 1
                                if status_count == 50:
                                        status_count = 0

                                        caution_level = self.caution_handler()[0]
                                        print caution_level
                                        
                                        fill = "green"
                                        if caution_level == 2:
                                                fill = "yellow"
                                        if caution_level == 1:
                                                fill = "orange"
                                        if caution_level == 0:
                                                fill = "red"
                                        
                                        can.create_rectangle(0, 0, LENGTH, HEIGHT, fill=fill)
                                        master.update()
                                        
                                if (status_count % 10) == 0:
                                        # Send pings
                                        pass
                                        
                                time.sleep(.01)
                except:
                        print sys.exc_info()[0]
                        print "DONE"
                

roam = roam_app(10, 'COM3')
roam.scan()
roam.mainloop()
roam.disconnect()



