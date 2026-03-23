import numpy as np
import matplotlib.pyplot as plt
from PIL import Image


import sys

if len(sys.argv) > 1:
    image_path = sys.argv[1]

else:
    raise ValueError("Aucun fichier fourni")

nb_colour = int(sys.argv[2]) if len(sys.argv) > 2 else 10

image = Image.open(image_path).convert("RGB")  # force RGB, évite RGBA ou palette

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

    h,w,c = img.shape

    # modifie les dimension pour avoir juste une ligne (47000 case au lieu de 188*250 cases

    flat_img = img.reshape(-1, 3)

    # contiendra toutes les boxes (pixel,indice)

    boxes = []
    for i in range(len(flat_img)):
        boxes.append((flat_img[i],i))

    boxes = [boxes]

    """
    while depht > 0:

        depht -= 1


        # calcul de la range pour chaques pixels

        for box in boxes:

            min_red = 255
            min_green = 255
            min_blue = 255

            max_red = 0
            max_green = 0
            max_blue = 0



            for pxl in box:


                if pxl[0][RED] < min_red:
                    min_red = pxl[0][RED]
                if pxl[0][GREEN] < min_green:
                    min_green = pxl[0][GREEN]
                if pxl[0][BLUE] < min_blue:
                    min_blue = pxl[0][BLUE]
                if pxl[0][RED] > max_red:
                    max_red = pxl[0][RED]
                if pxl[0][GREEN] > max_green:
                    max_green = pxl[0][GREEN]
                if pxl[0][BLUE] > max_blue:
                    max_blue = pxl[0][BLUE]

            red_rg = max_red - min_red
            green_rg = max_green - min_green
            blue_rg = max_blue - min_blue

            # get the max range

            max_rgb = max(red_rg, green_rg, blue_rg)

            # choisir la couleur avec la range la plus grande et trie de la box associé

            if max_rgb == red_rg:
                box = sort_by(RED,box)
            elif max_rgb == green_rg:
                box = sort_by(GREEN,box)
            else:
                box = sort_by(BLUE,box)

        # divise en 2 la box, du coup 1 couleur en plus

        for i in range(len(boxes)):

            box2split = boxes.pop(0)

            median = len(box2split) // 2

            box1, box2 = box2split[:median],box2split[median:]

            boxes.append(box1)
            boxes.append(box2)
    """

    while len(boxes) < 2 ** nb_colour:


        # trier les boîtes
        boxes.sort(key=compute_range, reverse=True)

        box = boxes.pop(0)

        # trouver la meilleure dimension
        color = compute_range_and_color(box)

        # tri
        box = sort_by(color, box)

        # split
        median = len(box) // 2
        box1 = box[:median]
        box2 = box[median:]

        boxes.append(box1)
        boxes.append(box2)

    palette = []

    # déterminer les couleur de la nouvelle palette

    for box in boxes:

        R = 0
        V = 0
        B = 0

        nb_pxl = len(box)

        for pxl in box:

            R += int(pxl[0][RED])
            V += int(pxl[0][GREEN])
            B += int(pxl[0][BLUE])

        final_pxl = [int(R/nb_pxl), int(V/nb_pxl), int(B/nb_pxl)]
        palette.append((final_pxl,box))


    #remplacer les pixels d'origine par la bonne couleur de la palette

    for color_box in palette:

        for pxl in color_box[1]:

            flat_img[pxl[1]] = color_box[0]

    new_img = flat_img.reshape(h, w, c)
    return new_img

# load image
#image = np.array(Image.open("images.png").convert("RGB"))
#print("image dimensions : ", image.shape)    # RGB


compressed_img = median_cut(image)

plt.imshow(compressed_img)
plt.show()