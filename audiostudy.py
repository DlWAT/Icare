import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fftshift
from scipy import signal
from scipy.io import wavfile
import wave
import soundfile as sf
hop_length = 256

n_fft=2**12
samplerate=44100
input_file = '8 shotgun.wav'
output_file = 'G53-41101-1111-00002.wav'
data=wave.open("sample.wav")

data, samplerate = sf.read("sample.wav") 
#samplerate, data = wavfile.read('sample.wav')
f, t, Sxx = signal.spectrogram(data, samplerate)
#plt.pcolormesh(t, f, Sxx, shading='gouraud')