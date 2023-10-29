import random
import tkinter as Tk
from itertools import count

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
Ld=[]
#plt.style.use('fivethirtyeight')
# values for first graph
x_vals = []

index = count()

def animate(i):
    # Generate values
    s.sendto(msgToSend, addrPort)
    msgServer = s.recvfrom(bufferSize)
    msg=msgServer[0].decode()
    x_vals.append(next(index))
    Lx.append(int(msg[0:5])-mx-32767)
    Ly.append(int(msg[5:10])-my-32767)
    Lz.append(int(msg[10:15])-mz-32767)
    Ld.append(np.sqrt((Lx[-1]**2+Ly[-1]**2+Lz[-1]**2-16384**2)/16384))
    # Get all axes of figure
    ax1, ax2, ax3, ax4= plt.gcf().get_axes()
    # Clear current data
    ax1.cla()
    ax2.cla()
    ax3.cla()
    ax4.cla()
    # Plot new data
    print(np.sum(Lx)/16384,np.sum(Ly)/16384,np.sum(Lz)/16384)
    ax1.plot(x_vals, Lx)
    ax2.plot(x_vals, Ly)
    ax3.plot(x_vals, Lz)
    ax4.plot(x_vals, Ld)


# GUI
root = Tk.Tk()
label = Tk.Label(root, text="Realtime Animated Graphs").grid(column=0, row=0)
root.geometry("1280x720")
# graph 1
canvas = FigureCanvasTkAgg(plt.gcf(), master=root)
canvas.get_tk_widget().grid(column=0, row=1)
# Create two subplots in row 1 and column 1, 2
plt.gcf().subplots(4, 1)
ani = FuncAnimation(plt.gcf(), animate, blit=False)

Tk.mainloop()