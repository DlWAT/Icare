import socket
import time
import matplotlib.pyplot as plt
import numpy as np
msgClient = "Hello Server"
msgToSend = str.encode(msgClient)
addrPort = ("192.168.1.43", 9999)
bufferSize = 1024


# Créer un socket UDP coté client
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
Lx=[]
Ly=[]
Lz=[]

Gx=[]
Gy=[]
Gz=[]

for i in range (200):
# Envoyer au serveur à l'aide du socket UDP créé
    s.sendto(msgToSend, addrPort)
    msgServer = s.recvfrom(bufferSize)
    msg=msgServer[0].decode()
    
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


ax=0
ay=0
az=0
print("calibration faite")
time.sleep(2)
print("go")
for i in range (500):
    t0= time.time()
# Envoyer au serveur à l'aide du socket UDP créé
    s.sendto(msgToSend, addrPort)
    msgServer = s.recvfrom(bufferSize)
    msg=msgServer[0].decode()
    
    Lx.append(int(msg[0:5])-mx-32767)
    Ly.append(int(msg[5:10])-my-32767)
    Lz.append(int(msg[10:15])-mz-32767)
    Gx.append(int(msg[15:20])-mgx-32767)
    Gy.append(int(msg[20:25])-mgy-32767)
    Gz.append(int(msg[25:30])-mgz-32767)
    t1 = time.time() -t0
    ax+=t1*Gx[-1]*250/16384
    ay+=t1*Gy[-1]*250/16384
    az+=t1*Gz[-1]*250/16384
    print("Time elapsed: ", t1 )
    print(ax,ay,az)
    #print(Gx[-1],Gy[-1],Gz[-1])
    
    
    