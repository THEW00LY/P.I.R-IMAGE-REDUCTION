import ctypes
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import libraries.Lanczos as Lanczos
import sys

if len(sys.argv) > 1:
    image_path = sys.argv[1]

else:
    raise ValueError("Aucun fichier fourni")

new_H = int(sys.argv[2]) if len(sys.argv) > 2 else 250
new_W = int(sys.argv[3]) if len(sys.argv) > 3 else 250
a     = int(sys.argv[4]) if len(sys.argv) > 4 else 6

myimg = Image.open(image_path).convert("RGB")  # force RGB, évite RGBA ou palette

# Garder img_array en vie jusqu'à la fin avec une référence explicite
img_array = np.ascontiguousarray(np.array(myimg, dtype=np.int32))

H, W = img_array.shape[:2]


# Passer le pointeur ET garder img_array vivant
ptr_img = img_array.ctypes.data_as(ctypes.c_void_p)
ptr_image_reduced = Lanczos.lanczos(ptr_img, H, W, new_H, new_W, a)
del ptr_img  # on n'en a plus besoin, mais img_array reste en vie

# Vérification que le résultat n'est pas nul
if ptr_image_reduced is None:
    raise RuntimeError("La lib C a retourné un pointeur nul")

result_array = np.ctypeslib.as_array(
    ctypes.cast(ptr_image_reduced, ctypes.POINTER(ctypes.c_int)),
    shape=(new_H, new_W, 3)
).copy()  # .copy() détache du pointeur C immédiatement

result_img = result_array.astype(np.uint8)

# Sauvegarde
output_path = "output.jpg"
Image.fromarray(result_img).save(output_path)
print("Compression terminée")