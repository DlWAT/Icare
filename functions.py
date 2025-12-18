import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R
from scipy.signal import butter, lfilter
import quaternion

def remove_gravity(acceleration, orientation_quaternion):
    # Gravité terrestre dans le référentiel du monde
    gravity_world = np.array([0, 0, -9.81])

    # Rotation inverse de la gravité dans le référentiel de l'accéléromètre
    inverse_orientation = np.conjugate(orientation_quaternion)
    gravity_accelerometer = quaternion.rotate_vectors(inverse_orientation, gravity_world)

    # Retirer la composante de la gravité des mesures de l'accéléromètre
    acceleration_without_gravity = acceleration - gravity_accelerometer

    return acceleration_without_gravity

def pos_orient(accel_data, gyro_data, dt, position, orientation, velocity,
               accel_bias=np.array([0, 0, 0]), gyro_bias=np.array([0, 0, 0]),
               object_frame=None):
    
    # Mesurer l'accélération et la vitesse angulaire
    accel_measurement = accel_data[-1, :] - accel_bias

    # Orientation quaternion de l'accéléromètre
    orientation_quaternion = np.array(orientation)  # Assurez-vous que orientation est une liste ou un tableau [w, x, y, z]

    # Calcul de la projection de la gravité dans le référentiel de l'accéléromètre
    accel_measurement = remove_gravity(accel_measurement, orientation)
    
    gyro_measurement = gyro_data[-1, :] - gyro_bias
    print("acc : ",accel_measurement)
    print("gyr : ",gyro_measurement)
    # Intégration de l'accélération pour obtenir la vitesse
    velocity += accel_measurement * dt  # pas de croix ici, car accel_measurement est maintenant un vecteur 3D

    # Calculer la nouvelle orientation avec les quaternions
    angle_change = np.linalg.norm(gyro_measurement) * dt
    axis_change = gyro_measurement / np.linalg.norm(gyro_measurement)
    delta_orientation = R.from_rotvec(angle_change * axis_change).as_quat()

    # Ensure the rotation vector has the correct shape
    delta_orientation_quat = quaternion.from_rotation_vector(delta_orientation[1:])

    # Perform quaternion multiplication
    orientation = orientation * delta_orientation_quat

    # Intégration de la vitesse pour obtenir la position
    position += velocity * dt #+ 0.5 #* accel_measurement * dt**2

    # Rotate object_frame using the rotated orientation
    if object_frame is not None:
        object_frame_rotated = quaternion.rotate_vectors(orientation, object_frame.T).T
        return position, orientation, velocity, object_frame_rotated
    else:
        return position, orientation, velocity


def butter_lowpass_filter(data, cutoff_frequency, fs, order=4):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_frequency / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = lfilter(b, a, data, axis=0)
    return y

def accelerometer_orientation_initiale(ax, ay, az):
    # Normalisation des composantes de l'accéléromètre
    norm = np.linalg.norm([ax, ay, az])
    ax, ay, az = ax / norm, ay / norm, az / norm
    
    # Calcul des composantes du quaternion
    angle_z = np.arccos(az)
    angle_x = np.arccos(ax / np.sqrt(1 - az**2))
    angle_y = np.arccos(ay / np.sqrt(1 - az**2))
    
    axis_z = np.cross([0, 0, -1], [ax, ay, az])
    axis_x = np.cross([0, 0, -1], [ay, -ax, 0])  # Composante x est dans le plan XY
    axis_y = np.cross([0, 0, -1], [-az, 0, ax])  # Composante y est dans le plan XY
    
    # Création du quaternion
    quat_z = quaternion.from_rotation_vector(angle_z * axis_z)
    quat_x = quaternion.from_rotation_vector(angle_x * axis_x)
    quat_y = quaternion.from_rotation_vector(angle_y * axis_y)
    
    # Combinaison des quaternions pour obtenir l'orientation complète
    orientation_quaternion = quat_z * quat_x * quat_y
    
    return orientation_quaternion