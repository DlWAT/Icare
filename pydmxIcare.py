from gettext import npgettext
import serial.tools.list_ports
import serial, sys
import numpy as np
import warnings


class DMX_Icare(object):

    def __init__(self) -> None:
        self.start_byte = np.array([0x7E, 0x06, 0x01, 0x02, 0x00], np.uint8)
        self.end_byte = np.array([0xE7], np.uint8)
        num_of_channels=512
        self.start_byte[2] = (num_of_channels+1) & 0xFF
        self.start_byte[3] = ((num_of_channels+1) >> 8) & 0xFF
        self.data= np.zeros([512], np.uint8)
        

    def connection(self):
        comlist = list(serial.tools.list_ports.comports())
        if not comlist:
            warnings.warn("No COM port available")
        try :    
            for port_no, description, address in comlist:
                if 'USB' in description:
                    comport=str(port_no)
            self.com = serial.Serial(comport, baudrate = 250000)
            print('DMX interface connected')
        except Exception as e:
            print('Error : Connection failed')


    def set_channel(self,num_channel,value):
        if type(num_channel) is not int:
            raise TypeError(str(num_channel)+" Must be int")
        if type(value) is not int:
            raise TypeError(str(num_channel)+" Must be int")
        if num_channel >511 :
            raise ValueError(num_channel+" Must be less than 512")
        if value >255 :
            raise ValueError(num_channel+" Must be less than 255")
        self.data[num_channel] = value

    def set_data(self, data_in,index_addr,number_channel):
        self.data[index_addr:index_addr+number_channel]=data_in

    def send_data(self):
        data_out = np.concatenate((self.start_byte, self.data, self.end_byte)).tobytes()
        self.com.write(data_out)


class light_group(object):
    def __init__(self,number_channel) -> None:
        self.number_channel=0
        self.group_data= np.zeros([number_channel], np.uint8)
        

    def addtogroup(self,lightsystem):
        if self.number_channel != lightsystem.number_channel:
            raise ValueError(" Number of channel must be the same !")
        