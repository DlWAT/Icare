import pydmxIcare
import pydmxlight
mydmx= pydmxIcare.DMX_Icare()
par_led1=pydmxlight.Par_Led_615_AFX(5,0)

print(mydmx.data[0:5])

mydmx.set_channel(1,255)
print(mydmx.data[0:5])

par_led1.set_channel(2,125)
par_led1.set_channel(3,18)
mydmx.set_data(par_led1.data,5,5)
print(mydmx.data[0:10])
