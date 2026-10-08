"""Interior scenes for JMD, built from the same material/asset library as the district model.

run: bvenv/bin/python build_interiors.py jmd.blend model.json SCENE out.png W H SPP
SCENE in: arena_expo, arena_theatre, museum, simulator, club_lounge
"""
import bpy, bmesh, json, math, random, sys
from mathutils import Vector, Matrix
from shapely.geometry import Polygon as SP
from shapely.ops import unary_union

BLEND, MODEL, SCENE, OUT, W, H, SPP = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7])
bpy.ops.wm.open_mainfile(filepath=BLEND)
M = json.load(open(MODEL))
sc = bpy.context.scene
random.seed(4)

# keep library (materials + ASSETS meshes), drop the district geometry
keep = {o.name for o in bpy.data.collections['ASSETS'].objects} | {'Cam', 'Sun'}
for o in list(bpy.data.objects):
    if o.name not in keep: bpy.data.objects.remove(o, do_unlink=True)
A = {o.name: o for o in bpy.data.collections['ASSETS'].objects}
N = {  # material key -> name in library
    'stone': 'Limestone GRC', 'stone_dark': 'Stone warm grey', 'white_metal': 'Warm white aluminium', 'bronze': 'Champagne bronze anodised',
    'graphite': 'Graphite panel', 'glass': 'Architectural glass', 'glass_tinted': 'Solar glass', 'floor': 'Polished stone floor',
    'ceiling': 'Interior ceiling light', 'interior_wall': 'Interior wall', 'concrete': 'Concrete', 'fabric': 'Shade fabric',
    'timber': 'Weathered timber', 'led': 'Linear light', 'pole': 'Pole', 'mech': 'Rooftop plant', 'cover': 'Reveal cover'}
def _fallback(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.53, 0.5, 1); return m
MAT = {k: (bpy.data.materials.get(v) or _fallback(v)) for k, v in N.items()}


def newmat(name, base, rough=0.5, metal=0.0, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    for k, v in kw.items(): b.inputs[k].default_value = (*v, 1) if isinstance(v, tuple) else v
    return m


MAT['dark_floor'] = newmat('Dark polished stone', (0.05, 0.05, 0.055), 0.12)
MAT['epoxy'] = newmat('Event floor', (0.17, 0.17, 0.18), 0.28)
MAT['club_floor'] = newmat('Club floor', (0.10, 0.09, 0.085), 0.3)
MAT['land'] = newmat('Exterior ground', (0.33, 0.26, 0.18), 0.9)
MAT['truss'] = newmat('Steel truss', (0.62, 0.63, 0.64), 0.4, 0.8)
MAT['acoustic'] = newmat('Acoustic panel', (0.18, 0.17, 0.16), 0.9)
MAT['seat'] = newmat('Seat fabric', (0.09, 0.09, 0.10), 0.8)
MAT['screen'] = newmat('LED screen off', (0.01, 0.01, 0.012), 0.2)
MAT['leather'] = newmat('Leather tan', (0.30, 0.16, 0.08), 0.45, **{'Coat Weight': 0.2})
MAT['fabric_sofa'] = newmat('Sofa fabric', (0.52, 0.47, 0.40), 0.85)
MAT['rug'] = newmat('Rug', (0.20, 0.18, 0.16), 0.95)
MAT['walnut'] = newmat('Walnut', (0.12, 0.065, 0.035), 0.35)
MAT['panel_frame'] = newmat('Exhibit frame', (0.03, 0.03, 0.03), 0.3, 0.6)
MAT['panel_light'] = newmat('Exhibit light panel', (0.5, 0.45, 0.38), 0.5, **{'Emission Color': (1.0, 0.82, 0.60), 'Emission Strength': 0.55})
MAT['red'] = newmat('Kerb red', (0.5, 0.03, 0.03), 0.4)


def paint(name, col, metal=0.6, rough=0.22):
    m = newmat(name, col, rough, metal); m.node_tree.nodes['Principled BSDF'].inputs['Coat Weight'].default_value = 1.0
    m.node_tree.nodes['Principled BSDF'].inputs['Coat Roughness'].default_value = 0.03
    return m


PAINTS = [paint('p_black', (0.012, 0.012, 0.014)), paint('p_silver', (0.55, 0.56, 0.57)), paint('p_white', (0.80, 0.80, 0.78), 0.1),
          paint('p_red', (0.38, 0.02, 0.02)), paint('p_blue', (0.02, 0.05, 0.13)), paint('p_green', (0.03, 0.09, 0.06)),
          paint('p_cream', (0.62, 0.55, 0.42), 0.1), paint('p_grey', (0.16, 0.17, 0.18))]


class MB:
    def __init__(self): self.d = {}
    def _b(self, m):
        if m not in self.d: self.d[m] = ([], [])
        return self.d[m]
    def face(self, m, pts):
        v, f = self._b(m); i = len(v); v.extend(pts); f.append(list(range(i, i + len(pts))))
    def prism(self, poly, z0, z1, side, top=None, bottom=None):
        poly = [tuple(p) for p in poly]
        if poly[0] == poly[-1]: poly = poly[:-1]
        n = len(poly)
        ar = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
        if ar < 0: poly = poly[::-1]
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            if side: self.face(side, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)])
        if top: self.face(top, [(x, y, z1) for x, y in poly])
        if bottom: self.face(bottom, [(x, y, z0) for x, y in poly[::-1]])
    def box(self, m, c, size, rot=0.0, mtop=None):
        hx, hy = size[0] / 2, size[1] / 2; cs, sn = math.cos(rot), math.sin(rot)
        pts = [(c[0] + x * cs - y * sn, c[1] + x * sn + y * cs) for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]
        self.prism(pts, c[2], c[2] + size[2], m, mtop or m, m)
    def cyl(self, m, c, r, h, seg=24):
        self.prism([(c[0] + r * math.cos(2 * math.pi * k / seg), c[1] + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)], c[2], c[2] + h, m, m, m)
    def build(self, name):
        for m, (v, f) in self.d.items():
            me = bpy.data.meshes.new(f'{name}_{m}'); me.from_pydata(v, [], f); me.validate()
            bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
            me.materials.append(MAT[m]); ob = bpy.data.objects.new(f'{name}_{m}', me); sc.collection.objects.link(ob)


def place(asset, loc, rot=0.0, mat=None, scale=1.0, subsurf=0):
    src = A[asset]
    ob = bpy.data.objects.new(asset + '_i', src.data.copy() if mat else src.data)
    if mat:
        ob.data.materials[0] = mat
    ob.location = loc; ob.rotation_euler = (0, 0, rot); ob.scale = (scale, scale, scale)
    if subsurf:
        md = ob.modifiers.new('s', 'SUBSURF'); md.levels = subsurf; md.render_levels = subsurf
    sc.collection.objects.link(ob)
    return ob


def area_light(loc, size, power, color=(1.0, 0.92, 0.82), rot=(0, 0, 0), shape='RECTANGLE'):
    L = bpy.data.lights.new('al', 'AREA'); L.shape = shape
    L.size = size[0]; L.size_y = size[1]; L.energy = power; L.color = color
    o = bpy.data.objects.new('al', L); o.location = loc; o.rotation_euler = rot; sc.collection.objects.link(o)
    return o


def spot(loc, target, power, angle=25, color=(1.0, 0.9, 0.78)):
    L = bpy.data.lights.new('sp', 'SPOT'); L.energy = power; L.spot_size = math.radians(angle); L.spot_blend = 0.5; L.color = color
    o = bpy.data.objects.new('sp', L); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); sc.collection.objects.link(o)


def people(n, region, kinds=(0, 1, 2), mix=(0.45, 0.3, 0.25), z=0.0, avoid=None):
    minx, miny, maxx, maxy = region.bounds; k = 0; tries = 0
    from shapely.geometry import Point
    while k < n and tries < 20000:
        tries += 1
        x, y = random.uniform(minx, maxx), random.uniform(miny, maxy)
        if not region.contains(Point(x, y)) or (avoid is not None and avoid.contains(Point(x, y))): continue
        r = random.random(); kind = 0 if r < mix[0] else (1 if r < mix[0] + mix[1] else 2)
        place(['fig_thobe', 'fig_abaya', 'fig_casual'][kind], (x, y, z), random.uniform(0, 6.28), scale=random.uniform(.95, 1.05)); k += 1


def camera(loc, look, lens=24, shift_y=0.0):
    globals()['LOOK'] = look
    c = sc.camera; c.location = loc
    c.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.type = 'PERSP'; c.data.shift_y = shift_y; c.data.sensor_width = 36; c.data.clip_start = 0.1


def sun_sky(az=270, el=25, strength=3.0, sky=0.25):
    to_sun = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    s = bpy.data.objects['Sun']; s.rotation_euler = to_sun.to_track_quat('Z', 'Y').to_euler(); s.data.energy = strength
    sk = sc.world.node_tree.nodes['sky']; sk.sun_elevation = math.radians(el); sk.sun_rotation = math.pi / 2 - math.radians(az); sk.sun_disc = False
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = sky


def car_display(loc, rot, paint_i, kind='car_sedan', plinth=None, z=0.0, plinth_mat='bronze', mb=None):
    if plinth and mb is not None:
        if plinth[0] == 'round':
            mb.cyl('graphite', (loc[0], loc[1], z), plinth[1], 0.28, 48); mb.cyl(plinth_mat, (loc[0], loc[1], z + 0.28), plinth[1] + 0.03, 0.02, 48)
        else:
            mb.box('graphite', (loc[0], loc[1], z), (plinth[1], plinth[2], 0.28), rot); mb.box(plinth_mat, (loc[0], loc[1], z + 0.28), (plinth[1] + 0.06, plinth[2] + 0.06, 0.02), rot)
        z += 0.30
    o = place(kind, (loc[0], loc[1], z), rot, mat=PAINTS[paint_i], subsurf=1)
    return o


mb = MB()
Z = M['zones']

# ======================================================================= ARENA (real DWG hall footprint)
if SCENE.startswith('arena'):
    halls = unary_union([SP(z['poly']) for z in Z if z['cls'] == 'arena_hall']).buffer(1.0, join_style=2).simplify(0.3)
    pts = list(halls.exterior.coords)
    HH = 21.0
    mb.prism(pts, -0.2, 0.0, None, 'epoxy')
    mb.prism(pts, HH, HH + 0.3, None, None, 'acoustic')
    n = len(pts) - 1
    for i in range(n):
        a, b = pts[i], pts[i + 1]
        mb.face('glass', [(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], 7.5), (a[0], a[1], 7.5)])
        mb.face('acoustic', [(a[0], a[1], 7.5), (b[0], b[1], 7.5), (b[0], b[1], HH), (a[0], a[1], HH)])
        L = math.dist(a, b); ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for k in range(int(L // 1.6)):
            p = (a[0] + (b[0] - a[0]) * (k + 0.5) / int(L // 1.6), a[1] + (b[1] - a[1]) * (k + 0.5) / int(L // 1.6))
            mb.box('walnut', (p[0], p[1], 8.0), (0.12, 0.35, HH - 8.5), ang)
        for k in range(int(L // 9)):
            p = (a[0] + (b[0] - a[0]) * (k + 0.5) / max(1, int(L // 9)), a[1] + (b[1] - a[1]) * (k + 0.5) / max(1, int(L // 9)))
            mb.box('white_metal', (p[0], p[1], 0), (0.6, 0.6, HH), ang)
    # primary trusses (deep steel, 12 m centres) and secondary purlins
    minx, miny, maxx, maxy = halls.bounds
    from shapely.geometry import LineString
    cx_, cy_ = halls.centroid.x, halls.centroid.y
    ang_t = math.radians(28)
    for k in range(-12, 13):
        off = k * 12.0
        p0 = (cx_ - math.cos(ang_t) * 300 - math.sin(ang_t) * off, cy_ - math.sin(ang_t) * 300 + math.cos(ang_t) * off)
        p1 = (cx_ + math.cos(ang_t) * 300 - math.sin(ang_t) * off, cy_ + math.sin(ang_t) * 300 + math.cos(ang_t) * off)
        seg = LineString([p0, p1]).intersection(halls.buffer(-0.5))
        for g in getattr(seg, 'geoms', [seg]):
            if g.is_empty or g.length < 5: continue
            (x0, y0), (x1, y1) = g.coords[0], g.coords[-1]; Lg = g.length; mid = ((x0 + x1) / 2, (y0 + y1) / 2)
            for zz in (HH - 0.35, HH - 3.2):
                mb.box('truss', (mid[0], mid[1], zz), (Lg, 0.45, 0.35), ang_t)
            nd = int(Lg // 3)
            for j in range(nd):
                t = (j + 0.5) / nd; px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                mb.box('truss', (px, py, HH - 2.9), (0.15, 0.15, 2.6), ang_t + (0.6 if j % 2 else -0.6))
            # skylight slot alongside every second truss
            if k % 2 == 0:
                mb.box('ceiling', (mid[0] - math.sin(ang_t) * 6, mid[1] + math.cos(ang_t) * 6, HH - 0.05), (Lg - 6, 2.6, 0.04), ang_t)
    # retractable partition tracks (DWG hall divisions)
    for z in Z:
        if z['cls'] != 'arena_hall': continue
        q = SP(z['poly']).simplify(0.3).exterior
        for i in range(len(q.coords) - 1):
            a, b = q.coords[i], q.coords[i + 1]
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if halls.buffer(-3).contains(SP([(mid[0] - .1, mid[1] - .1), (mid[0] + .1, mid[1] - .1), (mid[0] + .1, mid[1] + .1)])):
                mb.box('graphite', (mid[0], mid[1], HH - 4.0), (math.dist(a, b), 0.6, 0.5), math.atan2(b[1] - a[1], b[0] - a[0]))
    # lighting
    for k in range(-5, 6):
        for j in range(-5, 6):
            p = (cx_ + k * 14, cy_ + j * 14)
            from shapely.geometry import Point
            if halls.buffer(-6).contains(Point(p)):
                area_light((p[0], p[1], HH - 3.6), (3, 3), 650, (1.0, 0.93, 0.84))
    sun_sky(255, 22, 3.2, 0.35)
    # exterior ground so the glazing sees daylight + context
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(cx_, cy_, -0.25)); bpy.context.active_object.data.materials.append(MAT['stone_dark'])
    E = halls.exterior
    entry = min(range(n), key=lambda i: math.dist(((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2), (-297, -224)))
    ea, eb = pts[entry], pts[entry + 1]
    emid = ((ea[0] + eb[0]) / 2, (ea[1] + eb[1]) / 2)
    inward = (cx_ - emid[0], cy_ - emid[1]); il = math.hypot(*inward); inward = (inward[0] / il, inward[1] / il)
    far = (cx_ + inward[0] * 60, cy_ + inward[1] * 60)

    if SCENE == 'arena_expo':
        # exhibition mode: brand stands on a grid, open circulation
        grid_ang = math.atan2(inward[1], inward[0])
        u = (math.cos(grid_ang), math.sin(grid_ang)); v = (-u[1], u[0])
        stands = []
        for i in range(-4, 5):
            for j in range(-3, 4):
                p = (cx_ + u[0] * i * 17 + v[0] * j * 19, cy_ + u[1] * i * 17 + v[1] * j * 19)
                fp = SP([(p[0] + dx, p[1] + dy) for dx, dy in ((-7, -7), (7, -7), (7, 7), (-7, 7))])
                if halls.buffer(-10).contains(fp): stands.append((p, i, j))
        for p, i, j in stands:
            kind = (i + j) % 3
            if kind == 0:
                car_display(p, grid_ang + 0.6, (i * 3 + j) % 8, 'car_coupe', ('round', 3.4), mb=mb)
            else:
                mb.box('floor', (p[0], p[1], 0), (12, 10, 0.12), grid_ang)
                bw = (p[0] - u[0] * 5.6, p[1] - u[1] * 5.6)
                mb.box('graphite', (bw[0], bw[1], 0.12), (0.4, 10, 2.6), grid_ang)
                mb.box('led', (bw[0] + u[0] * 0.21, bw[1] + u[1] * 0.21, 2.5), (0.02, 9.6, 0.06), grid_ang)
                car_display((p[0] + v[0] * 2.5, p[1] + v[1] * 2.5), grid_ang + 1.2, (i + 2 * j) % 8, ['car_sedan', 'car_suv'][(i + j) % 2], z=0.12)
                car_display((p[0] - v[0] * 2.8 + u[0] * 1.5, p[1] - v[1] * 2.8 + u[1] * 1.5), grid_ang - 0.4, (i + j + 3) % 8, 'car_sedan_s', z=0.12)
            # hanging blank banner (brand identity to be applied by exhibitor)
            mb.box('graphite', (p[0], p[1], 12.0), (6.0, 0.05, 3.0), grid_ang + 1.57)
            mb.box('led', (p[0], p[1], 11.95), (6.1, 0.07, 0.05), grid_ang + 1.57)
        people(220, halls.buffer(-4), avoid=unary_union([SP([(p[0] + dx, p[1] + dy) for dx, dy in ((-6.5, -6.5), (6.5, -6.5), (6.5, 6.5), (-6.5, 6.5))]) for p, _, _ in stands]))
        cam_loc = (emid[0] + inward[0] * 14 - inward[1] * 6, emid[1] + inward[1] * 14 + inward[0] * 6, 8.0)
        camera(cam_loc, (far[0], far[1], 0.0), 22)
        sc.view_settings.exposure = -0.4
    else:
        # 180° theatre mode: stage at the far side, telescopic seating in a fan
        stage_c = (cx_ + inward[0] * 48, cy_ + inward[1] * 48)
        sa = math.atan2(inward[1], inward[0])
        mb.box('graphite', (stage_c[0], stage_c[1], 0), (14, 42, 1.2), sa)
        mb.box('bronze', (stage_c[0] - inward[0] * 7.05, stage_c[1] - inward[1] * 7.05, 1.2), (0.12, 42, 0.04), sa)
        sb = (stage_c[0] + inward[0] * 7.5, stage_c[1] + inward[1] * 7.5)
        MAT['screen_on'] = newmat('LED screen on', (0.02, 0.03, 0.05), 0.3, **{'Emission Color': (0.10, 0.16, 0.30), 'Emission Strength': 1.6})
        mb.box('screen_on', (sb[0], sb[1], 3.0), (0.6, 30, 12), sa)
        mb.box('led', (sb[0] - inward[0] * 0.31, sb[1] - inward[1] * 0.31, 3.0), (0.02, 30.2, 0.1), sa)
        mb.box('led', (sb[0] - inward[0] * 0.31, sb[1] - inward[1] * 0.31, 15.0), (0.02, 30.2, 0.1), sa)
        car_display(stage_c, sa + 1.3, 0, 'car_coupe', ('round', 3.6), z=1.2, mb=mb)
        for k in range(6):
            spot((stage_c[0] - inward[0] * 30 + inward[1] * (k - 2.5) * 8, stage_c[1] - inward[1] * 30 - inward[0] * (k - 2.5) * 8, HH - 4), (stage_c[0], stage_c[1], 1.5), 60000, 18)
        # seating: three fan blocks of telescopic tiers
        for blk, da in ((-1, -0.62), (0, 0.0), (1, 0.62)):
            d = sa + math.pi + da
            dirv = (math.cos(d), math.sin(d)); tv = (-dirv[1], dirv[0])
            for row in range(22):
                r = 22 + row * 0.9
                c = (stage_c[0] + dirv[0] * r, stage_c[1] + dirv[1] * r)
                w = 22 + row * 0.55
                zz = row * 0.42
                mb.box('graphite', (c[0], c[1], 0), (0.9, w, zz + 0.05), d)
                mb.box('seat', (c[0] + dirv[0] * 0.15, c[1] + dirv[1] * 0.15, zz + 0.05), (0.5, w - 0.6, 0.45), d)
                mb.box('seat', (c[0] + dirv[0] * 0.38, c[1] + dirv[1] * 0.38, zz + 0.05), (0.12, w - 0.6, 0.95), d)
            # aisle stair & handrail
            mb.box('bronze', (stage_c[0] + dirv[0] * 32 + tv[0] * 0, stage_c[1] + dirv[1] * 32, 10), (20, 0.05, 0.05), d)
        audience = SP()
        for blk, da in ((-1, -0.62), (0, 0.0), (1, 0.62)):
            pass
        back = 22 + 22 * 0.9 + 4
        cam_loc = (stage_c[0] - inward[0] * back + inward[1] * 6, stage_c[1] - inward[1] * back - inward[0] * 6, 22 * 0.42 + 3.2)
        camera(cam_loc, (stage_c[0], stage_c[1], 3.5), 24)
        sc.view_settings.exposure = -0.3
        people(40, halls.buffer(-3).difference(SP([(stage_c[0] + dx, stage_c[1] + dy) for dx, dy in ((-60, -60), (60, -60), (60, 60), (-60, 60))])))
        for m in bpy.data.materials:
            if m.name == 'Linear light': m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 12

# ======================================================================= WALL OF FAME MUSEUM (gallery; location TBC)
elif SCENE == 'museum':
    Lr, Wr, Hr = 64.0, 26.0, 9.0
    room = [(-Lr / 2, -Wr / 2), (Lr / 2, -Wr / 2), (Lr / 2, Wr / 2), (-Lr / 2, Wr / 2)]
    mb.prism(room, -0.1, 0.0, None, 'dark_floor')
    mb.prism(room, Hr, Hr + 0.2, None, None, 'acoustic')
    for (a, b) in zip(room, room[1:] + room[:1]):
        mb.face('walnut', [(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], Hr), (a[0], a[1], Hr)][::-1])
    # 'Wall of Fame': long north wall of illuminated milestone panels (content to be curated)
    for k in range(14):
        x = -Lr / 2 + 3 + k * 4.4
        mb.box('panel_frame', (x, Wr / 2 - 0.25, 1.4), (3.6, 0.2, 4.2))
        mb.box('panel_light', (x, Wr / 2 - 0.36, 1.6), (3.3, 0.02, 3.8))
        spot((x, Wr / 2 - 5, Hr - 0.3), (x, Wr / 2, 3.2), 900, 30)
    mb.box('led', (0, Wr / 2 - 0.4, 6.2), (Lr - 4, 0.04, 0.06))
    # timeline floor strip
    mb.box('bronze', (0, Wr / 2 - 3.2, 0.0), (Lr - 4, 0.12, 0.012))
    for k in range(15):
        mb.cyl('bronze', (-Lr / 2 + 3 + k * 4.4 - 1.1, Wr / 2 - 3.2, 0.0), 0.18, 0.015)
    # heritage vehicles on plinths, each with a free-standing story panel
    picks = [(-22, -2, 'car_sedan', 0, 0.3), (-8, 2.5, 'car_coupe', 6, -0.4), (6, -2.5, 'car_sedan_s', 3, 0.5), (20, 1.5, 'car_suv', 5, -0.3)]
    for x, y, kind, pi, rot in picks:
        car_display((x, y), rot, pi, kind, ('rect', 7.0, 4.0), mb=mb)
        mb.box('panel_frame', (x + 4.5, y - 3.0, 0), (1.4, 0.12, 1.9), 0.6)
        mb.box('panel_light', (x + 4.5 + 0.05, y - 3.0 - 0.08, 0.6), (1.2, 0.01, 1.1), 0.6)
        spot((x, y - 6, Hr - 0.3), (x, y, 0.6), 2600, 32)
        spot((x, y + 6, Hr - 0.3), (x, y, 0.6), 1600, 32)
    # glazed south wall to a shaded courtyard
    for k in range(9):
        x = -Lr / 2 + 4 + k * 7
        mb.box('bronze', (x, -Wr / 2 + 0.3, 0), (0.25, 0.25, Hr))
    mb.face('glass', [(-Lr / 2 + 2, -Wr / 2 + 0.2, 0), (Lr / 2 - 2, -Wr / 2 + 0.2, 0), (Lr / 2 - 2, -Wr / 2 + 0.2, 6.5), (-Lr / 2 + 2, -Wr / 2 + 0.2, 6.5)])
    for x in range(-28, 30, 7):
        area_light((x, 0, Hr - 0.05), (5, 1.2), 900, (1.0, 0.9, 0.78))
    sun_sky(200, 30, 2.0, 0.2)
    people(26, SP(room).buffer(-2), mix=(0.4, 0.35, 0.25))
    camera((-30, -10.5, 2.0), (6, 6, 1.6), 20)

# ======================================================================= SIMULATOR HALL
elif SCENE == 'simulator':
    Lr, Wr, Hr = 44.0, 26.0, 7.0
    room = [(-Lr / 2, -Wr / 2), (Lr / 2, -Wr / 2), (Lr / 2, Wr / 2), (-Lr / 2, Wr / 2)]
    mb.prism(room, -0.1, 0.0, None, 'dark_floor')
    mb.prism(room, Hr, Hr + 0.2, None, None, 'acoustic')
    for (a, b) in zip(room, room[1:] + room[:1]):
        mb.face('acoustic', [(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], Hr), (a[0], a[1], Hr)][::-1])
    # screen image: simple road/horizon render target (no third-party content)
    import numpy as np
    w_, h_ = 512, 256
    img = bpy.data.images.new('sim_screen', w_, h_)
    yy, xx = np.mgrid[0:h_, 0:w_] / np.array([h_, w_])[:, None, None]
    sky = np.stack([0.35 + 0.3 * yy, 0.5 + 0.3 * yy, 0.85 + 0.1 * yy], -1)
    ground = np.stack([0.55 - 0.2 * yy, 0.45 - 0.15 * yy, 0.30 - 0.1 * yy], -1)
    pix = np.where((yy < 0.48)[..., None], ground * 0.9, sky)
    road = (np.abs(xx - 0.5) < (0.48 - yy) * 0.9) & (yy < 0.48)
    pix[road] = [0.15, 0.15, 0.16]
    line = (np.abs(xx - 0.5) < 0.004) & (yy < 0.46) & ((yy * 40).astype(int) % 2 == 0)
    pix[line] = [0.9, 0.9, 0.85]
    rgba = np.concatenate([pix, np.ones((h_, w_, 1))], -1).astype(np.float32)
    img.pixels[:] = rgba.ravel(); img.pack()
    scr = bpy.data.materials.new('sim_screen'); scr.use_nodes = True; nt = scr.node_tree
    em = nt.nodes.new('ShaderNodeEmission'); ti = nt.nodes.new('ShaderNodeTexImage'); ti.image = img
    em.inputs['Strength'].default_value = 0.55
    nt.links.new(ti.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    MAT['simscreen'] = scr

    def rig(x, y, rot):
        cs, sn = math.cos(rot), math.sin(rot)
        P = lambda dx, dy, z: (x + dx * cs - dy * sn, y + dx * sn + dy * cs, z)
        mb.box('graphite', P(0, 0, 0), (3.0, 2.0, 0.35), rot)                     # motion platform
        mb.box('led', P(0, 0, 0.02), (3.06, 2.06, 0.04), rot)
        mb.box('seat', P(-0.5, 0, 0.35), (0.6, 0.55, 0.25), rot)                   # seat pan
        mb.box('seat', P(-0.85, 0, 0.55), (0.18, 0.55, 0.85), rot + 0.0)           # backrest
        mb.box('graphite', P(0.45, 0, 0.35), (0.12, 0.12, 0.55), rot)              # wheel column
        mb.box('graphite', P(0.42, 0, 0.92), (0.06, 0.34, 0.30), rot)              # wheel
        for k, a in ((-1, 0.55), (0, 0.0), (1, -0.55)):                             # triple screens
            cx_, cy_ = 1.45 + 0.25 * abs(k), k * 0.78
            px, py, _ = P(cx_, cy_, 0)
            mb.box('graphite', (px, py, 0.95), (0.06, 0.82, 0.5), rot + a)
            q = P(cx_ - 0.04, cy_, 0)
            # emissive face
            ang = rot + a; c2, s2 = math.cos(ang), math.sin(ang)
            hx, hz = 0.38, 0.22
            pts_ = [(q[0] - c2 * 0.0 - (-s2) * -hx, q[1] - s2 * 0.0 - c2 * -hx), (q[0] - (-s2) * hx, q[1] - c2 * hx)]
            mb.face('simscreen', [(q[0] + s2 * hx, q[1] - c2 * hx, 0.98), (q[0] - s2 * hx, q[1] + c2 * hx, 0.98), (q[0] - s2 * hx, q[1] + c2 * hx, 1.42), (q[0] + s2 * hx, q[1] - c2 * hx, 1.42)])
    for row in range(3):
        for col in range(6):
            rig(-14 + col * 4.4, -7 + row * 5.0, 0.0)
    # feature pod: 360° rig under a ring
    mb.cyl('graphite', (13, 4, 0), 3.4, 0.4, 48); mb.cyl('led', (13, 4, 0.4), 3.45, 0.03, 48)
    rig(13, 4, math.pi)
    for k in range(32):
        a = 2 * math.pi * k / 32
        mb.box('bronze', (13 + 3.3 * math.cos(a), 4 + 3.3 * math.sin(a), 4.6), (0.6, 0.12, 0.25), a + math.pi / 2)
    # lounge with leaderboard wall (blank)
    mb.box('screen', (Lr / 2 - 0.3, -6, 1.2), (0.2, 9, 3.6))
    mb.box('led', (Lr / 2 - 0.42, -6, 1.15), (0.02, 9.2, 0.05))
    for k in range(3):
        mb.box('leather', (12 + k * 2.6, -9.5, 0), (2.2, 0.9, 0.42)); mb.box('leather', (12 + k * 2.6, -9.95, 0.42), (2.2, 0.2, 0.45))
        mb.box('walnut', (12 + k * 2.6, -8.4, 0), (1.0, 0.6, 0.42))
    for x in range(-18, 22, 6):
        for y in (-8, 0, 8):
            mb.box('led', (x, y, Hr - 0.05), (4.5, 0.08, 0.04))
            area_light((x, y, Hr - 0.1), (4.5, 0.3), 70, (0.95, 0.92, 1.0))
    sun_sky(250, 10, 0.0, 0.0)
    people(22, SP(room).buffer(-1.5), mix=(0.5, 0.2, 0.3))
    camera((-21, -11.5, 2.3), (4, 2, 0.7), 20)
    for m in bpy.data.materials:
        if m.name == 'Linear light': m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 8

# ======================================================================= COLLECTORS' CLUB LOUNGE (ground-floor gallery of the DWG club bar)
elif SCENE == 'club_lounge':
    cc = next(z for z in Z if z['cls'] == 'collector_club')
    P = SP(cc['poly']).simplify(0.3)
    # local frame: long axis
    r = list(P.minimum_rotated_rectangle.exterior.coords)
    e1 = (r[1][0] - r[0][0], r[1][1] - r[0][1]); e2 = (r[2][0] - r[1][0], r[2][1] - r[1][1])
    if math.hypot(*e1) < math.hypot(*e2): e1, e2 = e2, e1
    Lx, Wy = math.hypot(*e1), math.hypot(*e2)
    u = (e1[0] / Lx, e1[1] / Lx); v = (-u[1], u[0]); c0 = P.centroid
    G = lambda s, t, z=0.0: (c0.x + u[0] * s + v[0] * t, c0.y + u[1] * s + v[1] * t, z)
    ang = math.atan2(u[1], u[0])
    Hr = 10.5
    inner = P.buffer(-0.8, join_style=2)
    ip = list(inner.exterior.coords)
    mb.prism(ip, -0.1, 0.0, None, 'club_floor')
    mb.prism(ip, Hr, Hr + 0.3, None, None, 'walnut')
    for i in range(len(ip) - 1):
        a, b = ip[i], ip[i + 1]
        mb.face('glass', [(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], Hr), (a[0], a[1], Hr)])
        L = math.dist(a, b); an = math.atan2(b[1] - a[1], b[0] - a[0])
        nx, ny = math.sin(an), -math.cos(an)
        for k in range(int(L // 1.4)):
            t = (k + 0.5) / int(L // 1.4); p = (a[0] + (b[0] - a[0]) * t + nx * 0.6, a[1] + (b[1] - a[1]) * t + ny * 0.6)
            mb.box('bronze', (p[0], p[1], 5.5), (0.1, 0.5, Hr - 5.5), an)
    # mezzanine gallery along one long side (double-height lounge)
    mz = [G(-Lx / 2 + 2, Wy / 2 - 9)[:2], G(Lx / 2 - 2, Wy / 2 - 9)[:2], G(Lx / 2 - 2, Wy / 2 - 1)[:2], G(-Lx / 2 + 2, Wy / 2 - 1)[:2]]
    mb.prism(mz, 5.0, 5.5, 'walnut', 'walnut', 'walnut')
    mb.box('glass', G(0, Wy / 2 - 9.05, 5.5), (Lx - 4, 0.04, 1.1), ang)
    mb.box('bronze', G(0, Wy / 2 - 9.05, 6.6), (Lx - 4, 0.08, 0.06), ang)
    for k in range(7):
        mb.box('bronze', G(-Lx / 2 + 8 + k * 16, Wy / 2 - 9.2, 0), (0.35, 0.35, 5.0), ang)
    # display cars on turntables + lounge settings
    for k, (s, t, kind, pi) in enumerate([(-38, -3, 'car_coupe', 3), (-14, -4, 'car_coupe', 6), (10, -3, 'car_sedan_s', 0), (34, -4, 'car_coupe', 1)]):
        g = G(s, t); car_display(g[:2], ang + 0.5 + k * 0.3, pi, kind, ('round', 3.3), mb=mb)
        spot(G(s, t - 6, Hr - 0.4), G(s, t, 0.5), 3500, 34)
    for s in (-26, -2, 22):
        g = G(s, 3.5)
        mb.cyl('rug', (g[0], g[1], 0.0), 3.6, 0.015, 48)
        for k in range(4):
            a2 = ang + k * math.pi / 2
            q = (g[0] + math.cos(a2) * 2.0, g[1] + math.sin(a2) * 2.0)
            mb.box('fabric_sofa', (q[0], q[1], 0), (0.95, 2.0 if k % 2 == 0 else 0.95, 0.42), a2)
            mb.box('fabric_sofa', (q[0] + math.cos(a2) * 0.4, q[1] + math.sin(a2) * 0.4, 0.42), (0.2, 2.0 if k % 2 == 0 else 0.95, 0.4), a2)
        mb.cyl('walnut', (g[0], g[1], 0), 0.8, 0.38, 32)
        area_light((g[0], g[1], Hr - 0.1), (3, 3), 600, (1.0, 0.85, 0.65), shape='DISK')
    # bar counter at the end wall
    mb.box('walnut', G(Lx / 2 - 6, 4, 0), (1.0, 12, 1.1), ang)
    mb.box('stone', G(Lx / 2 - 6, 4, 1.1), (1.2, 12.2, 0.06), ang)
    for s in range(-48, 50, 8):
        area_light(G(s, -6, Hr - 0.1), (5, 0.6), 900, (1.0, 0.86, 0.68))
    sun_sky(285, 4, 0.6, 0.35)
    people(16, inner.buffer(-2), mix=(0.55, 0.3, 0.15))
    camera(G(-Lx / 2 + 5, Wy / 2 - 9.6, 7.0), G(12, -5, 0.3), 20)
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(c0.x, c0.y, -0.15)); bpy.context.active_object.data.materials.append(MAT['land'])
    sc.view_settings.exposure = 0.3

mb.build('interior')
# figures read as toy-like near the lens: keep them >= 10 m from the camera
for o in list(bpy.data.objects):
    if o.name.startswith('fig_') and o.name.endswith('_i') or (o.name.startswith('fig_') and '_i' in o.name):
        if (Vector(o.location[:2]) - Vector(sc.camera.location[:2])).length < 10.0:
            bpy.data.objects.remove(o, do_unlink=True)
r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
sc.cycles.samples = SPP; sc.cycles.use_denoising = True; sc.cycles.adaptive_threshold = 0.02
sc.cycles.max_bounces = 8; sc.cycles.diffuse_bounces = 4; sc.cycles.glossy_bounces = 4; sc.cycles.transmission_bounces = 8
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False; sc.cycles.blur_glossy = 1.0
sc.view_settings.view_transform = 'AgX'
for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
    try: sc.view_settings.look = look; break
    except Exception: pass

def depth_override(sc, cam_obj, k):
    """ControlNet-style depth pass: inverse distance (near = white), no lighting, glass opaque."""
    import bpy
    m = bpy.data.materials.new('DEPTH_OVERRIDE'); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
    cd = nt.nodes.new('ShaderNodeCameraData'); dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'
    dv.inputs[0].default_value = k; nt.links.new(cd.outputs['View Distance'], dv.inputs[1])
    mn = nt.nodes.new('ShaderNodeMath'); mn.operation = 'MINIMUM'; mn.inputs[1].default_value = 1.0
    nt.links.new(dv.outputs[0], mn.inputs[0])
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mn.outputs[0], em.inputs['Strength'])
    nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    sc.view_layers[0].material_override = m
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    for o in bpy.data.objects:
        if o.type == 'LIGHT': o.hide_render = True
    for o in bpy.data.objects:   # instancing GN modifiers keep working; nothing else to do
        pass
    sc.cycles.samples = 8; sc.cycles.use_denoising = False; sc.cycles.max_bounces = 0
    try: sc.view_settings.view_transform = 'Raw'
    except Exception: sc.view_settings.view_transform = 'Standard'
    try: sc.view_settings.look = 'None'
    except Exception: pass
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.color_mode = 'BW'; sc.render.image_settings.color_depth = '16'

import os
if os.environ.get('JMD_DEPTH'):
    _c = sc.camera
    _look = Vector(VIEWS[VIEW]['look']) if 'VIEWS' in globals() and 'VIEW' in globals() else None
    _d = (Vector(LOOK) - _c.location).length
    depth_override(sc, _c, _d * 0.12)
r.filepath = OUT
bpy.ops.render.render(write_still=True)
print('wrote', OUT)
