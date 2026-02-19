import matplotlib.pyplot as plt
from PIL import Image
import easygui
import numpy as np
from math import sin, pi, floor

myimg = Image.open(easygui.fileopenbox())
img = np.array(myimg)
print(img.size) #retourne le nombre de pixel
print(img.shape[0])

def sinc(x):
    if x == 0:
        return 1.0
    return sin(pi * x) / (pi * x)

def lanczos_kernel(x, a=3):
    if abs(x) < a:
        return sinc(x) * sinc(x / a)
    return 0.0


def lanczos_resize(img, new_h, new_w, a=3):

    H, W = img.shape[:2]
    channels = img.shape[2] if len(img.shape) == 3 else 1

    # image de sortie
    if channels == 1:
        output = np.zeros((new_h, new_w))
    else:
        output = np.zeros((new_h, new_w, channels))

    # facteurs d'échelle
    scale_x = W / new_w
    scale_y = H / new_h

    # boucle principale
    for y_new in range(new_h):
        for x_new in range(new_w):

            # position réelle dans l'image originale
            x_old = x_new * scale_x
            y_old = y_new * scale_y

            x_base = floor(x_old)
            y_base = floor(y_old)

            sum_val = np.zeros(channels) if channels > 1 else 0
            total_weight = 0

            # voisins autour
            for y in range(y_base - a + 1, y_base + a + 1):
                for x in range(x_base - a + 1, x_base + a + 1):

                    # vérification bordures
                    if 0 <= x < W and 0 <= y < H:

                        dx = x_old - x
                        dy = y_old - y

                        weight = lanczos_kernel(dx, a) * lanczos_kernel(dy, a)

                        sum_val += img[y, x] * weight
                        total_weight += weight

            # normalisation
            if total_weight != 0:
                output[y_new, x_new] = sum_val / total_weight

    return output.astype(np.uint8)

img2 = lanczos_resize(img, 500, 500, 3)
plt.imshow(img2)
plt.show()

""" print("Dimensions de l'image : ",img.shape) # Dimensions x, y et nombre de couleurs
print("Pixel 500 sur 200 : ",img[200,500]) #pour afficher les composantes RVB du pixel aux coordonnées (200; 500)
print("Composante rouge de ce dernier pixel :",img[200,500][0])
print("Rouge : ",img[:,:,0]) """