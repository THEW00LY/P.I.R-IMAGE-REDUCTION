from PIL import Image
import os
import sys
import numpy
import math as m

if len(sys.argv) > 1:
    image_path = sys.argv[1]

else:
    raise ValueError("Aucun fichier fourni")

nb_colour = int(sys.argv[2]) if len(sys.argv) > 2 else 3

image = Image.open(image_path).convert("RGB")

class OctreeNode:
    __slots__ = (
        "level", "parent", "children", "is_leaf",
        "pixel_count", "red_sum", "green_sum", "blue_sum",
        "palette_index",
    )

    def __init__(self, level, parent):
        self.level = level
        self.parent = parent
        self.children = [None] * 8
        self.is_leaf = False
        self.pixel_count = 0
        self.red_sum = 0
        self.green_sum = 0
        self.blue_sum = 0
        self.palette_index = None

    def get_average_color(self):
        return (
            self.red_sum // self.pixel_count,
            self.green_sum // self.pixel_count,
            self.blue_sum // self.pixel_count,
        )


class OctreeQuantizer:
    MAX_DEPTH = 8

    def __init__(self, max_colors=256):
        self.max_colors = max_colors
        self.root = OctreeNode(0, None)
        self.levels = [set() for _ in range(self.MAX_DEPTH + 1)]
        self.leaf_count = 0

    @staticmethod
    def _octant_index(r, g, b, level):
        shift = 7 - level
        return (((r >> shift) & 1) << 2) | \
               (((g >> shift) & 1) << 1) | \
               ((b >> shift) & 1)

    def insert_color(self, r, g, b):
        node = self.root

        for level in range(self.MAX_DEPTH):
            if node.is_leaf:
                node.pixel_count += 1
                node.red_sum += r
                node.green_sum += g
                node.blue_sum += b
                return

            idx = self._octant_index(r, g, b, level)

            if node.children[idx] is None:
                child = OctreeNode(level + 1, node)
                node.children[idx] = child
                if level + 1 < self.MAX_DEPTH:
                    self.levels[level + 1].add(child)

            node = node.children[idx]

        if not node.is_leaf:
            self.leaf_count += 1
            node.is_leaf = True

        node.pixel_count += 1
        node.red_sum += r
        node.green_sum += g
        node.blue_sum += b

        while self.leaf_count > self.max_colors:
            self._reduce()

    def _reduce(self):
        for level in range(self.MAX_DEPTH - 1, 0, -1):
            if not self.levels[level]:
                continue

            node = self.levels[level].pop()
            merged_leaves = 0

            for i in range(8):
                child = node.children[i]
                if child is None:
                    continue
                node.red_sum   += child.red_sum
                node.green_sum += child.green_sum
                node.blue_sum  += child.blue_sum
                node.pixel_count += child.pixel_count
                if child.is_leaf:
                    merged_leaves += 1
                node.children[i] = None

            node.is_leaf = True

            if merged_leaves > 0:
                self.leaf_count -= (merged_leaves - 1)
            else:
                self.leaf_count += 1

            return

    def build_palette(self):
        palette = []
        self._collect_leaves(self.root, palette)
        return palette

    def _collect_leaves(self, node, palette):
        if node.is_leaf:
            node.palette_index = len(palette)
            palette.append(node.get_average_color())
            return
        for child in node.children:
            if child is not None:
                self._collect_leaves(child, palette)

    def get_palette_index(self, r, g, b):
        node = self.root
        for level in range(self.MAX_DEPTH):
            if node.is_leaf:
                return node.palette_index
            idx = self._octant_index(r, g, b, level)
            child = node.children[idx]
            if child is None:
                return node.palette_index if node.palette_index is not None else 0
            node = child
        return node.palette_index


def quantize_image(output_path, max_colors=256):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixels = img.load()

    print(f"Image : {width} x {height} ({width * height:,} pixels)")
    print(f"Target: {max_colors} colors\n")

    quantizer = OctreeQuantizer(max_colors=max_colors)
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            quantizer.insert_color(r, g, b)
        if (y + 1) % 100 == 0 or y == height - 1:
            pct = (y + 1) / height * 100
            print(f"\r  [1/3] Building octree … {pct:5.1f}%", end="", flush=True)
    print()

    palette = quantizer.build_palette()
    print(f"  [2/3] Palette ready   – {len(palette)} colors")

    if output_path.lower().endswith(".png") and max_colors <= 256:
        new_img = Image.new("P", (width, height))
        flat_palette = []
        for color in palette:
            flat_palette.extend(color)
        flat_palette.extend([0] * (768 - len(flat_palette)))
        new_img.putpalette(flat_palette)

        index_data = []
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                index_data.append(quantizer.get_palette_index(r, g, b))
            if (y + 1) % 100 == 0 or y == height - 1:
                pct = (y + 1) / height * 100
                print(f"\r  [3/3] Mapping pixels  … {pct:5.1f}%", end="", flush=True)
        print()
        new_img.putdata(index_data)
        new_img.save(output_path, optimize=True)
    else:
        new_img = Image.new("RGB", (width, height))
        new_pixels = new_img.load()
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                idx = quantizer.get_palette_index(r, g, b)
                new_pixels[x, y] = palette[idx]
            if (y + 1) % 100 == 0 or y == height - 1:
                pct = (y + 1) / height * 100
                print(f"\r  [3/3] Mapping pixels  … {pct:5.1f}%", end="", flush=True)
        print()
        if output_path.lower().endswith(".png"):
            new_img.save(output_path, optimize=True)
        else:
            new_img.save(output_path, quality=75, optimize=True)

    raw_size = width * height * 3
    original_size = os.path.getsize(image_path)
    new_size = os.path.getsize(output_path)
    saving_vs_raw = (1 - new_size / raw_size) * 100
    saving_vs_orig = (1 - new_size / original_size) * 100

    print(f"\n  Raw RGB  : {raw_size:>10,} bytes  (uncompressed)")
    print(f"  Original : {original_size:>10,} bytes")
    print(f"  Reduced  : {new_size:>10,} bytes")
    print(f"  vs Raw   : {saving_vs_raw:.1f}%")
    print(f"  vs Orig  : {saving_vs_orig:.1f}%")


if __name__ == "__main__":
    max_colors = int(sys.argv[2]) if len(sys.argv) > 2 else 256
    quantize_image("output_octree.png", max_colors=max_colors)
