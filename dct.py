from PIL import Image
import numpy as np
from scipy.fftpack import dct, idct
import os

#HOW TO USE:
# bash# Drop any image in your project folder, rename it test_image.png
# python dct.py
# # → produces dct_output.png + dct_comparison.png (side by side)

# Change quality level in the script:
# compress_image("your_photo.jpg", "output.png", quality=10)  # heavy compression
# compress_image("your_photo.jpg", "output.png", quality=80)  # near-lossless

# Run the benchmark (great to show your teacher the quality/size trade-off):
## Uncomment the last line in __main__
# benchmark("your_photo.png", qualities=[5, 15, 30, 50, 75, 90])


LUMINANCE_QUANTIZATION_MATRIX = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68,109,103, 77],
    [24, 35, 55, 64, 81,104,113, 92],
    [49, 64, 78, 87,103,121,120,101],
    [72, 92, 95, 98,112,100,103, 99],
], dtype=np.float32)

CHROMINANCE_QUANTIZATION_MATRIX = np.array([
    [17, 18, 24, 47, 99, 99, 99, 99],
    [18, 21, 26, 66, 99, 99, 99, 99],
    [24, 26, 56, 99, 99, 99, 99, 99],
    [47, 66, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
    [99, 99, 99, 99, 99, 99, 99, 99],
], dtype=np.float32)


def dct2d(block: np.ndarray) -> np.ndarray:
    return dct(dct(block.T, norm="ortho").T, norm="ortho")


def idct2d(block: np.ndarray) -> np.ndarray:
    return idct(idct(block.T, norm="ortho").T, norm="ortho")


def scale_quantization_matrix(base_matrix: np.ndarray, quality: int) -> np.ndarray:
    quality = max(1, min(95, quality))
    if quality < 50:
        scale = 5000 / quality
    else:
        scale = 200 - 2 * quality
    scaled = np.floor((base_matrix * scale + 50) / 100).astype(np.float32)
    scaled = np.clip(scaled, 1, 255)
    return scaled


def _pad_channel(channel: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
    h, w = channel.shape
    ph = (8 - h % 8) % 8
    pw = (8 - w % 8) % 8
    padded = np.pad(channel, ((0, ph), (0, pw)), mode="edge")
    return padded, (h, w)


def compress_channel(
    channel: np.ndarray,
    q_matrix: np.ndarray,
) -> tuple[np.ndarray, tuple[int, int]]:
    padded, original_shape = _pad_channel(channel.astype(np.float32))
    h, w = padded.shape
    coeffs = np.zeros_like(padded)

    for row in range(0, h, 8):
        for col in range(0, w, 8):
            block = padded[row:row+8, col:col+8] - 128.0
            dct_block = dct2d(block)
            coeffs[row:row+8, col:col+8] = np.round(dct_block / q_matrix)

    return coeffs, original_shape


def decompress_channel(
    coeffs: np.ndarray,
    q_matrix: np.ndarray,
    original_shape: tuple[int, int],
) -> np.ndarray:
    h, w = coeffs.shape
    reconstructed = np.zeros_like(coeffs)

    for row in range(0, h, 8):
        for col in range(0, w, 8):
            block = coeffs[row:row+8, col:col+8] * q_matrix
            reconstructed[row:row+8, col:col+8] = idct2d(block) + 128.0

    oh, ow = original_shape
    return np.clip(reconstructed[:oh, :ow], 0, 255).astype(np.uint8)


def compress_image(
    input_path: str,
    output_path: str,
    quality: int = 50,
) -> dict:
    img = Image.open(input_path).convert("RGB")
    width, height = img.size
    print(f"Image  : {width} × {height}  ({width * height:,} pixels)")
    print(f"Quality: {quality}/95\n")

    ycbcr = img.convert("YCbCr")
    y_ch, cb_ch, cr_ch = ycbcr.split()

    y  = np.array(y_ch,  dtype=np.float32)
    cb = np.array(cb_ch, dtype=np.float32)
    cr = np.array(cr_ch, dtype=np.float32)

    q_luma   = scale_quantization_matrix(LUMINANCE_QUANTIZATION_MATRIX,   quality)
    q_chroma = scale_quantization_matrix(CHROMINANCE_QUANTIZATION_MATRIX, quality)

    print("  [1/3] Compressing Y  channel …", end=" ", flush=True)
    y_coeffs,  y_shape  = compress_channel(y,  q_luma)
    print("done")

    print("  [1/3] Compressing Cb channel …", end=" ", flush=True)
    cb_coeffs, cb_shape = compress_channel(cb, q_chroma)
    print("done")

    print("  [1/3] Compressing Cr channel …", end=" ", flush=True)
    cr_coeffs, cr_shape = compress_channel(cr, q_chroma)
    print("done")

    print("  [2/3] Reconstructing channels …", end=" ", flush=True)
    y_rec  = decompress_channel(y_coeffs,  q_luma,   y_shape)
    cb_rec = decompress_channel(cb_coeffs, q_chroma, cb_shape)
    cr_rec = decompress_channel(cr_coeffs, q_chroma, cr_shape)
    print("done")

    print("  [3/3] Saving output image …", end=" ", flush=True)
    y_img  = Image.fromarray(y_rec,  mode="L")
    cb_img = Image.fromarray(cb_rec, mode="L")
    cr_img = Image.fromarray(cr_rec, mode="L")

    reconstructed_ycbcr = Image.merge("YCbCr", (y_img, cb_img, cr_img))
    reconstructed_rgb   = reconstructed_ycbcr.convert("RGB")
    reconstructed_rgb.save(output_path, optimize=True)
    print("done\n")

    raw_size      = width * height * 3
    original_size = os.path.getsize(input_path)
    new_size      = os.path.getsize(output_path)

    nonzero_coeffs = (
        int(np.count_nonzero(y_coeffs))
        + int(np.count_nonzero(cb_coeffs))
        + int(np.count_nonzero(cr_coeffs))
    )
    theoretical_size = nonzero_coeffs * 2

    stats = {
        "width":              width,
        "height":             height,
        "quality":            quality,
        "raw_size":           raw_size,
        "original_size":      original_size,
        "reconstructed_size": new_size,
        "theoretical_size":   theoretical_size,
        "nonzero_coeffs":     nonzero_coeffs,
        "total_coeffs":       y_coeffs.size + cb_coeffs.size + cr_coeffs.size,
        "zero_ratio":         1 - nonzero_coeffs / (y_coeffs.size + cb_coeffs.size + cr_coeffs.size),
    }

    print(f"  Raw RGB (uncompressed) : {raw_size:>12,} bytes")
    print(f"  Original file          : {original_size:>12,} bytes")
    print(f"  Reconstructed PNG      : {new_size:>12,} bytes")
    print(f"  Theoretical DCT size   : {theoretical_size:>12,} bytes")
    print(f"  Zero DCT coefficients  : {stats['zero_ratio']*100:.1f}%")
    print(f"  vs original file       : {(1 - new_size/original_size)*100:+.1f}%")

    return stats


def compare_images(original_path: str, compressed_path: str, out_path: str):
    orig = Image.open(original_path).convert("RGB")
    comp = Image.open(compressed_path).convert("RGB")

    if orig.height != comp.height:
        comp = comp.resize(orig.size, Image.LANCZOS)

    comparison = Image.new("RGB", (orig.width + comp.width + 10, orig.height), (40, 40, 40))
    comparison.paste(orig, (0, 0))
    comparison.paste(comp, (orig.width + 10, 0))
    comparison.save(out_path)
    print(f"\n  Side-by-side comparison saved → {out_path}")


def benchmark(input_path: str, qualities: list[int] = [5, 15, 30, 50, 75, 90]):
    print(f"\n{'='*65}")
    print(f"  BENCHMARK : {os.path.basename(input_path)}")
    print(f"{'='*65}")
    print(f"  {'Quality':>7}  {'Zero coeff %':>12}  {'Theor. size':>12}  {'Output size':>12}")
    print(f"  {'-'*7}  {'-'*12}  {'-'*12}  {'-'*12}")

    for q in qualities:
        out = f"_bench_q{q:02d}.png"
        stats = compress_image(input_path, out, quality=q)
        print(
            f"  {q:>7}  "
            f"{stats['zero_ratio']*100:>11.1f}%  "
            f"{stats['theoretical_size']:>12,}  "
            f"{stats['reconstructed_size']:>12,}"
        )
        print()

    print(f"{'='*65}\n")


if __name__ == "__main__":
    INPUT  = "test_image.png"
    OUTPUT = "dct_output.png"

    stats = compress_image(INPUT, OUTPUT, quality=50)
    compare_images(INPUT, OUTPUT, "dct_comparison.png")

    # benchmark(INPUT, qualities=[5, 15, 30, 50, 75, 90])