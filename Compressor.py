import matplotlib.pyplot as plt
from PIL import Image
import easygui
import numpy as np
from math import sin, pi, floor

myimg = Image.open(easygui.fileopenbox())
img = np.array(myimg)
print(img.size) #retourne le nombre de pixel
print(img.shape[0])

def sinus(x):
    if x == 0:
        return 1.0
    else:
        return sin(pi * x) / (pi * x)
    
def kernel(x,a):
     if abs(x) < a:
        return sinus(x)*sinus(x/a)

def Lanczos(h,l):
    a = 3
    img2 = np.array([h,l,3])
    H = img.shape[0]
    L = img.shape[0]
    scale_x = L / l
    scale_y = H / h
    for y in range(y-a, y+a+1):
        for x in range(x-a, x+a+1):
            pixel = img[y,x]
            if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
                distance_x = img2[x] - x
                distance_y = img2[y] - y



plt.imshow(myimg)
plt.show()

""" print("Dimensions de l'image : ",img.shape) # Dimensions x, y et nombre de couleurs
print("Pixel 500 sur 200 : ",img[200,500]) #pour afficher les composantes RVB du pixel aux coordonnées (200; 500)
print("Composante rouge de ce dernier pixel :",img[200,500][0])
print("Rouge : ",img[:,:,0]) """