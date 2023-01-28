#import pysimpledmx
#mydmx = pysimpledmx.DMXConnection(3)

import serial, sys

START_VAL   = 0x7E
END_VAL     = 0xE7

COM_BAUD    = 57600
COM_TIMEOUT = 1
COM_PORT    = 7
DMX_SIZE    = 512

LABELS = {
         'GET_WIDGET_PARAMETERS' :3,  #unused
         'SET_WIDGET_PARAMETERS' :4,  #unused
         'RX_DMX_PACKET'         :5,  #unused
         'TX_DMX_PACKET'         :6,
         'TX_RDM_PACKET_REQUEST' :7,  #unused
         'RX_DMX_ON_CHANGE'      :8,  #unused
      }



dmx_frame = [0] * DMX_SIZE
comport=None
com = serial.Serial(comport, baudrate = COM_BAUD, timeout = COM_TIMEOUT)
dmx_frame[1-1] = 0
packet = [
              START_VAL,
              LABELS['TX_DMX_PACKET'],
              len(dmx_frame) & 0xFF,
              (len(dmx_frame) >> 8) & 0xFF,
    ]
packet += dmx_frame
packet.append(END_VAL)

packet = map(chr, packet)
com.write(''.join(packet))

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