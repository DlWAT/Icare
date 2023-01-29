#import pysimpledmx
#mydmx = pysimpledmx.DMXConnection(3)
import serial.tools.list_ports
import serial, sys
import numpy as np
import random
import time
comlist = list(serial.tools.list_ports.comports())
for port_no, description, address in comlist:
    if 'USB' in description:
        MyComPort = port_no
        print(MyComPort)

data= np.zeros([512], np.uint8)
comport=str(port_no)
try :
    com = serial.Serial(comport, baudrate = 250000)
    print('dmx interface connected')
except:
    print('connection failed')
i=0
g=400
r=40
b=0
tempo=5
while i<int(255/tempo):
    
    time.sleep(0.01*tempo)
    max=50
    #r=random.randint(1, max)
    #g=random.randint(1, max)
    #b=random.randint(1, max)

    #b-=tempo
    #r+=tempo
    print(r,g,b)

    data[0] = r
    data[1] = g
    data[2] = b
    data[3] = 20
    data[4] = 150
    #dmx_frame[5] = 0
    start_byte = np.array([0x7E, 0x06, 0x01, 0x02, 0x00], np.uint8)
    end_byte = np.array([0xE7], np.uint8)
    num_of_channels=512

    start_byte[2] = (num_of_channels+1) & 0xFF
    start_byte[3] = ((num_of_channels+1) >> 8) & 0xFF

    data_out = np.concatenate((start_byte, data, end_byte)).tobytes()
    i+=1
    com.write(data_out)

def main_test(mydmx):

    mydmx.setChannel(1, 255) # set DMX channel 1 to full
    mydmx.setChannel(2, 128) # set DMX channel 2 to 128
    mydmx.setChannel(3, 0)   # set DMX channel 3 to 0
    mydmx.render()    # render all of the above changes onto the DMX network

def function1(freq):
    r=3
    g=4
    b=5
    return r,g,b