import numpy as np

import matplotlib.pyplot as plt

import librosa
import librosa.display

from scipy import signal

hop_length = 256

n_fft=2**12
input_file = '8 shotgun.wav'
output_file = 'G53-41101-1111-00002.wav'

x, sr = librosa.load(input_file,duration=2)#offset=7, duration=0.5
#x, sr = librosa.load('G53-58308-1111-00035.wav',offset=0.5, duration=0.5)

fig, ax = plt.subplots()
D = librosa.amplitude_to_db(np.abs(librosa.stft(x,n_fft=n_fft,hop_length=hop_length)), ref=np.max)
print(type(D))


img = librosa.display.specshow(D, y_axis='linear', x_axis='time',
                               sr=sr, hop_length=hop_length)

ax.set_title('Log-frequency power spectrogram')
ax.label_outer()

plt.colorbar(img, format="%+2.f dB")
plt.show()

def function(a):
    """"""
    b=2*a
    return b