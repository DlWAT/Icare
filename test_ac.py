import socket
import time
import matplotlib.pyplot as plt
import numpy as np
msgClient = "Hello Server"
msgToSend = str.encode(msgClient)
target_host = '192.168.237.221'
target_port = 7210

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
Lx=[]
Ly=[]
Lz=[]

Gx=[]
Gy=[]
Gz=[]

for i in range (200):
# Envoyer au serveur à l'aide du socket UDP créé
    nBytes = client.sendto('give me data'.encode('utf-8'), (target_host, target_port))
    #print(nBytes, 'Bytes', 'Send OK')
    msgServer, addr = client.recvfrom(4096)
    msg=msgServer.decode()
    
    Lx.append(int(msg[0:5])-32767)
    Ly.append(int(msg[5:10])-32767)
    Lz.append(int(msg[10:15])-32767)
    Gx.append(int(msg[15:20])-32767)
    Gy.append(int(msg[20:25])-32767)
    Gz.append(int(msg[25:30])-32767)
   
mx=int(np.mean(Lx))
my=int(np.mean(Ly))
mz=int(np.mean(Lz))

mgx=int(np.mean(Gx))
mgy=int(np.mean(Gy))
mgz=int(np.mean(Gz))

Lx=[]
Ly=[]
Lz=[]


angx=0
angy=0
angz=0

ax=0
ay=0
az=0

ax0=[]
ay0=[]
az0=[]

vx0=[0]
vy0=[0]
vz0=[0]
Gx=[]
Gy=[]
Gz=[]
x=0
y=0
z=0

Lx=[0]
Ly=[0]
Lz=[0]

print("calibration faite")
time.sleep(2)
print("go")
t0= time.time()
for i in range (500):
# Envoyer au serveur à l'aide du socket UDP créé
    nBytes = client.sendto('give me data'.encode('utf-8'), (target_host, target_port))
    #print(nBytes, 'Bytes', 'Send OK')
    msgServer, addr = client.recvfrom(4096)
    msg=msgServer.decode()
    
    #Lx.append(int(msg[0:5])-mx-32767)
    #Ly.append(int(msg[5:10])-my-32767)
    #Lz.append(int(msg[10:15])-mz-32767)
    Gx.append(int(msg[15:20])-mgx-32767)
    Gy.append(int(msg[20:25])-mgy-32767)
    Gz.append(int(msg[25:30])-mgz-32767)
    g=9.80665
    #g=1
    ax=g*(int(msg[0:5])-mx-32767)/2**16
    ay=g*(int(msg[5:10])-mx-32767)/2**16
    az=g*(int(msg[10:15])-mx-32767)/2**16
    
    t1 = time.time() -t0
    t0= time.time()
    angx+=t1*Gx[-1]*250*(2*np.pi/360)/2**16
    angy+=t1*Gy[-1]*250*(2*np.pi/360)/2**16
    angz+=t1*Gz[-1]*250*(2*np.pi/360)/2**16
    
    ax0.append(ax*(np.cos(angy)+np.cos(angz))+az*np.sin(angy)-ay*np.sin(angz)+0.00771732223743174)
    ay0.append(ay*(np.cos(angz)+np.cos(angx))+ax*np.sin(angz)-az*np.sin(angx)+4.460826898951338)
    az0.append(az*(np.cos(angx)+np.cos(angy))+ay*np.sin(angx)-ax*np.sin(angy)-2.773501512537836)
    if i>1:
        print(ax0[-1],ay0[-1],az0[-1])
        vx0.append(vx0[-1]+(ax0[-1]-ax0[-2])*t1)
        vy0.append(vy0[-1]+(ay0[-1]-ay0[-2])*t1)
        vz0.append(vz0[-1]+(az0[-1]-az0[-2])*t1)
        #print(Lx[-1],Ly[-1],Lz[-1])
        Lx.append(Lx[-1]+(vx0[-1]-vx0[-2])*t1)
        Ly.append(Ly[-1]+(vy0[-1]-vy0[-2])*t1)
        Lz.append(Lz[-1]+(vz0[-1]-vz0[-2])*t1)
    
    
    #print("Time elapsed: ", t1 )
    #print(x,y,z)
print(angx,angy,angz) 
plt.figure()
plt.plot(vx0)
plt.plot(vy0)
plt.plot(vz0)
plt.figure()
plt.plot(Lx)
plt.plot(Ly)
plt.plot(Lz)

print(np.mean(ax0),np.mean(ay0),np.mean(az0))
#plt.ylim(-10,10)
plt.show()