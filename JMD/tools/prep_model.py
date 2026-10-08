"""Convert DWG hatch zones (hatches.json, extracted from FINAL_8-10-2026.dwg) into a
classified, oriented site model in local metre coordinates (model.json).

Every footprint is taken verbatim from the DWG. Anything the DWG does not define
(heights, fronts, tree/car/people placement, off-site roads) is generated here from
explicit rules and recorded as an illustrative assumption in the register.
"""
import json, math, random, sys
from shapely.geometry import Polygon, Point, LineString, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

random.seed(7)
H = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
O = (1350.0, 1720.0)                       # local origin (DWG units = metres)
C_NW = (2058.69 - O[0], 1294.67 - O[1])    # centre of frontage arc (R = 1171.03)
R_NW = 1171.03
C_SE = (2335.13 - O[0], 118.74 - O[1])     # centre of south-east boundary arc (R = 1830.20)
R_SE = 1830.20
CENTRES = [C_NW, (2018.0 - O[0], 1324.0 - O[1]), (2008.0 - O[0], 1313.0 - O[1]),
           (2062.0 - O[0], 1290.0 - O[1]), (2059.0 - O[0], 1295.0 - O[1])]


def loc(pts):
    return [(x - O[0], y - O[1]) for x, y in pts]


def classify(i, h):
    ci, pat = h['ci'], h['pat']
    if pat == 'ANSI31':
        m = {40: 'showroom_standard', 177: 'showroom_premium', 143: 'showroom_flagship',
             219: 'showroom_flagship_plus', 30: 'shop', 244: 'service_unit', 149: 'energy_hub',
             251: 'management', 7: 'arena_hall', 252: 'offroad_obstacle', 9: 'testdrive_dropoff'}
        if ci == 241:
            return 'mosque_large' if any('mosque' in l for l in h['labs']) else 'commercial_block'
        return m.get(ci, 'unknown')
    if pat == 'SOLID':
        if ci == 46: return 'mosque_small'
        if ci == 7: return 'testdrive_building'
        if 'collector club' in h['labs']: return 'collector_club'
        if any('outdoor' in l for l in h['labs']): return 'outdoor_plaza'
        if any('off road' in l for l in h['labs']):
            return 'offroad_outer' if h['area'] > 50000 else 'offroad_inner'
    if pat == 'BRASS': return 'offroad_field'
    if pat == 'NET3': return 'arena_surround'
    if pat == 'HONEY': return 'landscape'
    if pat == 'ZIGZAG': return 'dealer_storage'
    if pat == 'AR-CONC': return 'paving'
    if pat == 'BRICK':
        labs = ' '.join(h['labs'])
        if 'guest' in labs: return 'guest_parking'
        if 'test drive' in labs: return 'testdrive_parking'
        return 'parking' if h['area'] > 100 else 'paving'
    return 'unknown'


def best_centre(P):
    best = None
    for c in CENTRES:
        rs = [math.dist(c, p) for p in P.exterior.coords]
        w = max(rs) - min(rs)
        if best is None or w < best[0]:
            best = (w, c, min(rs), max(rs))
    return best


def mrr_axes(P):
    c = list(P.minimum_rotated_rectangle.exterior.coords)
    e1 = (c[1][0] - c[0][0], c[1][1] - c[0][1]); e2 = (c[2][0] - c[1][0], c[2][1] - c[1][1])
    l1, l2 = math.hypot(*e1), math.hypot(*e2)
    if l1 < l2: e1, e2, l1, l2 = e2, e1, l2, l1
    return (e1[0] / l1, e1[1] / l1), (e2[0] / l2, e2[1] / l2), l1, l2


# ---------------------------------------------------------------- zones
zones = []
for i, h in enumerate(H):
    P = Polygon(loc(h['pts'])).buffer(0)
    if P.is_empty or P.area < 5: continue
    if isinstance(P, MultiPolygon): P = max(P.geoms, key=lambda g: g.area)
    cls = classify(i, h)
    if cls == 'shop' and min(mrr_axes(P)[2:]) < 8: continue        # secondary hatch path, not a unit
    if cls == 'dealer_storage' and P.area < 10000: cls = 'pdi_shed'  # narrow strip inside storage yard
    z = {'id': i, 'cls': cls, 'area': round(P.area, 1), 'poly': [list(map(lambda v: round(v, 3), p)) for p in P.exterior.coords]}
    cx, cy = P.centroid.x, P.centroid.y
    if cls.startswith('showroom') or cls == 'shop':
        c = C_NW if cls.startswith('showroom') else (2018.0 - O[0], 1324.0 - O[1])
        d = math.hypot(cx - c[0], cy - c[1])
        z['front'] = [-(cx - c[0]) / d * -1, (cy - c[1]) / d]  # outward radial
        z['front'] = [(cx - c[0]) / d, (cy - c[1]) / d]
    zones.append(z)

# service units: doors face away from the centre-line of their back-to-back block
svc = [z for z in zones if z['cls'] == 'service_unit']
blocks = unary_union([Polygon(z['poly']).buffer(0.6) for z in svc])
for z in svc:
    P = Polygon(z['poly'])
    blk = next(b for b in getattr(blocks, 'geoms', [blocks]) if b.contains(P.centroid))
    ax, nrm, _, _ = mrr_axes(blk)
    bc = blk.centroid
    s = (P.centroid.x - bc.x) * nrm[0] + (P.centroid.y - bc.y) * nrm[1]
    z['front'] = [nrm[0] * (1 if s >= 0 else -1), nrm[1] * (1 if s >= 0 else -1)]

# ---------------------------------------------------------------- site boundary
def arc(c, r, a0, a1, step=2.0):
    n = max(2, int(abs(a1 - a0) * r / step))
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]

nw = arc(C_NW, R_NW, 3.1614, 2.2772)               # SW -> NE along frontage
top = [(1317.22 - O[0], 2193.32 - O[1]), (1817.86 - O[0], 2193.32 - O[1])]
right = [(1817.86 - O[0], 1874.32 - O[1])]
se = arc(C_SE, R_SE, 1.8573, 2.4819)               # NE -> SW
site = Polygon(nw + top + right + se).buffer(0)

# ---------------------------------------------------------------- off-site context roads (ILLUSTRATIVE)
roads = []
def ring_road(c, r_in, r_out, a0, a1, kind):
    poly = Polygon(arc(c, r_out, a0, a1) + arc(c, r_in, a1, a0)).buffer(0)
    roads.append({'kind': kind, 'poly': [list(p) for p in poly.exterior.coords], 'centre': c, 'r_in': r_in, 'r_out': r_out, 'a0': a0, 'a1': a1})

# Frontage road (Madinah Road per source narration; cross-section illustrative):
# verge 6 | service rd 8 | sep 4 | 4 lanes 15 | median 10 | 4 lanes 15 | sep 4 | service rd 8 | verge 6
ring_road(C_NW, R_NW, R_NW + 76, 3.80, 1.72, 'frontage')
ring_road(C_SE, R_SE - 46, R_SE, 1.62, 2.95, 'se_road')
roads.append({'kind': 'local', 'poly': [list(p) for p in Polygon([(top[0][0] - 60, top[0][1]), (top[1][0] + 30, top[1][1]), (top[1][0] + 30, top[1][1] + 24), (top[0][0] - 60, top[0][1] + 24)]).exterior.coords]})
roads.append({'kind': 'local', 'poly': [list(p) for p in Polygon([(right[0][0], right[0][1] - 40), (right[0][0] + 24, right[0][1] - 40), (right[0][0] + 24, top[1][1] + 24), (right[0][0], top[1][1] + 24)]).exterior.coords]})

# ---------------------------------------------------------------- scatter: parking stalls -> cars
cars, palms, people, shrubs = [], [], [], []

def place_arc_stalls(P, occ, kind='car'):
    w, c, rmin, rmax = best_centre(P)
    angs = [math.atan2(y - c[1], x - c[0]) for x, y in P.exterior.coords]
    a0, a1 = min(angs), max(angs)
    for row_r, flip in ((rmin + 2.6, 1), (rmax - 2.6, -1)):
        if rmax - rmin < 9: row_r, flip = (rmin + rmax) / 2, 1
        n = int((a1 - a0) * row_r / 2.6)
        for k in range(n):
            a = a0 + (k + 0.5) * (a1 - a0) / n
            x, y = c[0] + row_r * math.cos(a), c[1] + row_r * math.sin(a)
            fp = affinity.rotate(Polygon([(-2.3, -1), (2.3, -1), (2.3, 1), (-2.3, 1)]), a, use_radians=True).buffer(0)
            fp = affinity.translate(fp, x, y)
            if not P.contains(fp): continue
            if random.random() > occ: continue
            heading = a + (0 if random.random() < 0.5 else math.pi)
            cars.append([round(x, 2), round(y, 2), round(heading, 3), random.random()])
        if rmax - rmin < 9: break

def place_grid_stalls(P, occ, pitch=2.6, depth=5.2, aisle=6.5):
    ax, nrm, L, W = mrr_axes(P)
    cen = P.centroid
    nrows = int(W // (depth * 2 + aisle)) * 2 or 1
    for rr in range(-int(W), int(W)):
        pass
    t = -W / 2 + depth / 2 + 1
    rows = []
    while t < W / 2 - depth / 2:
        rows.append(t); rows.append(t + depth)
        t += depth * 2 + aisle
    for t in rows:
        s = -L / 2 + 2
        while s < L / 2 - 2:
            x = cen.x + ax[0] * s + nrm[0] * t; y = cen.y + ax[1] * s + nrm[1] * t
            if P.contains(Point(x, y).buffer(2.4)) and random.random() < occ and not any(Q.contains(Point(x, y)) for Q in SHEDS):
                heading = math.atan2(nrm[1], nrm[0]) + (0 if random.random() < .5 else math.pi)
                cars.append([round(x, 2), round(y, 2), round(heading + random.uniform(-.03, .03), 3), random.random()])
            s += pitch

SHEDS = [Polygon(z['poly']).buffer(3) for z in zones if z['cls'] == 'pdi_shed']
_done = []
for z in zones:
    P = Polygon(z['poly'])
    if z['cls'] == 'parking':
        if any(P.intersection(Q).area > 0.3 * min(P.area, Q.area) for Q in _done): continue
        _done.append(P)
        w, c, rmin, rmax = best_centre(P)
        _, _, L, W = mrr_axes(P)
        if w < 40 and L > 250: place_arc_stalls(P, 0.62)
        else: place_grid_stalls(P, 0.55)
    elif z['cls'] == 'dealer_storage':
        place_grid_stalls(P, 0.88)
    elif z['cls'] in ('guest_parking', 'testdrive_parking'):
        place_grid_stalls(P, 0.7)

# cars on display inside showrooms (along the glazed front)
display = []
for z in zones:
    if not z['cls'].startswith('showroom'): continue
    P = Polygon(z['poly']); fx, fy = z['front']
    tx, ty = -fy, fx
    _, _, L, W = mrr_axes(P)
    n = {'showroom_standard': 2, 'showroom_premium': 3, 'showroom_flagship': 4, 'showroom_flagship_plus': 4}[z['cls']]
    width = abs(L * (tx * mrr_axes(P)[0][0] + ty * mrr_axes(P)[0][1])) + abs(W * (tx * mrr_axes(P)[1][0] + ty * mrr_axes(P)[1][1]))
    width = min(width, 30)
    for k in range(n):
        s = -width / 2 + width * (k + 0.5) / n
        for depth_off in (4.0, 11.0) if z['cls'] != 'showroom_standard' else (4.5,):
            cx = P.centroid.x + fx * (W / 2 - depth_off) + tx * s
            cy = P.centroid.y + fy * (W / 2 - depth_off) + ty * s
            if P.contains(Point(cx, cy).buffer(2.4)):
                display.append([round(cx, 2), round(cy, 2), round(math.atan2(fy, fx) + math.pi / 2 + random.uniform(-.5, .5), 3), random.random()])

# traffic on frontage road (static, lane-aligned)
for r in roads:
    if r['kind'] not in ('frontage', 'se_road'): continue
    c = r['centre']
    if r['kind'] == 'frontage':
        lanes = [(R_NW + 6 + 2, -1), (R_NW + 6 + 6, 1), (R_NW + 18 + 2, -1), (R_NW + 18 + 5.6, -1), (R_NW + 18 + 9.2, -1), (R_NW + 18 + 12.8, -1),
                 (R_NW + 43 + 2, 1), (R_NW + 43 + 5.6, 1), (R_NW + 43 + 9.2, 1), (R_NW + 43 + 12.8, 1), (R_NW + 62 + 2, 1), (R_NW + 62 + 6, -1)]
    else:
        lanes = [(R_SE - 6 - 2, 1), (R_SE - 6 - 5.6, 1), (R_SE - 6 - 9.2, 1), (R_SE - 31 - 2, -1), (R_SE - 31 - 5.6, -1), (R_SE - 31 - 9.2, -1)]
    for rr, d in lanes:
        a = r['a1'] if r['a1'] < r['a0'] else r['a0']
        amax = max(r['a0'], r['a1'])
        while a < amax:
            a += random.uniform(28, 90) / rr
            x, y = c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)
            cars.append([round(x, 2), round(y, 2), round(a + d * math.pi / 2, 3), random.random()])

# ---------------------------------------------------------------- palms
def along_arc(c, r, a0, a1, spacing, jitter=0.0):
    n = int(abs(a1 - a0) * r / spacing)
    return [(c[0] + (r + random.uniform(-jitter, jitter)) * math.cos(a0 + (a1 - a0) * k / n),
             c[1] + (r + random.uniform(-jitter, jitter)) * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]

for p in along_arc(C_NW, R_NW + 3, 3.78, 1.74, 11): palms.append(p)          # frontage verge
for p in along_arc(C_NW, R_NW + 38, 3.78, 1.74, 13): palms.append(p)         # frontage median
for p in along_arc(C_NW, R_NW + 73, 3.78, 1.74, 11): palms.append(p)         # far verge
for p in along_arc(C_SE, R_SE - 23, 1.63, 2.93, 13): palms.append(p)         # SE median

# palms on the long edges of parking bays (tree islands every ~16 m)
built = unary_union([Polygon(z['poly']).buffer(0.5) for z in zones if z['cls'] not in ('parking', 'landscape', 'dealer_storage', 'offroad_outer', 'offroad_inner', 'offroad_field', 'arena_surround', 'outdoor_plaza', 'paving', 'guest_parking', 'testdrive_parking', 'offroad_obstacle')])
for z in zones:
    if z['cls'] != 'parking': continue
    P = Polygon(z['poly'])
    edge = P.exterior
    L = edge.length
    s = 0
    while s < L:
        pt = edge.interpolate(s)
        q = P.buffer(-1.2).exterior.interpolate(P.buffer(-1.2).exterior.project(pt))
        if not built.contains(q): palms.append((q.x, q.y))
        s += 26

# shop-arcade promenade palms (front side of shop row), plazas, landscape belt
shops = [z for z in zones if z['cls'] == 'shop']
for z in shops:
    P = Polygon(z['poly']); fx, fy = z['front']
    c = P.centroid
    palms.append((c.x + fx * 17.5, c.y + fy * 17.5))
land = [Polygon(z['poly']) for z in zones if z['cls'] == 'landscape']
for P in land:
    minx, miny, maxx, maxy = P.bounds
    for _ in range(int(P.area / 70)):
        x, y = random.uniform(minx, maxx), random.uniform(miny, maxy)
        if P.contains(Point(x, y)):
            (palms if random.random() < .45 else shrubs).append((x, y))
plaza = unary_union([Polygon(z['poly']) for z in zones if z['cls'] in ('outdoor_plaza', 'arena_surround')])
arena_halls = unary_union([Polygon(z['poly']) for z in zones if z['cls'] == 'arena_hall'])
arena_outer = unary_union([Polygon(z['poly']) for z in zones if z['cls'] in ('arena_surround', 'arena_hall')]).convex_hull
OP = unary_union([Polygon(z['poly']) for z in zones if z['cls'] == 'outdoor_plaza'])
for g in getattr(OP, 'geoms', [OP]):
    ext = g.buffer(-3).exterior
    s = 0
    while s < ext.length:
        p = ext.interpolate(s); palms.append((p.x, p.y)); s += 9

# energy hub / management frontage
palms = [(round(x, 2), round(y, 2), round(random.uniform(0.85, 1.2), 2), round(random.uniform(0, 6.28), 2)) for x, y in palms
         if not any(Polygon(z['poly']).contains(Point(x, y)) for z in zones if z['cls'] in ('showroom_standard', 'shop', 'service_unit', 'collector_club'))]

# ---------------------------------------------------------------- people
def scatter_people(geom, n, mix=(0.45, 0.30, 0.25)):
    minx, miny, maxx, maxy = geom.bounds
    k = 0; tries = 0
    while k < n and tries < n * 50:
        tries += 1
        x, y = random.uniform(minx, maxx), random.uniform(miny, maxy)
        if geom.contains(Point(x, y)):
            r = random.random()
            kind = 0 if r < mix[0] else (1 if r < mix[0] + mix[1] else 2)
            people.append([round(x, 2), round(y, 2), round(random.uniform(0, 6.28), 2), kind, round(random.uniform(.92, 1.06), 2)])
            k += 1

promenade = unary_union([Polygon(z['poly']).buffer(9).difference(Polygon(z['poly']).buffer(0.2)) for z in shops])
scatter_people(promenade, 380)
scatter_people(OP.buffer(-1), 160)
scatter_people(arena_outer.difference(arena_halls.buffer(2)), 180)
cc = [Polygon(z['poly']) for z in zones if z['cls'] == 'collector_club'][0]
scatter_people(cc.buffer(10).difference(cc.buffer(1)), 25)

json.dump({'origin': O, 'C_NW': C_NW, 'R_NW': R_NW, 'C_SE': C_SE, 'R_SE': R_SE,
           'site': [list(p) for p in site.exterior.coords], 'site_area': round(site.area),
           'zones': zones, 'roads': roads, 'cars': cars, 'display_cars': display,
           'palms': palms, 'shrubs': [(round(x, 2), round(y, 2)) for x, y in shrubs], 'people': people,
           'arena_outer': [list(p) for p in arena_outer.exterior.coords]}, open(OUT, 'w'))
from collections import Counter
cnt = Counter(z['cls'] for z in zones)
area = Counter()
for z in zones: area[z['cls']] += z['area']
for k in sorted(cnt): print(f"{k:24s} {cnt[k]:4d}  {area[k]:10.0f} m2")
print('site area', round(site.area), 'cars', len(cars), 'display', len(display), 'palms', len(palms), 'people', len(people), 'shrubs', len(shrubs))
