from nicegui import ui, app
import subprocess
import os
import time
import tempfile
from PIL import Image

# ──────────────────────────────────────────────
#  CONFIGURATION — ajouter/retirer des algos ici
# ──────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_FILE = "logo.jpg"

SIZE_ALGOS = {
    "Lanczos": {
        "script": "Compressor.py",
        "output": "output_lanczos.jpg",
        "params": [
            {"label": "Width",  "default": 250, "min": 1, "key": "w"},
            {"label": "Height", "default": 250, "min": 1, "key": "h"},
            {"label": "a",      "default": 6,   "min": 1, "key": "a"},
        ],
    },
    # ← ajouter un algo de taille ici
}

COLOR_ALGOS = {
    "Octree": {
        "script": "octree.py",
        "output": "output_octree.png",
        "params": [
            {"label": "Nb couleurs", "default": 256, "min": 8, "type": "number"},
        ],
    },
    "Median Cut": {
        "script": "median-cut.py",
        "output": "output_mediancut.png",
        "params": [
            {"label": "Nb couleurs", "default": 64, "type": "select",
             "options": [2, 4, 8, 16, 32, 64, 128, 256]},
        ],
    },
    # ← ajouter un algo de couleur ici
}

# ──────────────────────────────────────────────
#  STATE
# ──────────────────────────────────────────────

state = {
    "uploaded_path": None,
    "original_w": None,
    "original_h": None,
    "ratio_locked": True,
    "updating_ratio": False,   # verrou anti-boucle
}

algo_widgets = {}   # { algo_name: [widget, ...] }

# ──────────────────────────────────────────────
#  SETUP
# ──────────────────────────────────────────────

app.add_static_files('/static', BASE_DIR)
ui.add_head_html('<link rel="stylesheet" href="/static/GUI_Style_INSA.css">')
ui.dark_mode(False)

# ──────────────────────────────────────────────
#  CORE
# ──────────────────────────────────────────────

def run_script(script_name, input_path, output_name, args):
    script_path = os.path.join(BASE_DIR, script_name)
    output_path = os.path.join(BASE_DIR, output_name)
    result = subprocess.run(
        ['python', script_path, input_path] + [str(a) for a in args],
        check=True, capture_output=True, text=True, cwd=BASE_DIR,
    )
    print(result.stdout)
    return output_path if os.path.exists(output_path) else None


def get_param_values(algo_name):
    return [int(w.value) for w in algo_widgets.get(algo_name, [])]


def extract_palette(image_path, max_colors=256):
    img = Image.open(image_path).convert("RGB")
    colors = img.getcolors(maxcolors=img.width * img.height)
    if not colors:
        return []
    colors.sort(key=lambda x: -x[0])
    palette, seen = [], set()
    for count, rgb in colors:
        if rgb not in seen:
            seen.add(rgb)
            palette.append(rgb)
        if len(palette) >= max_colors:
            break
    return palette


def render_palette(palette):
    palette_container.clear()
    if not palette:
        with palette_container:
            ui.label("—").classes('text-caption')
        return
    with palette_container:
        ui.label(f"{len(palette)} couleur(s)").classes('text-caption')
        with ui.column().classes('gap-0 w-full').style('max-height: 320px; overflow-y: auto;'):
            for r, g, b in palette:
                hex_val = f"#{r:02X}{g:02X}{b:02X}"
                with ui.row().classes('palette-row w-full'):
                    ui.element('div').classes('palette-swatch').style(f'background-color: {hex_val};')
                    ui.label(hex_val).style('min-width: 68px; font-weight: 500;')
                    ui.label(f"rgb({r}, {g}, {b})").classes('palette-rgb')


def process():
    if not state["uploaded_path"]:
        ui.notify("Veuillez d'abord charger une image", type='negative')
        return

    current_path = state["uploaded_path"]
    final_output = None
    color_output  = None

    # ── Étape 1 : taille ──
    selected_size = size_select.value
    if selected_size and selected_size in SIZE_ALGOS and selected_size != '— aucun —':
        algo = SIZE_ALGOS[selected_size]
        args = get_param_values(selected_size)
        if selected_size == "Lanczos":
            w, h = args[0], args[1]
            if w > state["original_w"] or h > state["original_h"]:
                ui.notify(
                    f"Dimensions ({w}×{h}) supérieures à l'originale "
                    f"({state['original_w']}×{state['original_h']})",
                    type='negative',
                )
                return
        try:
            out = run_script(algo["script"], current_path, algo["output"], args)
            if out:
                current_path = out
                final_output = out
            else:
                ui.notify(f"{algo['output']} introuvable après {selected_size}", type='warning')
                return
        except subprocess.CalledProcessError as e:
            ui.notify(f"Erreur {selected_size} : {e.stderr[-200:]}", type='negative')
            return

    # ── Étape 2 : couleurs ──
    selected_color = color_select.value
    if selected_color and selected_color in COLOR_ALGOS and selected_color != '— aucun —':
        algo = COLOR_ALGOS[selected_color]
        args = get_param_values(selected_color)
        if selected_color == "Octree" and args[0] < 8:
            ui.notify("Minimum 8 couleurs pour Octree", type='negative')
            return
        try:
            out = run_script(algo["script"], current_path, algo["output"], args)
            if out:
                final_output = out
                color_output  = out
            else:
                ui.notify(f"{algo['output']} introuvable après {selected_color}", type='warning')
                return
        except subprocess.CalledProcessError as e:
            ui.notify(f"Erreur {selected_color} : {e.stderr[-200:]}", type='negative')
            return

    if final_output:
        # Récupère les dimensions réelles de l'image produite
        out_img = Image.open(final_output)
        out_w, out_h = out_img.size
        show_result(f'/static/{os.path.basename(final_output)}?t={time.time()}', out_w, out_h)
        if color_output:
            render_palette(extract_palette(color_output))
        else:
            palette_container.clear()
        ui.notify("Traitement terminé ✓", type='positive')
    else:
        ui.notify("Aucun algorithme sélectionné", type='warning')


def show_result(src, w, h):
    state['last_result_src'] = src
    ui.run_javascript(f'''
        const img = document.getElementById("result-img");
        if (img) {{
            img.src = "{src}";
            img.style.display = "block";
        }}
    ''')


# ──────────────────────────────────────────────
#  UPLOAD
# ──────────────────────────────────────────────

def handle_upload(e):
    suffix = os.path.splitext(e.file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(e.file._data)
        state["uploaded_path"] = tmp.name

    img = Image.open(state["uploaded_path"])
    state["original_w"], state["original_h"] = img.size

    # Pré-remplir W et H Lanczos
    _set_lanczos_dims(state["original_w"], state["original_h"])

    app.add_static_files('/tmp_uploads', os.path.dirname(state["uploaded_path"]))
    original_preview.set_source(f'/tmp_uploads/{os.path.basename(state["uploaded_path"])}')
    palette_container.clear()
    ui.notify(f"{e.file.name}  —  {state['original_w']}×{state['original_h']}", type='positive')


def _set_lanczos_dims(w, h):
    """Remplit les champs Width/Height de Lanczos sans déclencher le callback ratio."""
    if "Lanczos" not in algo_widgets or len(algo_widgets["Lanczos"]) < 2:
        return
    state["updating_ratio"] = True
    algo_widgets["Lanczos"][0].value = w
    algo_widgets["Lanczos"][1].value = h
    state["updating_ratio"] = False


# ──────────────────────────────────────────────
#  RATIO LOCK
# ──────────────────────────────────────────────

def on_width_change(value):
    if state["updating_ratio"] or not state["ratio_locked"]:
        return
    if not state["original_w"] or not value:
        return
    ratio = state["original_h"] / state["original_w"]
    new_h = max(1, round(int(value) * ratio))
    _set_lanczos_dims(int(value), new_h)


def on_height_change(value):
    if state["updating_ratio"] or not state["ratio_locked"]:
        return
    if not state["original_h"] or not value:
        return
    ratio = state["original_w"] / state["original_h"]
    new_w = max(1, round(int(value) * ratio))
    _set_lanczos_dims(new_w, int(value))


def on_ratio_toggle(value):
    state["ratio_locked"] = value


# ──────────────────────────────────────────────
#  FULLSCREEN
# ──────────────────────────────────────────────

def show_fullscreen(src):
    if not src:
        return
    dialog = ui.dialog().props('full-width')
    zoom = {'value': 1}
    pos  = {'x': 0, 'y': 0}
    drag = {'active': False}

    with dialog:
        with ui.card().classes('m-auto').style(
            'width:95vw; height:95vh; max-width:none; background:#111;'
            'display:flex; align-items:center; justify-content:center;'
            'overflow:hidden; position:relative;'
        ):
            # Vraie balise <img> — pas de q-img, zoom/drag géré en JS pur
            ui.html(f'''
                <img id="fs-img" src="{src}"
                     style="max-width:100%; max-height:100%; object-fit:contain;
                            transform-origin:center; cursor:grab; user-select:none;
                            transition: none;"
                     draggable="false" />
                <span style="position:absolute;bottom:12px;left:50%;transform:translateX(-50%);
                             color:rgba(255,255,255,0.35);font-size:0.65rem;letter-spacing:0.1em;
                             font-family:monospace;pointer-events:none;">
                  Double-clic pour réinitialiser · Scroll pour zoomer
                </span>
            ''')
            ui.button(icon='close', on_click=dialog.close).props('round flat color=white').classes(
                'absolute top-2 right-2 z-50'
            )

        # Zoom + drag entièrement en JS sur la vraie <img>
        ui.run_javascript('''
            (function() {
                const el = document.getElementById("fs-img");
                if (!el) return;
                let scale = 1, tx = 0, ty = 0;
                let dragging = false, sx = 0, sy = 0;

                function apply() {
                    el.style.transform = `scale(${scale}) translate(${tx}px, ${ty}px)`;
                }
                function clamp() {
                    const mx = (scale - 1) * el.naturalWidth  / 2;
                    const my = (scale - 1) * el.naturalHeight / 2;
                    tx = Math.max(-mx, Math.min(tx, mx));
                    ty = Math.max(-my, Math.min(ty, my));
                }

                el.addEventListener("wheel", e => {
                    e.preventDefault();
                    const old = scale;
                    scale = Math.max(1, Math.min(scale * (e.deltaY < 0 ? 1.1 : 1/1.1), 10));
                    tx *= scale / old; ty *= scale / old;
                    clamp(); apply();
                }, { passive: false });

                el.addEventListener("mousedown", e => {
                    dragging = true; sx = e.clientX; sy = e.clientY;
                    el.style.cursor = "grabbing";
                });
                window.addEventListener("mousemove", e => {
                    if (!dragging) return;
                    tx += (e.clientX - sx) / scale;
                    ty += (e.clientY - sy) / scale;
                    sx = e.clientX; sy = e.clientY;
                    clamp(); apply();
                });
                window.addEventListener("mouseup", () => {
                    dragging = false; el.style.cursor = "grab";
                });
                el.addEventListener("dblclick", () => {
                    scale = 1; tx = 0; ty = 0; apply();
                });
            })();
        ''')

    dialog.open()


# ──────────────────────────────────────────────
#  PARAM WIDGETS
# ──────────────────────────────────────────────

def build_param_widgets(algo_name, params):
    widgets = []
    for p in params:
        key = p.get("key", "")
        if p.get("type") == "select":
            w = ui.select(label=p["label"], options=p["options"], value=p["default"]).classes('w-36')
        elif key == "w":
            w = ui.number(label=p["label"], value=p["default"], min=p.get("min", 1), format='%d',
                          on_change=lambda e: on_width_change(e.value)).classes('w-36')
        elif key == "h":
            w = ui.number(label=p["label"], value=p["default"], min=p.get("min", 1), format='%d',
                          on_change=lambda e: on_height_change(e.value)).classes('w-36')
        else:
            w = ui.number(label=p["label"], value=p["default"], min=p.get("min", 1), format='%d').classes('w-36')
        widgets.append(w)
    algo_widgets[algo_name] = widgets


def on_size_change(value):
    size_params_container.clear()
    if value and value in SIZE_ALGOS and value != '— aucun —':
        with size_params_container:
            build_param_widgets(value, SIZE_ALGOS[value]["params"])
            # Affiche le toggle ratio lock juste après Width/Height
            if value == "Lanczos":
                with ui.row().classes('items-center gap-2 mt-1'):
                    ui.checkbox('Garder le ratio', value=state["ratio_locked"],
                                on_change=lambda e: on_ratio_toggle(e.value)).classes('text-caption')


def on_color_change(value):
    color_params_container.clear()
    if value and value in COLOR_ALGOS and value != '— aucun —':
        with color_params_container:
            build_param_widgets(value, COLOR_ALGOS[value]["params"])


# ──────────────────────────────────────────────
#  UI
# ──────────────────────────────────────────────

# Sidebar rouge (sans logo)
ui.add_body_html('''
<div class="pir-sidebar"></div>
''')

with ui.column().classes('pir-main w-full gap-0'):

    with ui.row().classes('items-center gap-3 pt-6 pb-2'):
        ui.html(f'<img src="/static/{LOGO_FILE}" style="height:44px;width:auto;" />')
        ui.label("P.I.R — Image Reduction").classes('text-h4').style('margin:0;padding:0;')

    # Upload
    with ui.row().classes('w-full justify-center my-4'):
        ui.upload(
            on_upload=handle_upload,
            label="Choisir une image",
            auto_upload=True,
            max_file_size=10_000_000,
        ).props('centered').classes('w-72')

    # Prévisualisations
    with ui.row().classes('w-full gap-4'):
        with ui.column().classes('flex-1 items-center gap-1'):
            ui.label('Original').classes('text-caption')
            # object-contain : affiche l'image entière dans la boîte, ratio respecté
            original_preview = ui.image().classes('w-full h-[55vh] object-contain')

        with ui.column().classes('flex-1 items-center gap-1'):
            ui.label('Résultat  —  clic pour zoomer').classes('text-caption')
            # Vraie balise <img> — pas de q-img, pas de background-size:cover
            result_container = ui.element('div').style(
                'width:100%; height:55vh; background:#111; display:flex;'
                'align-items:center; justify-content:center;'
                'border:1px solid var(--grey-light); cursor:pointer; overflow:hidden;'
            )
            with result_container:
                result_html = ui.html('<img id="result-img" src="" style="max-width:100%;max-height:100%;object-fit:contain;display:none;" />')
            result_container.on('click', lambda: show_fullscreen(state.get('last_result_src', '')))

    # Contrôles
    with ui.row().classes('w-full gap-4 mt-6 items-start'):

        # Taille
        with ui.card().classes('flex-1 p-4 gap-3'):
            ui.label('Taille').classes('text-bold text-lg')
            size_select = ui.select(
                label='Algorithme',
                # None = aucun sélectionné (valeur sentinelle)
                options=['— aucun —'] + list(SIZE_ALGOS.keys()),
                value='— aucun —',
                on_change=lambda e: on_size_change(e.value),
            ).classes('w-full')
            size_params_container = ui.column().classes('gap-2')

        # Couleurs
        with ui.card().classes('flex-1 p-4 gap-3'):
            ui.label('Couleurs').classes('text-bold text-lg')
            color_select = ui.select(
                label='Algorithme',
                options=['— aucun —'] + list(COLOR_ALGOS.keys()),
                value='— aucun —',
                on_change=lambda e: on_color_change(e.value),
            ).classes('w-full')
            color_params_container = ui.column().classes('gap-2')

        # Lancer
        with ui.card().classes('p-4 flex items-center justify-center'):
            ui.button('Lancer', on_click=process).classes('px-10 py-3 text-base')

    # Palette
    with ui.card().classes('w-full p-4 mt-4'):
        ui.label('Palette résultat').classes('text-bold text-lg')
        palette_container = ui.column().classes('w-full gap-0')
        with palette_container:
            ui.label("Lance une réduction de couleurs pour voir la palette.").classes('text-caption')

ui.run()