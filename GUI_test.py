from nicegui import ui
import subprocess
import os
import time

OUTPUT_IMAGE = "output.jpg"

image = ui.image().classes('w-96')

def run_Lanczos(file_path):
    # exécute ton script avec l'image uploadée
    subprocess.run(['python', 'Compressor.py', file_path])

    # recharge l'image générée (avec timestamp pour éviter le cache)
    if os.path.exists(OUTPUT_IMAGE):
        image.set_source(f"{OUTPUT_IMAGE}?t={time.time()}")

def handle_upload(e):
    # e.file.path contient le chemin temporaire du fichier uploadé
    ui.notify(f"Uploaded {e.file.name}")
    run_Lanczos(e.file.path)

ui.upload(on_upload=handle_upload).classes('max-w-full')

# Si tu as d'autres scripts
def run_Octree():
    subprocess.run(['python','Octree.py'])
    if os.path.exists(OUTPUT_IMAGE):
        image.set_source(f"{OUTPUT_IMAGE}?t={time.time()}")

def run_MedianCut():
    subprocess.run(['python','MedianCut.py'])
    if os.path.exists(OUTPUT_IMAGE):
        image.set_source(f"{OUTPUT_IMAGE}?t={time.time()}")

ui.button('Run compressor with Lanczos reduction', on_click=lambda: None)  # plus besoin
ui.button('Run compressor with Octree reduction', on_click=run_Octree)
ui.button('Run compressor with MedianCut reduction', on_click=run_MedianCut)

ui.run()