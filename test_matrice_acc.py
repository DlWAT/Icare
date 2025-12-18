import numpy as np
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
import serial
import time

class IMUProcessor:
    def __init__(self, dt=0.01):
        self.acceleration = []
        self.gyroscope = []
        self.dt = dt
        self.orientations = []

    def add_data(self, acc, gyro):
        self.acceleration.append(acc)
        self.gyroscope.append(gyro)
        if not self.orientations:
            self.orientations.append(R.from_euler('xyz', [0, 0, 0], degrees=True))
        else:
            orientation = self.orientations[-1]
            delta_rotation = R.from_rotvec(gyro * self.dt)
            orientation = orientation * delta_rotation
            self.orientations.append(orientation)

    def compensate_gravity_and_transform(self, acceleration, orientation):
        g = np.array([0, 0, 9.81])  # Gravitational acceleration in m/s^2
        acc_no_gravity = acceleration - orientation.apply(g)
        acc_transformed = orientation.apply(acc_no_gravity)
        return acc_transformed

    def integrate(self, transformed_acceleration):
        velocity = np.cumsum(transformed_acceleration * self.dt, axis=0)
        position = np.cumsum(velocity * self.dt, axis=0)
        return velocity, position

    def process(self):
        if not self.acceleration or not self.gyroscope:
            return np.zeros((1, 3)), np.zeros((1, 3))  # Retourne des tableaux 2D vides si pas de données

        acc_transformed = np.array([self.compensate_gravity_and_transform(acc, orientation) for acc, orientation in zip(self.acceleration, self.orientations)])
        velocity, position = self.integrate(acc_transformed)
        return velocity, position

    def get_positions_and_angles(self):
        velocity, position = self.process()
        if len(self.orientations) == 0:
            angles = np.zeros((1, 3))
        else:
            angles = np.array([orientation.as_euler('xyz', degrees=True) for orientation in self.orientations])
        if position.ndim == 1:
            position = position.reshape(-1, 3)  # Assurez-vous que position est un tableau 2D
        return {
            'x': position[:, 0],
            'y': position[:, 1],
            'z': position[:, 2],
            'roll': angles[:, 0],
            'pitch': angles[:, 1],
            'yaw': angles[:, 2]
        }

# Initialiser la communication série avec le capteur
ser = serial.Serial('COM3', baudrate=9600, timeout=1)  # Remplacez 'COM9' par le port série approprié

# Initialiser le processeur IMU
imu_processor = IMUProcessor(dt=0.01)
timestamps = []  # Liste pour stocker les timestamps

# Visualisation en 3D avec les graphes des accélérations, des vitesses angulaires, des positions et des angles
fig = plt.figure(figsize=(20, 15))

# Subplot pour la trajectoire en 3D
ax_traj = fig.add_subplot(231, projection='3d')
ax_traj.set_title('Trajectoire en tire-bouchon')
ax_traj.set_xlabel('X')
ax_traj.set_ylabel('Y')
ax_traj.set_zlabel('Z')

# Subplot pour les accélérations
ax_acc = fig.add_subplot(232)
ax_acc.set_title('Accélérations')
ax_acc.set_xlabel('Temps (s)')
ax_acc.set_ylabel('Accélération (m/s^2)')
line_acc_x, = ax_acc.plot([], [], label='acc_x')
line_acc_y, = ax_acc.plot([], [], label='acc_y')
line_acc_z, = ax_acc.plot([], [], label='acc_z')
ax_acc.legend()

# Subplot pour les vitesses angulaires
ax_gyro = fig.add_subplot(233)
ax_gyro.set_title('Vitesses angulaires')
ax_gyro.set_xlabel('Temps (s)')
ax_gyro.set_ylabel('Vitesse angulaire (rad/s)')
line_gyro_x, = ax_gyro.plot([], [], label='gyro_x')
line_gyro_y, = ax_gyro.plot([], [], label='gyro_y')
line_gyro_z, = ax_gyro.plot([], [], label='gyro_z')
ax_gyro.legend()

# Subplot pour les positions
ax_pos = fig.add_subplot(235)
ax_pos.set_title('Positions')
ax_pos.set_xlabel('Temps (s)')
ax_pos.set_ylabel('Position (m)')
line_pos_x, = ax_pos.plot([], [], label='pos_x')
line_pos_y, = ax_pos.plot([], [], label='pos_y')
line_pos_z, = ax_pos.plot([], [], label='pos_z')
ax_pos.legend()

# Subplot pour les angles
ax_ang = fig.add_subplot(236)
ax_ang.set_title('Angles')
ax_ang.set_xlabel('Temps (s)')
ax_ang.set_ylabel('Angle (deg)')
line_roll, = ax_ang.plot([], [], label='roll')
line_pitch, = ax_ang.plot([], [], label='pitch')
line_yaw, = ax_ang.plot([], [], label='yaw')
ax_ang.legend()

# Ligne de la trajectoire en pointillés
line_traj, = ax_traj.plot([], [], [], 'r--')
# Point mobile en forme de curseur
point_traj, = ax_traj.plot([], [], [], 'bo')

def init():
    line_traj.set_data([], [])
    line_traj.set_3d_properties([])
    point_traj.set_data([], [])
    point_traj.set_3d_properties([])
    line_acc_x.set_data([], [])
    line_acc_y.set_data([], [])
    line_acc_z.set_data([], [])
    line_gyro_x.set_data([], [])
    line_gyro_y.set_data([], [])
    line_gyro_z.set_data([], [])
    line_pos_x.set_data([], [])
    line_pos_y.set_data([], [])
    line_pos_z.set_data([], [])
    line_roll.set_data([], [])
    line_pitch.set_data([], [])
    line_yaw.set_data([], [])
    return line_traj, point_traj, line_acc_x, line_acc_y, line_acc_z, line_gyro_x, line_gyro_y, line_gyro_z, line_pos_x, line_pos_y, line_pos_z, line_roll, line_pitch, line_yaw

def update(frame):
    # Lire les données du capteur
    ser.write(b'READ_DATA\n')  # Commande pour lire les données du capteur (à adapter selon le protocole du capteur)
    line = ser.readline().decode(errors='ignore').strip()  # Ignorer les erreurs de décodage
    if line:
        try:
            data = list(map(float, line.split(',')))
            if len(data) == 6:
                acc = np.array(data[:3])
                gyro = np.array(data[3:])
                imu_processor.add_data(acc, gyro)
                timestamps.append(len(timestamps) * imu_processor.dt)
        except ValueError:
            print(f"Skipping invalid data: {line}")

    if len(imu_processor.acceleration) < len(timestamps):
        return

    positions_and_angles = imu_processor.get_positions_and_angles()

    frame_limit = min(frame, len(timestamps))  # Limiter le nombre de frames pour éviter l'IndexError

    line_traj.set_data(positions_and_angles['x'][:frame_limit], positions_and_angles['y'][:frame_limit])
    line_traj.set_3d_properties(positions_and_angles['z'][:frame_limit])
    point_traj.set_data(positions_and_angles['x'][frame_limit-1], positions_and_angles['y'][frame_limit-1])
    point_traj.set_3d_properties(positions_and_angles['z'][frame_limit-1])

    line_acc_x.set_data(timestamps[:frame_limit], np.array(imu_processor.acceleration)[:frame_limit, 0])
    line_acc_y.set_data(timestamps[:frame_limit], np.array(imu_processor.acceleration)[:frame_limit, 1])
    line_acc_z.set_data(timestamps[:frame_limit], np.array(imu_processor.acceleration)[:frame_limit, 2])

    line_gyro_x.set_data(timestamps[:frame_limit], np.array(imu_processor.gyroscope)[:frame_limit, 0])
    line_gyro_y.set_data(timestamps[:frame_limit], np.array(imu_processor.gyroscope)[:frame_limit, 1])
    line_gyro_z.set_data(timestamps[:frame_limit], np.array(imu_processor.gyroscope)[:frame_limit, 2])

    line_pos_x.set_data(timestamps[:frame_limit], positions_and_angles['x'][:frame_limit])
    line_pos_y.set_data(timestamps[:frame_limit], positions_and_angles['y'][:frame_limit])
    line_pos_z.set_data(timestamps[:frame_limit], positions_and_angles['z'][:frame_limit])

    line_roll.set_data(timestamps[:frame_limit], positions_and_angles['roll'][:frame_limit])
    line_pitch.set_data(timestamps[:frame_limit], positions_and_angles['pitch'][:frame_limit])
    line_yaw.set_data(timestamps[:frame_limit], positions_and_angles['yaw'][:frame_limit])

    return line_traj, point_traj, line_acc_x, line_acc_y, line_acc_z, line_gyro_x, line_gyro_y, line_gyro_z, line_pos_x, line_pos_y, line_pos_z, line_roll, line_pitch, line_yaw

ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=20, cache_frame_data=False)

plt.show()
