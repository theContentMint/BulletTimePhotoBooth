"""
Module containing the logger class
"""

import serial
import datetime
import time
from threading import Thread
import csv

class logger:
    """
    This class logs the times trigged by an arduino to a file 
    in csv format. The arduino must send a trigger "T" via serial.
    Inputs:
        Optional: 
            serial_port: number or string used by serial.Serial()
                otherwise searches the first three ports
            filename:    default 'biker_time.csv
    """
    def __init__(self, serial_port = None, filename = 'biker_time.csv'):
        if serial_port == None:
            for i in range(10):
                try:
                    s = serial.Serial(i)
                    self.serial_port = i
                    s.close()
                    break
                except serial.serialutil.SerialException:
                    pass
            if i == 9:
                raise serial.serialutil.SerialException('Could not find ports for 1-10')
        else:         
            self.serial_port = serial_port
        self.filename = filename
        self.running = False
        
    def start(self):
        """
        Starts a thread that opens the file and stream to serial, it
        writes a datetime code for every T recieved (excluding the fist two
        reads)
        """
        # create serial connection
        self.s = serial.Serial(self.serial_port, 9600, timeout = 0)
        # clear the first couple
        self.s.read(self.s.inWaiting())
        # open file for writing and create csv writter
        self.file = open(self.filename, 'wb')
        self.writer = csv.writer(self.file)
        # start thread
        self.running = True
        self.thread = Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()
    
    def run(self):
        """
        The function that the thread runs called by start.
        """
        while self.running:
            try:
                buffer = self.s.read(self.s.inWaiting())
                for c in buffer:
                    if c == 'T':
                        self.writer.writerow([str(datetime.datetime.now())])
                        print datetime.datetime.now()
            except Exception as e:
                print e
                self.s.close()
                self.file.close()
                break
            time.sleep(0.05)
                
    def stop(self):
        """
        Stops thread and closes serial connection and file.
        """
        self.running = False
        time.sleep(0.5)
        self.s.close()
        self.file.close()
        return not self.thread.is_alive()



            
    
