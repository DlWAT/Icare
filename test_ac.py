import socket
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from functions import *
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

Lax=[]
Lay=[]
Laz=[]

L_time=[0]
angx=0
angy=0
angz=0

ax=0
ay=0
az=0

ax0=[0]
ay0=[0]
az0=[0]

vx0=[0,0,0]
vy0=[0,0,0]
vz0=[0,0,0]
Gx=[]
Gy=[]
Gz=[]
x=0
y=0
z=0

Lx=[0,0,0]
Ly=[0,0,0]
Lz=[0,0,0]
g=9.80665
print("calibration faite")
time.sleep(2)
print("go")
sos = signal.butter(2, 50, 'lp', fs=1000, output='sos')
t0= time.time()
for i in range (500):
# Envoyer au serveur à l'aide du socket UDP créé
    nBytes = client.sendto('give me data'.encode('utf-8'), (target_host, target_port))
    #print(nBytes, 'Bytes', 'Send OK')
    msgServer, addr = client.recvfrom(4096)
    msg=msgServer.decode()
    
    Lax.append(g*(int(msg[0:5])-mx-32767)/2**16)
    Lay.append(g*(int(msg[5:10])-my-32767)/2**16)
    Laz.append(g*(int(msg[10:15])-mz-32767)/2**16)
    Gx.append(int(msg[15:20])-mgx-32767)
    Gy.append(int(msg[20:25])-mgy-32767)
    Gz.append(int(msg[25:30])-mgz-32767)
    
    
    #g=1
    ax=g*(int(msg[0:5])-0*mx-32767)/2**16
    ay=g*(int(msg[5:10])-0*my-32767)/2**16
    az=g*(int(msg[10:15])-0*mz-32767)/2**16
    
    t1 = time.time() -t0
    L_time.append(t1+L_time[-1])
    t0= time.time()
    
    angx+=t1*Gx[-1]*250*(2*np.pi/360)/2**16
    angy+=t1*Gy[-1]*250*(2*np.pi/360)/2**16
    angz+=t1*Gz[-1]*250*(2*np.pi/360)/2**16
    
    ax0.append(ax*(np.cos(angy)+np.cos(angz))+az*np.sin(angy)-ay*np.sin(angz))
    ay0.append(ay*(np.cos(angz)+np.cos(angx))+ax*np.sin(angz)-az*np.sin(angx))
    az0.append(az*(np.cos(angx)+np.cos(angy))+ay*np.sin(angx)-ax*np.sin(angy))
    if i>1:
        filteredax = signal.sosfilt(sos, ax0)
        filtereday = signal.sosfilt(sos, ay0)
        filteredaz = signal.sosfilt(sos, az0)
        print(ax0[-1],ay0[-1],az0[-1])
        vx0.append(vx0[-1]+(filteredax[-1]+filteredax[-2])*0.5*t1)
        vy0.append(vy0[-1]+(filtereday[-1])*t1)
        vz0.append(vz0[-1]+(filteredaz[-1])*t1)
        #print(Lx[-1],Ly[-1],Lz[-1])
        Lx.append(Lx[-1]+(vx0[-1])*t1)
        Ly.append(Ly[-1]+(vy0[-1])*t1)
        Lz.append(Lz[-1]+(vz0[-1])*t1)
    
vel = get_vel_drift(time,acc)
pos = integral(time,vel,['posx','posy','posz'])
plt.figure()
plt.plot(L_time,ax0)
plt.plot(L_time,ay0)
plt.plot(L_time,az0)

plt.figure()
plt.plot(L_time,filteredax)
plt.plot(L_time,filtereday)
plt.plot(L_time,filteredaz)

plt.figure()
plt.plot(L_time,vx0)
plt.plot(L_time,vy0)
plt.plot(L_time,vz0)

plt.figure()
plt.plot(L_time,Lx)
plt.plot(L_time,Ly)
plt.plot(L_time,Lz)

print(np.mean(ax0),np.mean(ay0),np.mean(az0))
#plt.ylim(-10,10)
plt.show()