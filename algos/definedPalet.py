import os
import sys
from PIL import Image


class Color:
    def __init__(self, red=0, green=0, blue=0):
        self.red = red
        self.green = green
        self.blue = blue

    def __eq__(self, other):
        return (
            isinstance(other, Color)
            and self.red == other.red
            and self.green == other.green
            and self.blue == other.blue
        )

    def __hash__(self):
        return hash((self.red, self.green, self.blue))


def parse_color_arg(arg):
    if isinstance(arg, str) and arg.startswith('#'):
        hex_value = arg.lstrip('#')
        if len(hex_value) == 6:
            return tuple(int(hex_value[i:i+2], 16) for i in (0, 2, 4))
    if isinstance(arg, str) and ',' in arg:
        parts = [int(p.strip()) for p in arg.split(',') if p.strip()]
        if len(parts) == 3:
            return tuple(parts)
    raise ValueError(f"Couleur invalide : {arg}")


def build_palette(color_args):
    palette = []
    for arg in color_args:
        if arg is None:
            continue
        try:
            color = parse_color_arg(arg)
        except ValueError:
            continue
        palette.append(color)
    return palette


def default_palette():
    return [
        (26, 71, 111),
        (144, 53, 59),
        (85, 117, 47),
        (227, 126, 0),
        (110, 142, 132),
        (193, 5, 52),
        (147, 141, 210),
        (202, 194, 126),
        (160, 82, 45),
        (123, 146, 168),
        (45, 109, 102),
        (156, 136, 71),
        (191, 161, 156),
        (255, 210, 0),
        (217, 230, 235),
    ]


def get_distance_color(color_a, color_b):
    return abs(color_a.red - color_b.red) + abs(color_a.green - color_b.green) + abs(color_a.blue - color_b.blue)


def nearest_color(color, palette):
    best = None
    best_distance = None
    for r, g, b in palette:
        candidate = Color(r, g, b)
        distance = get_distance_color(color, candidate)
        if best_distance is None or distance < best_distance:
            best = candidate
            best_distance = distance
    return best


def algorithm(img, palette=None):
    if palette is None or len(palette) == 0:
        palette = default_palette()

    pixels = list(img.getdata())
    width, height = img.size
    new_pixels = []
    cache = {}

    for p in pixels:
        key = (p[0], p[1], p[2])
        if key in cache:
            nearest = cache[key]
        else:
            source_color = Color(*key)
            nearest = nearest_color(source_color, palette)
            cache[key] = nearest
        new_pixels.append((nearest.red, nearest.green, nearest.blue))

    result = Image.new('RGB', (width, height))
    result.putdata(new_pixels)
    return result


def main():
    if len(sys.argv) < 2:
        raise ValueError('Usage: python definedPalet.py <input_image> [#RRGGBB ...]')

    input_path = sys.argv[1]
    colors = sys.argv[2:]
    palette = build_palette(colors)
    if not palette:
        palette = default_palette()

    img = Image.open(input_path).convert('RGB')
    output_path = os.path.join(os.path.dirname(__file__), '..', 'output_images', 'output_definedpalette.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    result = algorithm(img, palette)
    result.save(output_path)
    print(output_path)


if __name__ == '__main__':
    main()