"""Normalise a 16-bit inverse-depth render into an 8-bit ControlNet depth map (near = white, sky = black)."""
import sys
import numpy as np
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(src)).astype(np.float64) / 65535.0
m = a > 1e-5
# linear inverse depth a = 0.12 * D / d (D = camera-to-subject distance). Window: d in [0.15 D, 4 D]
a_near, a_far = 0.12 / 0.15, 0.12 / 4.0
b = np.zeros_like(a)
b[m] = np.clip((np.log(np.maximum(a[m], 1e-6)) - np.log(a_far)) / (np.log(a_near) - np.log(a_far)), 0, 1) * 0.94 + 0.06
Image.fromarray((b * 255 + 0.5).astype(np.uint8)).save(dst)
print(dst)
