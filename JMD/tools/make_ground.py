"""Paint the ground-surface texture (asphalt, stalls, paving, landscape, off-road, kerbs)
from model.json at a chosen resolution and window.

usage: make_ground.py model.json out.png x0 y0 x1 y1 metres_per_pixel
"""
import json, math, sys, random
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union

M = json.load(open(sys.argv[1])); OUT = sys.argv[2]
x0, y0, x1, y1, mpp = map(float, sys.argv[3:8])
W, H = int((x1 - x0) / mpp), int((y1 - y0) / mpp)
rng = np.random.default_rng(3)
random.seed(3)


def px(p):
    return ((p[0] - x0) / mpp, (y1 - p[1]) / mpp)


def noise(scale_m, amp):
    """value noise at a metric scale, upsampled bilinearly"""
    gw, gh = max(2, int(W * mpp / scale_m) + 2), max(2, int(H * mpp / scale_m) + 2)
    g = rng.standard_normal((gh, gw)).astype(np.float32)
    im = Image.fromarray(g).resize((W, H), Image.BILINEAR)
    return np.asarray(im) * amp


SAND = (182, 155, 117)
img = Image.new('RGB', (W, H), SAND)
d = ImageDraw.Draw(img)
mask_layers = {}


def poly(pts, fill, outline=None, width=1):
    d.polygon([px(p) for p in pts], fill=fill, outline=outline)


def line(pts, fill, w_m):
    d.line([px(p) for p in pts], fill=fill, width=max(1, int(round(w_m / mpp))))


def ring_pts(c, r, a0, a1, step=1.0):
    n = max(2, int(abs(a1 - a0) * r / step))
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def band(c, r0, r1, a0, a1, fill):
    poly(ring_pts(c, r1, a0, a1) + ring_pts(c, r0, a1, a0), fill)


def dashed_arc(c, r, a0, a1, fill, w=0.15, dash=3.0, gap=9.0):
    lo, hi = min(a0, a1), max(a0, a1)
    a = lo
    while a < hi:
        b = min(hi, a + dash / r)
        line(ring_pts(c, r, a, b, 0.5), fill, w)
        a += (dash + gap) / r


ASPH = (74, 74, 76); ASPH2 = (66, 66, 68); PARK = (82, 81, 80); WHITE = (228, 226, 220)
PAVE = (200, 190, 172); PAVE2 = (184, 173, 155); LAND = (108, 116, 70); KERB = (190, 186, 178)
DIRT = (180, 138, 92); DIRT2 = (160, 120, 80); WATER = (78, 74, 58); YEL = (214, 178, 70)

# ------------------------------------------------ off-site roads (illustrative cross-sections)
CNW, RNW = M['C_NW'], M['R_NW']
a0, a1 = 3.80, 1.72
band(CNW, RNW, RNW + 6, a0, a1, PAVE2)
band(CNW, RNW + 6, RNW + 14, a0, a1, ASPH)
band(CNW, RNW + 14, RNW + 18, a0, a1, LAND)
band(CNW, RNW + 18, RNW + 33, a0, a1, ASPH2)
band(CNW, RNW + 33, RNW + 43, a0, a1, LAND)
band(CNW, RNW + 43, RNW + 58, a0, a1, ASPH2)
band(CNW, RNW + 58, RNW + 62, a0, a1, LAND)
band(CNW, RNW + 62, RNW + 70, a0, a1, ASPH)
band(CNW, RNW + 70, RNW + 76, a0, a1, PAVE2)
for r in (RNW + 14, RNW + 18, RNW + 33, RNW + 43, RNW + 58, RNW + 62):
    line(ring_pts(CNW, r, a0, a1), KERB, 0.3)
for base in (RNW + 18, RNW + 43):
    line(ring_pts(CNW, base + 0.4, a0, a1), WHITE, 0.15); line(ring_pts(CNW, base + 14.6, a0, a1), WHITE, 0.15)
    for k in (1, 2, 3):
        dashed_arc(CNW, base + 0.3 + 3.6 * k, a0, a1, WHITE)
for base in (RNW + 6, RNW + 62):
    dashed_arc(CNW, base + 4, a0, a1, WHITE)

CSE, RSE = M['C_SE'], M['R_SE']
b0, b1 = 1.62, 2.95
band(CSE, RSE - 6, RSE, b0, b1, PAVE2)
band(CSE, RSE - 17, RSE - 6, b0, b1, ASPH2)
band(CSE, RSE - 31, RSE - 17, b0, b1, LAND)
band(CSE, RSE - 42, RSE - 31, b0, b1, ASPH2)
band(CSE, RSE - 46, RSE - 42, b0, b1, PAVE2)
for base in (RSE - 17, RSE - 42):
    line(ring_pts(CSE, base + 0.4, b0, b1), WHITE, 0.15); line(ring_pts(CSE, base + 10.6, b0, b1), WHITE, 0.15)
    for k in (1, 2):
        dashed_arc(CSE, base + 0.4 + 3.4 * k, b0, b1, WHITE)
for r in M['roads']:
    if r['kind'] == 'local':
        poly(r['poly'], ASPH)

# ------------------------------------------------ site base: internal roads are asphalt
poly(M['site'], ASPH)
site = Polygon(M['site'])
Z = M['zones']
by = lambda *cl: [Polygon(z['poly']) for z in Z if z['cls'] in cl]
buildings = by('showroom_standard', 'showroom_premium', 'showroom_flagship', 'showroom_flagship_plus', 'shop',
               'service_unit', 'collector_club', 'mosque_small', 'mosque_large', 'commercial_block', 'management',
               'testdrive_building', 'pdi_shed')

# pedestrian footways around buildings (3.5 m) and kerbs
for P in buildings:
    g = P.buffer(3.5, join_style=2)
    poly(list(g.exterior.coords), PAVE)
for P in by('shop'):
    z = next(z for z in Z if z['cls'] == 'shop' and Polygon(z['poly']).equals(P))
    fx, fy = z['front']
    prom = P.buffer(0.1).union(Polygon([(x + fx * 10, y + fy * 10) for x, y in P.exterior.coords])).convex_hull
    poly(list(prom.exterior.coords), PAVE)

# arena plaza + outdoor function area
arena_outer = Polygon(M['arena_outer'])
poly(list(arena_outer.buffer(6, join_style=2).exterior.coords), PAVE)
for P in by('outdoor_plaza', 'paving'):
    poly(list(P.buffer(2).exterior.coords), PAVE)
for P in by('energy_hub'):
    poly(list(P.exterior.coords), (176, 172, 164))

# parking with stall lines
def stall_lines(P):
    # pick the boundary arc-centre that makes the bay thinnest; fall back to rectangle axes
    best = None
    for c in (M['C_NW'], [2018 - 1350, 1324 - 1720], [2008 - 1350, 1313 - 1720]):
        rs = [math.dist(c, q) for q in P.exterior.coords]
        if best is None or max(rs) - min(rs) < best[0]:
            best = (max(rs) - min(rs), c, min(rs), max(rs))
    w, c, rmin, rmax = best
    mrr = list(P.minimum_rotated_rectangle.exterior.coords)
    L = max(math.dist(mrr[0], mrr[1]), math.dist(mrr[1], mrr[2]))
    segs = []
    if w < 40 and L > 250:
        angs = [math.atan2(y - c[1], x - c[0]) for x, y in P.exterior.coords]
        lo, hi = min(angs), max(angs)
        rows = [(rmin, rmin + 5.2), (rmax - 5.2, rmax)] if rmax - rmin >= 9 else [(rmin, rmax)]
        for ra, rb in rows:
            rm = (ra + rb) / 2; n = int((hi - lo) * rm / 2.6)
            for k in range(n + 1):
                a = lo + k * (hi - lo) / n
                segs.append([(c[0] + ra * math.cos(a), c[1] + ra * math.sin(a)), (c[0] + rb * math.cos(a), c[1] + rb * math.sin(a))])
            segs.append(ring_pts(c, rb if ra == rmin else ra, lo, hi, 1.0))
    else:
        return stall_lines_rect(P)
    return segs


def stall_lines_rect(P):
    mrr = list(P.minimum_rotated_rectangle.exterior.coords)
    e1 = (mrr[1][0] - mrr[0][0], mrr[1][1] - mrr[0][1]); e2 = (mrr[2][0] - mrr[1][0], mrr[2][1] - mrr[1][1])
    if math.hypot(*e1) < math.hypot(*e2): e1, e2 = e2, e1
    l1, l2 = math.hypot(*e1), math.hypot(*e2)
    u = (e1[0] / l1, e1[1] / l1); v = (e2[0] / l2, e2[1] / l2); cen = P.centroid
    segs = []
    t = -l2 / 2 + 1
    while t < l2 / 2 - 5:
        for row in (t, t + 5.2):  # two back-to-back rows of 5.2 m stalls, then 6.5 m aisle
            s = -l1 / 2
            while s < l1 / 2:
                a = (cen.x + u[0] * s + v[0] * row, cen.y + u[1] * s + v[1] * row)
                b = (a[0] + v[0] * 5.2, a[1] + v[1] * 5.2)
                segs.append([a, b]); s += 2.6
        segs.append([(cen.x - u[0] * l1 / 2 + v[0] * (t + 5.2), cen.y - u[1] * l1 / 2 + v[1] * (t + 5.2)),
                     (cen.x + u[0] * l1 / 2 + v[0] * (t + 5.2), cen.y + u[1] * l1 / 2 + v[1] * (t + 5.2))])
        t += 16.9
    return segs


for z in Z:
    if z['cls'] not in ('parking', 'dealer_storage', 'guest_parking', 'testdrive_parking'): continue
    P = Polygon(z['poly'])
    poly(z['poly'], PARK)
    best = min(((max(math.dist(c, q) for q in P.exterior.coords) - min(math.dist(c, q) for q in P.exterior.coords)), c)
               for c in (M['C_NW'], [668, -396], [658, -407]))
    mrr = list(P.minimum_rotated_rectangle.exterior.coords)
    L = max(math.dist(mrr[0], mrr[1]), math.dist(mrr[1], mrr[2]))
    segs = stall_lines(P) if (best[0] < 40 and L > 250 and z['cls'] == 'parking') else stall_lines_rect(P)
    for s_ in segs:
        g = LineString(s_).intersection(P.buffer(-0.3))
        for gg in getattr(g, 'geoms', [g]):
            if not gg.is_empty and gg.geom_type == 'LineString': line(list(gg.coords), WHITE, 0.12)
    line(list(P.exterior.coords), KERB, 0.35)

# landscape belt
for P in by('landscape'):
    poly(list(P.exterior.coords), LAND)

# off-road: loop track ring, terrain, obstacles
outer, inner = by('offroad_outer')[0], by('offroad_inner')[0]
poly(list(outer.exterior.coords), ASPH)
poly(list(inner.exterior.coords), DIRT)
for P in by('offroad_field'):
    poly(list(P.exterior.coords), (186, 146, 100))
obs = sorted([z for z in Z if z['cls'] == 'offroad_obstacle'], key=lambda z: z['area'])
MUD = (92, 70, 50); MUD2 = (74, 56, 40)
for z in obs:
    P = Polygon(z['poly'])
    if z['id'] == 202:   # mud apron around the water crossing (voice note: mud + water experiences)
        poly(list(P.buffer(9).exterior.coords), MUD)
        poly(list(P.buffer(4).exterior.coords), MUD2)
    poly(z['poly'], WATER if z['id'] == 202 else DIRT2)
# kerbs on the loop: red/white blocks on both edges
for edge in (outer.buffer(-0.6).exterior, inner.buffer(0.6).exterior):
    s = 0; k = 0
    while s < edge.length:
        a, b = edge.interpolate(s), edge.interpolate(min(edge.length, s + 2.0))
        line([(a.x, a.y), (b.x, b.y)], (178, 40, 36) if k % 2 else WHITE, 0.9)
        s += 2.0; k += 1
mid = outer.buffer(-(math.sqrt(outer.area) - math.sqrt(inner.area)) * 0.0)
# tyre tracks in the dirt
for _ in range(60):
    pts = []
    c = inner.representative_point(); x, y = c.x + random.uniform(-90, 90), c.y + random.uniform(-90, 90)
    a = random.uniform(0, 6.28)
    for k in range(40):
        a += random.uniform(-.12, .12); x += math.cos(a) * 3; y += math.sin(a) * 3; pts.append((x, y))
    g = LineString(pts).intersection(inner.buffer(-3))
    for gg in getattr(g, 'geoms', [g]):
        if gg.geom_type == 'LineString' and not gg.is_empty:
            line([(p[0] + 0.0, p[1]) for p in gg.coords], (165, 125, 84), 0.35)
            line([(p[0] + 1.7, p[1]) for p in gg.coords], (165, 125, 84), 0.35)

# arena forecourt paving bands (subtle)
for P in [arena_outer.buffer(6)]:
    ext = P.exterior; s = 0
    while s < ext.length:
        a = ext.interpolate(s); s += 6

# zebra crossings across the main internal drive between the two building rows
# (kept implicit: the masterplan does not locate crossings)

# ------------------------------------------------ texture: grain + large-scale variation
arr = np.asarray(img).astype(np.float32)
grain = noise(max(mpp * 2, 0.08), 5.0) + noise(1.5, 3.0) + noise(12, 4.0) + noise(60, 3.0)
arr += grain[..., None]
arr = np.clip(arr, 0, 255).astype(np.uint8)
Image.fromarray(arr).save(OUT, quality=93) if OUT.endswith('.jpg') else Image.fromarray(arr).save(OUT)
print(OUT, W, H)
