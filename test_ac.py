import socket
import time
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from functions import pos_orient, butter_lowpass_filter, accelerometer_orientation_initiale
from scipy.spatial.transform import Rotation as R
from datetime import datetime
import quaternion

msgClient = "Hello Server"
msgToSend = str.encode(msgClient)
target_host = '192.168.237.221'
target_port = 7210

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
Lx = []
Ly = []
Lz = []

Gx = []
Gy = []
Gz = []

for i in range(100):
    # Envoyer au serveur à l'aide du socket UDP créé
    nBytes = client.sendto('give me data'.encode('utf-8'), (target_host, target_port))
    msgServer, addr = client.recvfrom(4096)
    msg = msgServer.decode()

    Lx.append(int(msg[0:5]) - 32767)
    Ly.append(int(msg[5:10]) - 32767)
    Lz.append(int(msg[10:15]) - 32767)
    Gx.append(int(msg[15:20]) - 32767)
    Gy.append(int(msg[20:25]) - 32767)
    Gz.append(int(msg[25:30]) - 32767)

mx = int(np.mean(Lx))
my = int(np.mean(Ly))
mz = int(np.mean(Lz))

mgx = int(np.mean(Gx))
mgy = int(np.mean(Gy))
mgz = int(np.mean(Gz))

Lax = []
Lay = []
Laz = []
g = np.array([0, 0, -9.81])  # accélération due à la gravité

# Paramètres de l'accéléromètre et du gyroscope
accel_bias = np.array([0, 0, -0])  # biais de l'accéléromètre
gyro_bias = np.array([0, 0, -0])  # biais du gyroscope

# Fréquence d'échantillonnage
dt = 0.2  # intervalle de temps entre les échantillons (augmenté)
sample_freq = 1 / dt

# Générer des données factices pour l'accéléromètre et le gyroscope
num_samples = 50
accel_data = np.random.randn(num_samples, 3)  # données aléatoires pour l'accéléromètre
gyro_data = np.random.randn(num_samples, 3)  # données aléatoires pour le gyroscope

# Initialiser les variables de rotation
orientation = accelerometer_orientation_initiale(mx, my, mz)  # quaternion initial [w, x, y, z]
print(orientation)
# Initialiser les variables de position et vitesse
position = np.zeros(3)
velocity = np.zeros(3)

# Initialiser le repère de l'objet
object_frame = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])  # Repère initial (X, Y, Z)

# Boucle de simulation
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

print("calibration faite")
#time.sleep(2)
print("go")
sos = signal.butter(2, 50, 'lp', fs=1000, output='sos')
t0 = time.time()
time_1 = datetime.now()
elapsed_time = []
Lx = []
Ly = []
Lz = []

Gx = []
Gy = []
Gz = []
for i in range(400):
    elapsed_time.append((datetime.now() - time_1).total_seconds())
    time_1 = datetime.now()
    dt = elapsed_time[-1]
    # Envoyer au serveur à l'aide du socket UDP créé
    nBytes = client.sendto('give me data'.encode('utf-8'), (target_host, target_port))
    msgServer, addr = client.recvfrom(4096)
    msg = msgServer.decode()
    Lx.append(int(msg[0:5]) - 32767)
    Ly.append(int(msg[5:10]) - 32767)
    Lz.append(int(msg[10:15]) - 32767)
    Gx.append(int(msg[15:20]) - 32767)
    Gy.append(int(msg[20:25]) - 32767)
    Gz.append(int(msg[25:30]) - 32767)
    accx = (int(msg[0:5]) - mx - 32767) / 2 ** 16 * 9.81
    accy = (int(msg[5:10]) - my - 32767) / 2 ** 16 * 9.81
    accz = (int(msg[10:15]) - mz - 32767) / 2 ** 16 * 9.81
    gx = (int(msg[15:20]) - mgx - 32767) / 2 ** 16 * 250 * (2 * np.pi / 360)
    gy = (int(msg[20:25]) - mgy - 32767) / 2 ** 16 * 250 * (2 * np.pi / 360)
    gz = (int(msg[25:30]) - mgz - 32767) / 2 ** 16 * 250 * (2 * np.pi / 360)
    accel_data += np.array([accx, accy, accz])
    gyro_data += np.array([gx, gy, gz])
    fs = 1 / np.mean(elapsed_time)
    
    #acc_data = butter_lowpass_filter(accel_data, 50, fs, order=2)
    #gyr_data = butter_lowpass_filter(gyro_data, 50, fs, order=2)
    position, orientation, velocity = pos_orient(accel_data, gyro_data, dt, position, orientation, velocity)

    # Dessiner le repère de l'objet en temps réel
    object_frame_rotated = quaternion.rotate_vectors(orientation, object_frame.T).T
    quiver_length = 20  # Taille des flèches

    for j in range(3):
        ax.quiver(position[0], position[1], position[2],
                  object_frame_rotated[0, j], object_frame_rotated[1, j], object_frame_rotated[2, j],
                  color=['r', 'g', 'b'][j], length=quiver_length, normalize=True)

# Afficher les résultats
print("Position finale:", position)

# Visualiser la trajectoire
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.show()

mx = int(np.mean(Lx))
my = int(np.mean(Ly))
mz = int(np.mean(Lz))

mgx = int(np.mean(Gx))
mgy = int(np.mean(Gy))
mgz = int(np.mean(Gz))
print(mx,my,mz)
print(mgx,mgy,mgz)