from PIL import Image
from matplotlib import pyplot as plt

already_calculate_index = 0
total_pixel = 0

color_list = []

class Color:
    def __init__(self):
        self.red = 0
        self.green = 0
        self.blue = 0
    # Methods to compare two colors
    def __eq__(self, other):
        return self.red == other.red and self.green == other.green and self.blue == other.blue
    
    def __hash__(self):
        return hash((self.red, self.green, self.blue))


def add_color(r, g, b):
    c = Color()
    c.red = r
    c.green = g
    c.blue = b
    color_list.append(c)

# ------------------------------------

# From two color, calcul distance between them
def get_distance_color(color_a, color_b):
    dist_r = abs(color_a.red - color_b.red)
    dist_g = abs(color_a.green - color_b.green)
    dist_b = abs(color_a.blue - color_b.blue)
    return dist_r + dist_g + dist_b

# Function who takes a color and return the nearest color from colorList
def nearest_color(color):
    nearest_color = Color()
    best_distance = -1
    for c in color_list:
        # Found a better color
        new_distance = get_distance_color(color, c)
        if (best_distance == -1 or new_distance < best_distance) :
            nearest_color = c
            best_distance = new_distance
    return nearest_color

# ---------------------------------

def algorithm(img):
    global total_pixel
    global already_calculate_index

    color_already_calculated = {} # A dict (same than hashmap) is complexity O(n), so it's more efficient to keep already calculated values
    pixels = list(img.getdata())
    width, height = img.size

    new_pixels = list()

    print(pixels[0])
    print(f"Largeur : {width}, Hauteur : {height}")

    for p in pixels:
        total_pixel += 1
        c = Color()
        c.red = p[0]
        c.green = p[1]
        c.blue = p[2]

        # Colors was already calculated
        if color_already_calculated.__contains__(c):
            #print("hey")
            new_color = color_already_calculated.get(c)
            new_pixels.append((new_color.red, new_color.green, new_color.blue))
            already_calculate_index = already_calculate_index + 1
        
        # if not, we have to calculate and stock value
        else:
            new_color = nearest_color(c)
            color_already_calculated[c] = new_color
            new_pixels.append((new_color.red, new_color.green, new_color.blue))

    img_return = Image.new("RGB", (width, height))
    img_return.putdata(new_pixels)

    return img_return

# https://mthevenin.github.io/stata_graphiques/formation/formation31.html (S2)
def default_palet():
    add_color(26, 71, 111)
    add_color(144, 53, 59)
    add_color(85, 117, 47)
    add_color(227, 126, 0)
    add_color(110, 142, 132)

    add_color(193, 5, 52)
    add_color(147, 141, 210)
    add_color(202, 194, 126)
    add_color(160, 82, 45)
    add_color(123, 146, 168)

    add_color(45, 109, 102)
    add_color(156, 136, 71)
    add_color(191, 161, 156)
    add_color(255, 210, 0)
    add_color(217, 230, 235)


# ---------------------------------------------------------------------------

default_palet()

default_image = Image.open('images_test/canard.jpg')
new_image = algorithm(default_image)

print(f"Déjà calculé :{already_calculate_index}/{total_pixel}")

fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    
axes[0].imshow(default_image)
axes[0].set_title("Image par défaut")
axes[0].axis("off")

axes[1].imshow(new_image)
axes[1].set_title("Image après application de la palette")
axes[1].axis("off")

plt.tight_layout()
plt.show()