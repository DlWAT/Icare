import pydmxIcare

mydmx= pydmxIcare.DMX_Icare()
mydmx.connection()
mydmx.set_channel(1,255)