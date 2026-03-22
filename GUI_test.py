from nicegui import ui
import subprocess
import os
import time

OUTPUT_IMAGE = "output.jpg"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# État de l'application
state = {'uploaded_img': None}

image = ui.image().classes('w-96')

def run_Lanczos(file_path):
    if not file_path:
        ui.notify("⚠️ Upload une image d'abord")
        return

    subprocess.run(['python', 'Compressor.py', file_path])

    if os.path.exists(OUTPUT_IMAGE):
        image.set_source(f"{OUTPUT_IMAGE}?t={time.time()}")

# Si tu as d'autres scripts
def run_Octree(file_path):
    if not file_path:
        ui.notify("⚠️ Upload une image d'abord", type='warning')
        return
    
    # On passe l'argument au script comme pour Lanczos
    subprocess.run(['python', 'Octree.py', file_path])
    
    if os.path.exists(OUTPUT_IMAGE):
        image.set_source(f"{OUTPUT_IMAGE}?t={time.time()}")
        ui.notify("Compression Octree terminée")

def run_MedianCut(file_path):
    if not file_path:
        ui.notify("⚠️ Upload une image d'abord", type='warning')
        return

    subprocess.run(['python', 'MedianCut.py', file_path])
    
    if os.path.exists(OUTPUT_IMAGE):
        image.set_source(f"{OUTPUT_IMAGE}?t={time.time()}")
        ui.notify("Compression MedianCut terminée")

def process_image(script_name):
    if not state['uploaded_img']:
        ui.notify("⚠️ Veuillez d'abord uploader une image", type='negative')
        return
    
    # Afficher un indicateur de chargement
    with ui.spinner(size='lg'):
        try:
            # On exécute le script correspondant
            subprocess.run(['python', script_name, state['uploaded_img']], check=True)
            
            if os.path.exists(OUTPUT_IMAGE):
                # Mise à jour de l'image avec un timestamp pour le cache
                result_display.set_source(f"{OUTPUT_IMAGE}?t={time.time()}")
                ui.notify(f"Succès : {script_name} exécuté")
        except Exception as e:
            ui.notify(f"Erreur : {e}", type='negative')

def handle_upload(e):
    global uploaded_img
    
    # Debug radical : on affiche TOUT ce que l'objet contient vraiment
    print(f"Type de l'objet : {type(e)}")
    
    try:
        # Dans NiceGUI 1.4+, l'objet a directement ces attributs
        # On utilise e.name et e.content (qui est un objet file-like)
        
        name = e.name
        content = e.content # SpooledTemporaryFile
        
        path = os.path.join(UPLOAD_DIR, name)

        with open(path, "wb") as f:
            # On lit le contenu depuis le début
            content.seek(0)
            f.write(content.read())

        uploaded_img = path
        ui.notify(f"Image sauvegardée : {name}")
        print(f"Chemin stocké : {uploaded_img}")

    except AttributeError:
        # Si e.name n'existe vraiment pas, on essaie de voir si c'est un dictionnaire
        # (Parfois nécessaire selon la version de Starlette)
        ui.notify("Erreur de structure d'objet. Vérifie la console.", type='negative')
        print("L'objet ne semble pas avoir d'attribut 'name'.")
        
# --- UI Layout ---
with ui.row().classes('w-full justify-center'):
    ui.label('Compresseur d\'Image Multi-Algorithmes').classes('text-h4')

with ui.card().classes('w-full shadow-lg'):
    ui.upload(on_upload=handle_upload, label="Choisir une image").classes('w-full')

with ui.row().classes('w-full justify-around mt-4'):
    with ui.column().classes('items-center'):
        ui.label('Aperçu Original')
        original_preview = ui.image().classes('w-64 border')
        
    with ui.column().classes('items-center'):
        ui.label('Résultat')
        result_display = ui.image().classes('w-64 border')

with ui.row().classes('w-full justify-center gap-4 mt-4'):
    ui.button('Lanczos', on_click=lambda: process_image('Compressor.py')).props('color=blue')
    ui.button('Octree', on_click=lambda: process_image('Octree.py')).props('color=green')
    ui.button('MedianCut', on_click=lambda: process_image('MedianCut.py')).props('color=orange')

ui.run()