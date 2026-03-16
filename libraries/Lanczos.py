import ctypes
import os
import sys
import numpy as np
import subprocess
from pathlib import Path

# --- Chargement automatique de la lib selon l'OS ---
def _charger_lib():
    dossier = os.path.dirname(os.path.abspath(__file__))
    src_path = Path(dossier) / "lanczos.c"
    dll_path = Path(dossier)/ "lanczos.dll"
    dylib_path = Path(dossier)/ "lanczos.dylib"
    so_path = Path(dossier)/ "lanczos.so"

    # Windows
    if sys.platform == "win32":
        nom = "lanczos.dll"
        try : 
            f = open(dll_path)
        except:
            print("Fichier compilation dll non reconnu, création en cours...")
            result = subprocess.run(["gcc", "-shared", "-O2", "-o", str(dll_path), str(src_path)])
            print("créer")
        else:
            print("Librarie dll exist déjà ")

    # macOS
    elif sys.platform == "darwin":
        nom = "lanczos.dylib"
        try : 
            f = open(dylib_path)
        except:
            print("Fichier compilation dylib non reconnu, création en cours...")
            result = subprocess.run(["gcc", "-shared", "-O2", "-arch", "arm64", "-arch", "x86_64", "-o", str(dylib_path), str(src_path)])
            print("créer")
        else:
            print("Librarie dylib exist déjà ")
    # Distrib Linux
    else:
        nom = "lanczos.so"
        try : 
            f = open(so_path)
        except:
            print("Fichier compilation so non reconnu, création en cours...")
            result = subprocess.run(["gcc", "-shared", "-O2", "-o", str(so_path), str(src_path)])
            print("créer")
        else:
            print("Librarie dylib exist déjà ")

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