from nicegui import ui, app
import subprocess
import os
import time
import tempfile
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_LANCZOS   = os.path.join(BASE_DIR, "output_lanczos.jpg")
OUTPUT_OCTREE    = os.path.join(BASE_DIR, "output_octree.png")
OUTPUT_MEDIANCUT = os.path.join(BASE_DIR, "output_mediancut.png")
uploaded_image_path = None
original_w, original_h = None, None  # dimensions de l'image uploadée

app.add_static_files('/static', BASE_DIR)

def show_fullscreen(src):
    with ui.dialog() as dialog, ui.card().classes('w-full h-full'):
        with ui.row().classes('w-full justify-end'):
            ui.button(icon='close', on_click=dialog.close).props('flat round')
        ui.image(src).classes('w-full h-full object-contain')
    dialog.open()

def handle_upload(e):
    global uploaded_image_path, original_w, original_h
    suffix = os.path.splitext(e.file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(e.file._data)
        uploaded_image_path = tmp.name
    # Récupère les dimensions ici, quand l'image est dispo
    img = Image.open(uploaded_image_path)
    original_w, original_h = img.size
    lanczos_h.value = original_h
    lanczos_w.value = original_w
    app.add_static_files('/tmp_uploads', os.path.dirname(uploaded_image_path))
    original_preview.set_source(f'/tmp_uploads/{os.path.basename(uploaded_image_path)}')
    ui.notify(f"Image chargée : {e.file.name} ({original_w}x{original_h})", type='positive')

def process_lanczos():
    if not uploaded_image_path:
        ui.notify("Veuillez d'abord choisir une image", type='negative')
        return
    h = int(lanczos_h.value)
    w = int(lanczos_w.value)
    a = int(lanczos_a.value)
    # Vérification que c'est bien une réduction
    if h > original_h or w > original_w:
        ui.notify(f"Taille entrée ({w}x{h}) supérieure à l'originale ({original_w}x{original_h})", type='negative')
        return
    process_image('Compressor.py', OUTPUT_LANCZOS, [h, w, a])

def process_octree():
    n = int(octree_n.value)
    if n < 8:
        ui.notify("Minimum 8 couleurs pour Octree", type='negative')
        octree_n.value = 8
        return
    process_image('octree.py', OUTPUT_OCTREE, [n])

def process_image(script_name, output, args):
    if not uploaded_image_path:
        ui.notify("Veuillez d'abord choisir une image", type='negative')
        return
    script_path = os.path.join(BASE_DIR, script_name)
    try:
        result = subprocess.run(
            ['python', script_path, uploaded_image_path] + [str(a) for a in args],
            check=True,
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        print(f"stdout : {result.stdout}")
        if os.path.exists(output):
            result_display.set_source(f'/static/{os.path.basename(output)}?t={time.time()}')
            ui.notify("Succès ✓", type='positive')
        else:
            ui.notify(f"{os.path.basename(output)} introuvable", type='warning')
    except subprocess.CalledProcessError as e:
        print(f"stderr : {e.stderr}")
        ui.notify(f"Erreur : {e.stderr[-200:]}", type='negative')

# --- UI Layout ---
with ui.row().classes('w-full justify-center'):
    ui.label("P.I.R, Image reduction algorithms").classes('text-h4')

with ui.card().classes('w-full shadow-lg p-4'):
    ui.upload(
        on_upload=handle_upload,
        label="Cliquer pour choisir...",
        auto_upload=True,
        max_file_size=10_000_000
    ).props('flat bordered').classes('w-full')

with ui.row().classes('w-full justify-around mt-4'):
    with ui.column().classes('items-center'):
        ui.label('Aperçu Original')
        original_preview = ui.image().classes('w-64 border')
    with ui.column().classes('items-center'):
        ui.label('Résultat')
        result_display = ui.image().classes('w-64 border cursor-pointer')
        result_display.on('click', lambda: show_fullscreen(result_display.source))

# --- Paramètres et boutons ---
with ui.row().classes('w-full justify-around mt-4 items-start'):

    with ui.card().classes('p-4'):
        ui.label('Lanczos').classes('text-bold text-lg')
        lanczos_h = ui.number(label='Height', value=250, min=1, format='%d').classes('w-32')
        lanczos_w = ui.number(label='Width',  value=250, min=1, format='%d').classes('w-32')
        lanczos_a = ui.number(label='a',      value=6,   min=1, format='%d').classes('w-32')
        ui.button('Lancer', on_click=process_lanczos)

    with ui.card().classes('p-4'):
        ui.label('Octree').classes('text-bold text-lg')
        octree_n = ui.number(label='Nb couleurs', value=256, min=8, format='%d').classes('w-32')
        ui.button('Lancer', on_click=process_octree)

    with ui.card().classes('p-4'):
        ui.label('Median Cut').classes('text-bold text-lg')
        
        # On stocke le sélecteur dans une variable
        mediancut_n = ui.select(
            label='Nb couleurs',
            options=[2, 4, 8, 16, 32, 64, 128, 256],
            value=64
        ).classes('w-32')

        # La fonction lambda ira chercher .value au moment du clic
        ui.button('Lancer', on_click=lambda: process_image(
            'median-cut.py', 
            OUTPUT_MEDIANCUT,
            [int(mediancut_n.value)]  # Lecture dynamique ici
        ))

ui.run()