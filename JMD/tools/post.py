"""Studio post-production grade applied identically to every render (contrast, warmth, vignette, sharpen)."""
import sys
import numpy as np
from PIL import Image, ImageFilter

def grade(src, dst, warmth=1.0, contrast=1.0, vignette=0.14):
    im = Image.open(src).convert('RGB')
    im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=2))
    a = np.asarray(im).astype(np.float32) / 255.0
    # gentle S-curve
    k = 0.18 * contrast
    a = a + k * a * (1 - a) * (2 * a - 1)
    a = np.clip(0.5 + (a - 0.5) * (1.0 + 0.06 * contrast), 0, 1)
    # warm highlights / cool shadows (subtle split-tone)
    lum = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2])[..., None]
    warm = np.array([1.035, 1.0, 0.955]) ** warmth
    cool = np.array([0.985, 1.0, 1.02])
    a = a * (lum * warm + (1 - lum) * cool)
    # saturation +8 %
    a = lum + (a - lum) * 1.08
    # vignette
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
    a = a * (1 - vignette * np.clip(r - 0.35, 0, 1) ** 1.6 / 0.65 ** 1.6)[..., None]
    out = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    out.save(dst, quality=94, subsampling=0) if dst.lower().endswith('.jpg') else out.save(dst)

if __name__ == '__main__':
    grade(sys.argv[1], sys.argv[2], *(float(x) for x in sys.argv[3:]))
