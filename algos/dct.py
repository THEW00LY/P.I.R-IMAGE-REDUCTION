import sys
import os

from PIL import Image
import numpy as np
from scipy.fftpack import dct, idct


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
    quality: int,
) -> dict:
    img = Image.open(input_path).convert("RGB")
    ycbcr = img.convert("YCbCr")
    y_ch, cb_ch, cr_ch = ycbcr.split()

    y  = np.array(y_ch,  dtype=np.float32)
    cb = np.array(cb_ch, dtype=np.float32)
    cr = np.array(cr_ch, dtype=np.float32)

    q_luma   = scale_quantization_matrix(LUMINANCE_QUANTIZATION_MATRIX,   quality)
    q_chroma = scale_quantization_matrix(CHROMINANCE_QUANTIZATION_MATRIX, quality)

    y_coeffs,  y_shape  = compress_channel(y,  q_luma)
    cb_coeffs, cb_shape = compress_channel(cb, q_chroma)
    cr_coeffs, cr_shape = compress_channel(cr, q_chroma)

    y_rec  = decompress_channel(y_coeffs,  q_luma,   y_shape)
    cb_rec = decompress_channel(cb_coeffs, q_chroma, cb_shape)
    cr_rec = decompress_channel(cr_coeffs, q_chroma, cr_shape)

    y_img  = Image.fromarray(y_rec,  mode="L")
    cb_img = Image.fromarray(cb_rec, mode="L")
    cr_img = Image.fromarray(cr_rec, mode="L")

    reconstructed_ycbcr = Image.merge("YCbCr", (y_img, cb_img, cr_img))
    reconstructed_rgb   = reconstructed_ycbcr.convert("RGB")

    default_output_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "output_images", "output_dct.jpg")
    )

    reconstructed_rgb.save(default_output_path, optimize=True)

    return {
        "y_coeffs": y_coeffs,
        "cb_coeffs": cb_coeffs,
        "cr_coeffs": cr_coeffs,
        "quality": quality,
        "output_path": default_output_path,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Aucun fichier fourni")

    input_path = sys.argv[1]
    quality = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    result = compress_image(input_path, quality)
    print(f"Image enregistrée : {result['output_path']}")
