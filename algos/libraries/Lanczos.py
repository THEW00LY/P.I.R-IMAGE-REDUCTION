import ctypes
import os
import sys
import numpy as np

# --- Chargement automatique de la lib selon l'OS ---
def _charger_lib():
    dossier = os.path.dirname(os.path.abspath(__file__))
    if sys.platform == "win32":
        nom = "lanczos.dll"
    elif sys.platform == "darwin":
        nom = "lanczos.dylib"
    else:
        nom = "lanczos.so"
    
    chemin = os.path.join(dossier, nom)
    return ctypes.CDLL(chemin)

_lib = _charger_lib()


# argtypes -> Paramètres
# restypes -> retours
_lib.lanczos.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.lanczos.restype  = ctypes.c_void_p

# --- API publique : fonctions Python normales ---
def lanczos(img, old_h, old_w, new_h, new_w, a):
    return _lib.lanczos(img, old_h, old_w, new_h, new_w, a)