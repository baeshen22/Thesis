"""Prepare slide-ready images from the render library (gradients for title legibility, dimmed plan, source crops).
usage: prep_deck_images.py RENDER_DIR PREVIEW_DIR SOURCE_DIR OUT_DIR
"""
import os, sys
import numpy as np
from PIL import Image, ImageEnhance

RD, PV, SRC, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)


def load(name):
    for p in (os.path.join(RD, f'{name}.jpg'), os.path.join(PV, f'{name}.g.jpg'), os.path.join(PV, f'{name}.jpg'), os.path.join(PV, f'{name}.png')):
        if os.path.exists(p):
            return Image.open(p).convert('RGB'), p
    raise FileNotFoundError(name)


def grad(im, side='left', strength=0.78, extent=0.62):
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    if side == 'left':
        t = np.clip(1 - np.arange(w) / (w * extent), 0, 1)[None, :]
    elif side == 'bottom':
        t = np.clip((np.arange(h) - h * (1 - extent)) / (h * extent), 0, 1)[:, None]
    elif side == 'top':
        t = np.clip(1 - np.arange(h) / (h * extent), 0, 1)[:, None]
    t = (t ** 1.4) * strength
    dark = np.array([27, 28, 30], np.float32)
    a = a * (1 - t[..., None]) + dark * t[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def crop_to(im, ar, anchor_y=0.5):
    w, h = im.size
    if w / h > ar:
        nw = int(h * ar); x0 = (w - nw) // 2; return im.crop((x0, 0, x0 + nw, h))
    nh = int(w / ar); y0 = int((h - nh) * anchor_y); return im.crop((0, y0, w, y0 + nh))


def save(im, name, maxw=2400):
    if im.width > maxw: im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, name), quality=90, subsampling=0)
    print(name, im.size)


AR = 13.333 / 7.5
im, _ = load('hero_aerial'); im = crop_to(im, AR, 0.62); save(grad(grad(im, 'left', 0.80, 0.75), 'bottom', 0.55, 0.5), 'S01_hero.jpg')
im, _ = load('dusk_aerial'); im = crop_to(im, AR, 0.5); save(grad(grad(im, 'top', 0.6, 0.35), 'bottom', 0.95, 0.5), 'S02_vision.jpg')
im, _ = load('masterplan'); save(im, 'S03_masterplan.jpg', 2400)
dim = ImageEnhance.Brightness(ImageEnhance.Color(im).enhance(0.35)).enhance(0.55); save(dim, 'S15_plan_dim.jpg', 2400)
for src, dst in (('arrival', 'S04_arrival.jpg'), ('showroom_blvd', 'S05_showroom_blvd.jpg'), ('showroom_street', 'S05_showroom_street.jpg'),
                 ('facade_a', 'S06a_facade.jpg'), ('facade_b', 'S06b_facade.jpg'), ('facade_c', 'S06c_facade.jpg'),
                 ('arcade', 'S07_arcade.jpg'), ('arena_hero', 'S08_arena.jpg'), ('offroad', 'S10_offroad.jpg'),
                 ('club_ext', 'S13a_club_ext.jpg'), ('launch_plaza', 'S14_plaza.jpg')):
    im, _ = load(src); save(im, dst)
for src, dst in (('int_arena_expo', 'S09a_expo.jpg'), ('int_arena_theatre', 'S09b_theatre.jpg'), ('int_museum', 'S11_museum.jpg'),
                 ('int_simulator', 'S12_simulator.jpg'), ('int_club_lounge', 'S13b_club_lounge.jpg')):
    try:
        im, _ = load(src)
    except FileNotFoundError:
        im, _ = load(src.replace('int_', 'i_'))
    save(im, dst)
im, _ = load('vision_aerial'); im = crop_to(im, AR, 0.55); save(grad(grad(im, 'top', 0.55, 0.35), 'left', 0.6, 0.4), 'S17_vision.jpg')
try:
    im, _ = load('frontage_dusk')
except FileNotFoundError:
    im = Image.open(os.path.join(PV, 'frontage_dusk.g.jpg')).convert('RGB')
im = crop_to(im, AR, 0.5); save(grad(im, 'bottom', 0.85, 0.5), 'S18_closing.jpg')
# source material (unaltered content, cropped to frame)
p24 = Image.open(os.path.join(SRC, 'p-24.jpg')).convert('RGB'); save(p24, 'S16_locations.jpg')
p25 = Image.open(os.path.join(SRC, 'p-25.jpg')).convert('RGB'); save(p25, 'S16_options.jpg')
