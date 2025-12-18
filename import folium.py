import cv2
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt
from scipy.fftpack import fft

# Initialisation de MediaPipe pour la détection des visages
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils

# Fonction pour obtenir les pixels autour du nez
def get_nose_region(frame, detection):
    image_height, image_width, _ = frame.shape
    bbox = detection.location_data.relative_bounding_box
    nose_x = int(bbox.xmin * image_width + bbox.width * image_width / 2)
    nose_y = int(bbox.ymin * image_height + bbox.height * image_height / 2)
    region_size = 10  # Taille de la région autour du nez

    # Extraction de la région autour du nez
    nose_region = frame[
        nose_y - region_size : nose_y + region_size,
        nose_x - region_size : nose_x + region_size
    ]
    return nose_region

# Initialisation de la capture vidéo
cap = cv2.VideoCapture(0)

# Stockage des valeurs des pixels
pixel_values = []

with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Conversion de l'image en RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(frame_rgb)

        if results.detections:
            for detection in results.detections:
                nose_region = get_nose_region(frame_rgb, detection)
                if nose_region.size > 0:
                    pixel_mean = np.mean(nose_region, axis=(0, 1))
                    pixel_values.append(pixel_mean)

                # Dessiner les détections de visage
                mp_drawing.draw_detection(frame, detection)

        # Affichage de l'image
        cv2.imshow('Face Detection', frame)

        # Sortir de la boucle en appuyant sur 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

# Libération des ressources
cap.release()
cv2.destroyAllWindows()

# Conversion de la liste des valeurs de pixels en un tableau NumPy
pixel_values = np.array(pixel_values)

# Tracé du signal temporel
plt.figure()
plt.plot(pixel_values)
plt.title('Signal Temporel des Valeurs de Pixels Autour du Nez')
plt.xlabel('Temps')
plt.ylabel('Valeur de Pixel')
plt.show()

# Calcul et tracé de la Transformée de Fourier
pixel_values_flattened = pixel_values.mean(axis=1)  # Moyenne sur les canaux de couleur
N = len(pixel_values_flattened)
T = 1.0 / 30.0  # Supposons une fréquence de 30 FPS
yf = fft(pixel_values_flattened)
xf = np.fft.fftfreq(N, T)[:N//2]

plt.figure()
plt.plot(xf, 2.0/N * np.abs(yf[:N//2]))
plt.title('Transformée de Fourier des Valeurs de Pixels')
plt.xlabel('Fréquence (Hz)')
plt.ylabel('Amplitude')
plt.show()
