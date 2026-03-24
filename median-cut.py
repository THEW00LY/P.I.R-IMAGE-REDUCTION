import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import math as m
import heapq
import itertools

import sys

if len(sys.argv) > 1:
    image_path = sys.argv[1]

else:
    raise ValueError("Aucun fichier fourni")

nb_colour = int(sys.argv[2]) if len(sys.argv) > 2 else 10
nb_colour = int(m.log2(nb_colour))

image = np.array(Image.open(image_path).convert("RGB"))  # force RGB, évite RGBA ou palette

RED = 0
GREEN = 1
BLUE = 2

def sort_by(color, flat_img):

    return sorted(flat_img, key=lambda x: x[0][color])


def compute_range(box):
    reds = [p[0][RED] for p in box]
    greens = [p[0][GREEN] for p in box]
    blues = [p[0][BLUE] for p in box]

    range_r = max(reds) - min(reds)
    range_g = max(greens) - min(greens)
    range_b = max(blues) - min(blues)

    biggest_range = max(range_r, range_g, range_b)

    return biggest_range


def compute_range_and_color(box):
    reds = [p[0][RED] for p in box]
    greens = [p[0][GREEN] for p in box]
    blues = [p[0][BLUE] for p in box]

    ranges = [
        max(reds) - min(reds),
        max(greens) - min(greens),
        max(blues) - min(blues)
    ]

    color = np.argmax(ranges)
    return color

def median_cut(img, nb_colour):

    h, w, c = img.shape
    flat_img = img.reshape(-1, 3)

    def compute_range(indices):
        pixels = flat_img[indices]
        return np.max(pixels.max(axis=0) - pixels.min(axis=0))

    heap = []
    counter = itertools.count()  # 🔥 clé unique

    initial_indices = np.arange(len(flat_img))
    initial_range = compute_range(initial_indices)

    heapq.heappush(heap, (-initial_range, next(counter), initial_indices))

    print(f"Début du traitement pour {2**nb_colour} couleurs...", flush=True)

    while len(heap) < 2 ** nb_colour:

        _, _, indices = heapq.heappop(heap)
        pixels = flat_img[indices]

        ranges = pixels.max(axis=0) - pixels.min(axis=0)
        color = np.argmax(ranges)

        sorted_idx = indices[np.argsort(pixels[:, color])]

        median = len(sorted_idx) // 2
        box1 = sorted_idx[:median]
        box2 = sorted_idx[median:]

        heapq.heappush(heap, (-compute_range(box1), next(counter), box1))
        heapq.heappush(heap, (-compute_range(box2), next(counter), box2))

    palette = []
    for _, _, indices in heap:
        pixels = flat_img[indices]
        mean_color = pixels.mean(axis=0).astype(np.uint8)
        palette.append((mean_color, indices))

    for color, indices in palette:
        flat_img[indices] = color

    return flat_img.reshape(h, w, c)
# load image
#image = np.array(Image.open("images.png").convert("RGB"))
#print("image dimensions : ", image.shape)    # RGB


compressed_img = median_cut(image, nb_colour)
path = "output_mediancut.png"

Image.fromarray(compressed_img).save(path)

#plt.imshow(compressed_img)
#plt.show()