import numpy as np

class Par_Led_615_AFX(object):
    
    def __init__(self,number_channel,position) -> None:
        self.data=np.zeros([number_channel], np.uint8)
        self.pos=position
        self.number_channel=number_channel
        self.position=position
    
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