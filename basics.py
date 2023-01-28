import pysimpledmx
mydmx = pysimpledmx.DMXConnection(8)

mydmx.setChannel(1, 255) # set DMX channel 1 to full
mydmx.setChannel(2, 128) # set DMX channel 2 to 128
mydmx.setChannel(3, 0)   # set DMX channel 3 to 0
mydmx.render()    # render all of the above changes onto the DMX network

mydmx.setChannel(4, 255, autorender=True) # set channel 4 to full and render to the network