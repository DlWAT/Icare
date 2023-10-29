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
for i in range (50):
# Envoyer au serveur à l'aide du socket UDP créé
    s.sendto(msgToSend, addrPort)
    msgServer = s.recvfrom(bufferSize)
    msg=msgServer[0].decode()
    
    Lx.append(int(msg[0:5])-32767)
    Ly.append(int(msg[5:10])-32767)
    Lz.append(int(msg[10:15])-32767)

mx=np.mean(Lx)
my=np.mean(Ly)
mz=np.mean(Lz)
Lx=[]
Ly=[]
Lz=[]
print("calibration faite")
time.sleep(2)
print("go")
for i in range (500):
# Envoyer au serveur à l'aide du socket UDP créé
    s.sendto(msgToSend, addrPort)
    msgServer = s.recvfrom(bufferSize)
    msg=msgServer[0].decode()
    
    Lx.append(int(msg[0:5])-mx-32767)
    Ly.append(int(msg[5:10])-my-32767)
    Lz.append(int(msg[10:15])-mz-32767)

plt.figure()
plt.plot(Lx)
plt.plot(Ly)
plt.plot(Lz)
plt.ylim(-32568,32568)
plt.show()