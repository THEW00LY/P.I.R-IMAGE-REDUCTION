from nicegui import ui, app
import subprocess
import os
import time
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_IMAGE = os.path.join(BASE_DIR, "output.jpg")
uploaded_image_path = None

# Permet à NiceGUI de servir les fichiers du dossier projet
app.add_static_files('/static', BASE_DIR)

def show_fullscreen(src):
    with ui.dialog() as dialog, ui.card().classes('w-full h-full'):
        with ui.row().classes('w-full justify-end'):
            ui.button(icon='close', on_click=dialog.close).props('flat round')
        ui.image(src).classes('w-full h-full object-contain')
    dialog.open()

def handle_upload(e):
    global uploaded_image_path
    suffix = os.path.splitext(e.file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(e.file._data)
        uploaded_image_path = tmp.name
    app.add_static_files('/tmp_uploads', os.path.dirname(uploaded_image_path))
    original_preview.set_source(f'/tmp_uploads/{os.path.basename(uploaded_image_path)}')
    ui.notify(f"Image chargée : {e.file.name}", type='positive')

def process_image(script_name):
    if not uploaded_image_path:
        ui.notify("Veuillez d'abord choisir une image", type='negative')
        return

    script_path = os.path.join(BASE_DIR, script_name)

    try:
        result = subprocess.run(
            ['python', script_path, uploaded_image_path],
            check=True,
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        print(f"stdout : {result.stdout}")

        if os.path.exists(OUTPUT_IMAGE):
            # /static/ sert les fichiers depuis BASE_DIR
            result_display.set_source(f'/static/output.jpg?t={time.time()}')
            ui.notify("Succès ✓", type='positive')
        else:
            ui.notify("output.jpg introuvable", type='warning')

    except subprocess.CalledProcessError as e:
        print(f"stderr : {e.stderr}")
        ui.notify(f"Erreur : {e.stderr[-200:]}", type='negative')

# --- UI Layout ---
with ui.row().classes('w-full justify-center'):
    ui.label("Compresseur d'Image Multi-Algorithmes").classes('text-h4')

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

with ui.row().classes('w-full justify-around mt-4'):
    ui.button("Lanczos",    on_click=lambda: process_image('Compressor.py'))
    ui.button("Octree",     on_click=lambda: process_image('Octree.py'))
    ui.button("Median Cut", on_click=lambda: process_image('MedianCut.py'))

ui.run()