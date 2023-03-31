import matplotlib.pyplot as plt
import numpy as np
len=101
output2=np.zeros((len,len,len))
i_mid=101

for i in range (len):
    for j in range (len):
        for k in range (0,len):
            
            seuil=0.1*k
            dist=np.sqrt((i_mid-i)**2+(i_mid-j)**2)
            if dist<seuil:
                output2[i][j][k]=1
            else: 
                output2[i][j][k]=1/(1+(dist-seuil)/100)
                
print(np.max(output2))
print(np.min(output2))
plt.imshow(output2[:,50,:])
plt.show()