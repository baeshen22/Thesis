"""Build the JMD district 3D model in Blender from model.json.

run:  bvenv/bin/python build_scene.py model.json ground_global.jpg out.blend
All footprints come from the DWG; architecture is applied per the JMD Visual Design Bible.
"""
import bpy, bmesh, json, math, random, sys
from mathutils import Vector, Matrix
from shapely.geometry import Polygon as SP

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
MODEL, GROUND, OUT = argv[0], argv[1], argv[2]
M = json.load(open(MODEL))
random.seed(11)
GX0, GY0, GX1, GY1 = -1100, -1000, 900, 900          # extent of the global ground texture

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ======================================================================= materials
def mat(name, base=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*base, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    for k, v in kw.items():
        inp = b.inputs[k]
        inp.default_value = (*v, 1) if isinstance(v, tuple) and len(v) == 3 else v
    return m


def add_noise_bump(m, scale=3.0, strength=0.08, detail=6.0):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = detail
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = strength
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return nz


def add_color_var(m, c1, c2, scale=0.4):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = (*c1, 1); mix.inputs['B'].default_value = (*c2, 1)
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])


MAT = {}
MAT['stone'] = mat('Limestone GRC', (0.70, 0.635, 0.54), 0.62)
add_noise_bump(MAT['stone'], 18, 0.03); add_color_var(MAT['stone'], (0.70, 0.635, 0.54), (0.66, 0.60, 0.51), 0.6)
MAT['stone_dark'] = mat('Stone warm grey', (0.46, 0.43, 0.39), 0.55)
MAT['white_metal'] = mat('Warm white aluminium', (0.70, 0.69, 0.66), 0.32, 0.25)
MAT['bronze'] = mat('Champagne bronze anodised', (0.40, 0.30, 0.19), 0.34, 0.9)
MAT['graphite'] = mat('Graphite panel', (0.055, 0.055, 0.06), 0.35, 0.3)
MAT['glass'] = mat('Architectural glass', (0.78, 0.84, 0.84), 0.015, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.5, 'Thin Wall': True})
MAT['glass_tinted'] = mat('Solar glass', (0.55, 0.60, 0.60), 0.02, 0.0, **{'Transmission Weight': 1.0, 'IOR': 1.5, 'Thin Wall': True})
MAT['floor'] = mat('Polished stone floor', (0.74, 0.72, 0.68), 0.12)
MAT['ceiling'] = mat('Interior ceiling light', (0.9, 0.88, 0.84), 0.6, **{'Emission Color': (1.0, 0.92, 0.80), 'Emission Strength': 1.6})
MAT['interior_wall'] = mat('Interior wall', (0.62, 0.60, 0.57), 0.7)
MAT['shed'] = mat('Metal cladding light grey', (0.66, 0.67, 0.68), 0.4, 0.5)
nt = MAT['shed'].node_tree
wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.inputs['Scale'].default_value = 2.2
tcs = nt.nodes.new('ShaderNodeTexCoord'); bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.25
nt.links.new(tcs.outputs['Object'], wv.inputs['Vector']); nt.links.new(wv.outputs['Fac'], bp.inputs['Height'])
nt.links.new(bp.outputs['Normal'], nt.nodes['Principled BSDF'].inputs['Normal'])
MAT['roof'] = mat('Roof membrane', (0.52, 0.50, 0.47), 0.75)
add_color_var(MAT['roof'], (0.54, 0.52, 0.49), (0.47, 0.455, 0.43), 0.08)
MAT['roof_metal'] = mat('Standing-seam roof', (0.42, 0.41, 0.38), 0.5, 0.2)
_nt = MAT['roof_metal'].node_tree; _wv = _nt.nodes.new('ShaderNodeTexWave'); _wv.wave_type = 'BANDS'; _wv.inputs['Scale'].default_value = 0.9
_tc = _nt.nodes.new('ShaderNodeTexCoord'); _bp = _nt.nodes.new('ShaderNodeBump'); _bp.inputs['Strength'].default_value = 0.35
_nt.links.new(_tc.outputs['Object'], _wv.inputs['Vector']); _nt.links.new(_wv.outputs['Fac'], _bp.inputs['Height']); _nt.links.new(_bp.outputs['Normal'], _nt.nodes['Principled BSDF'].inputs['Normal'])
MAT['timber'] = mat('Weathered timber', (0.28, 0.20, 0.13), 0.8)
MAT['context'] = mat('Context massing', (0.50, 0.47, 0.43), 0.85)
_n = MAT['context'].node_tree; _cd = _n.nodes.new('ShaderNodeCameraData'); _mr = _n.nodes.new('ShaderNodeMapRange')
_mr.inputs['From Min'].default_value = 300; _mr.inputs['From Max'].default_value = 2600
_mx = _n.nodes.new('ShaderNodeMix'); _mx.data_type = 'RGBA'; _mx.inputs['A'].default_value = (0.50, 0.47, 0.43, 1); _mx.inputs['B'].default_value = (0.60, 0.52, 0.44, 1)
_n.links.new(_cd.outputs['View Distance'], _mr.inputs['Value']); _n.links.new(_mr.outputs['Result'], _mx.inputs['Factor'])
_n.links.new(_mx.outputs['Result'], _n.nodes['Principled BSDF'].inputs['Base Color'])
MAT['door'] = mat('Roller door', (0.30, 0.31, 0.32), 0.5, 0.6)
MAT['concrete'] = mat('Concrete', (0.58, 0.56, 0.53), 0.75)
MAT['fabric'] = mat('Shade fabric', (0.92, 0.91, 0.88), 0.8, **{'Transmission Weight': 0.25, 'Thin Wall': True})
MAT['water'] = mat('Water', (0.10, 0.17, 0.17), 0.04, **{'Transmission Weight': 0.0})
MAT['rock'] = mat('Rock', (0.30, 0.22, 0.155), 0.85); add_noise_bump(MAT['rock'], 2.0, 0.6)
MAT['mech'] = mat('Rooftop plant', (0.55, 0.56, 0.56), 0.5, 0.4)
MAT['pole'] = mat('Pole', (0.35, 0.36, 0.37), 0.4, 0.8)
MAT['led'] = mat('Linear light', (1, 1, 1), 0.5, **{'Emission Color': (1.0, 0.86, 0.66), 'Emission Strength': 6.0})

# --- ground: global texture + optional hi-res local tile (swapped per camera)
g = bpy.data.materials.new('Ground'); g.use_nodes = True; nt = g.node_tree
b = nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = 0.85
geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(geo.outputs['Position'], sep.inputs['Vector'])


def uv_for(x0, y0, x1, y1, name):
    mx = nt.nodes.new('ShaderNodeMapRange'); mx.inputs['From Min'].default_value = x0; mx.inputs['From Max'].default_value = x1; mx.clamp = False
    my = nt.nodes.new('ShaderNodeMapRange'); my.inputs['From Min'].default_value = y0; my.inputs['From Max'].default_value = y1; my.clamp = False
    cb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(sep.outputs['X'], mx.inputs['Value']); nt.links.new(sep.outputs['Y'], my.inputs['Value'])
    nt.links.new(mx.outputs['Result'], cb.inputs['X']); nt.links.new(my.outputs['Result'], cb.inputs['Y'])
    mx.name = name + '_mx'; my.name = name + '_my'
    return cb


cg = uv_for(GX0, GY0, GX1, GY1, 'global')
tg = nt.nodes.new('ShaderNodeTexImage'); tg.name = 'tex_global'; tg.extension = 'EXTEND'; tg.interpolation = 'Cubic'
tg.image = bpy.data.images.load(GROUND)
nt.links.new(cg.outputs['Vector'], tg.inputs['Vector'])
cl = uv_for(0, 0, 1, 1, 'local')
tl = nt.nodes.new('ShaderNodeTexImage'); tl.name = 'tex_local'; tl.extension = 'CLIP'; tl.interpolation = 'Cubic'
_ph = bpy.data.images.new('no_tile', 4, 4, alpha=True); _ph.pixels[:] = [0.0] * 64; _ph.pack(); tl.image = _ph
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.name = 'mix_local'
nt.links.new(cl.outputs['Vector'], tl.inputs['Vector'])
nt.links.new(tg.outputs['Color'], mix.inputs['A']); nt.links.new(tl.outputs['Color'], mix.inputs['B'])
nt.links.new(tl.outputs['Alpha'], mix.inputs['Factor'])
mix.inputs['Factor'].default_value = 0
# far field: blend to procedural sand beyond the texture
sand_nz = nt.nodes.new('ShaderNodeTexNoise'); sand_nz.inputs['Scale'].default_value = 0.004
sand_mix = nt.nodes.new('ShaderNodeMix'); sand_mix.data_type = 'RGBA'
sand_mix.inputs['A'].default_value = (0.47, 0.335, 0.18, 1); sand_mix.inputs['B'].default_value = (0.41, 0.29, 0.155, 1)
tcg = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tcg.outputs['Object'], sand_nz.inputs['Vector'])
nt.links.new(sand_nz.outputs['Fac'], sand_mix.inputs['Factor'])
# inside-texture mask
ins = nt.nodes.new('ShaderNodeMath'); ins.operation = 'COMPARE'
far = nt.nodes.new('ShaderNodeMix'); far.data_type = 'RGBA'
# mask = |x|<GX and y in range, approximated via distance from texture centre
cxn = nt.nodes.new('ShaderNodeVectorMath'); cxn.operation = 'SUBTRACT'
cxn.inputs[1].default_value = ((GX0 + GX1) / 2, (GY0 + GY1) / 2, 0)
nt.links.new(geo.outputs['Position'], cxn.inputs[0])
ab = nt.nodes.new('ShaderNodeVectorMath'); ab.operation = 'ABSOLUTE'; nt.links.new(cxn.outputs[0], ab.inputs[0])
sx = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(ab.outputs[0], sx.inputs[0])
mxv = nt.nodes.new('ShaderNodeMath'); mxv.operation = 'MAXIMUM'; nt.links.new(sx.outputs['X'], mxv.inputs[0]); nt.links.new(sx.outputs['Y'], mxv.inputs[1])
sm = nt.nodes.new('ShaderNodeMapRange'); sm.inputs['From Min'].default_value = (GY1 - GY0) / 2 - 60; sm.inputs['From Max'].default_value = (GY1 - GY0) / 2 - 2
nt.links.new(mxv.outputs[0], sm.inputs['Value'])
nt.links.new(sm.outputs['Result'], far.inputs['Factor'])
nt.links.new(mix.outputs['Result'], far.inputs['A']); nt.links.new(sand_mix.outputs['Result'], far.inputs['B'])
camd = nt.nodes.new('ShaderNodeCameraData')
hz = nt.nodes.new('ShaderNodeMapRange'); hz.inputs['From Min'].default_value = 1400; hz.inputs['From Max'].default_value = 9000
hz.interpolation_type = 'SMOOTHSTEP'
nt.links.new(camd.outputs['View Distance'], hz.inputs['Value'])
hzm = nt.nodes.new('ShaderNodeMix'); hzm.data_type = 'RGBA'; hzm.name = 'haze_mix'
hzm.inputs['B'].default_value = (0.62, 0.52, 0.42, 1)
nt.links.new(hz.outputs['Result'], hzm.inputs['Factor'])
nt.links.new(far.outputs['Result'], hzm.inputs['A'])
nt.links.new(hzm.outputs['Result'], b.inputs['Base Color'])
gb = nt.nodes.new('ShaderNodeBump'); gb.inputs['Strength'].default_value = 0.05
gn = nt.nodes.new('ShaderNodeTexNoise'); gn.inputs['Scale'].default_value = 40
nt.links.new(tcg.outputs['Object'], gn.inputs['Vector']); nt.links.new(gn.outputs['Fac'], gb.inputs['Height'])
nt.links.new(gb.outputs['Normal'], b.inputs['Normal'])
MAT['ground'] = g

# --- vehicle materials (colour varies per instance)
cp = bpy.data.materials.new('Car paint'); cp.use_nodes = True; nt = cp.node_tree
b = nt.nodes['Principled BSDF']; b.inputs['Metallic'].default_value = 0.55; b.inputs['Roughness'].default_value = 0.28
b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.04
oi = nt.nodes.new('ShaderNodeObjectInfo'); ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.interpolation = 'CONSTANT'
cols = [(0.0, (0.80, 0.80, 0.78)), (0.30, (0.55, 0.56, 0.57)), (0.48, (0.02, 0.02, 0.022)), (0.64, (0.18, 0.19, 0.20)),
        (0.76, (0.04, 0.07, 0.14)), (0.84, (0.45, 0.40, 0.33)), (0.92, (0.40, 0.03, 0.03)), (0.97, (0.10, 0.16, 0.12))]
ramp.color_ramp.elements[0].position = cols[0][0]; ramp.color_ramp.elements[0].color = (*cols[0][1], 1)
ramp.color_ramp.elements[1].position = cols[1][0]; ramp.color_ramp.elements[1].color = (*cols[1][1], 1)
for p_, c_ in cols[2:]:
    e = ramp.color_ramp.elements.new(p_); e.color = (*c_, 1)
nt.links.new(oi.outputs['Random'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
MAT['carpaint'] = cp
MAT['cover'] = mat('Reveal cover', (0.22, 0.22, 0.23), 0.7, **{'Sheen Weight': 0.6})
MAT['carglass'] = mat('Car glass', (0.03, 0.035, 0.04), 0.03, 0.0, **{'Specular IOR Level': 0.7})
MAT['tyre'] = mat('Tyre', (0.025, 0.025, 0.025), 0.75)
MAT['rim'] = mat('Rim', (0.6, 0.6, 0.6), 0.25, 1.0)
MAT['lamp_f'] = mat('Head lamp', (0.9, 0.9, 0.9), 0.1, **{'Emission Color': (1, .95, .85), 'Emission Strength': 0.0})
MAT['lamp_r'] = mat('Tail lamp', (0.35, 0.02, 0.02), 0.2, **{'Emission Color': (1, .05, .03), 'Emission Strength': 0.0})
MAT['trim'] = mat('Black trim', (0.03, 0.03, 0.03), 0.4)
MAT['bark'] = mat('Palm trunk', (0.33, 0.26, 0.19), 0.9); add_noise_bump(MAT['bark'], 30, 0.5)
leaf = mat('Palm frond', (0.12, 0.135, 0.065), 0.6, **{'Subsurface Weight': 0.0})
nt = leaf.node_tree
tr = nt.nodes.new('ShaderNodeBsdfTranslucent'); tr.inputs['Color'].default_value = (0.16, 0.19, 0.05, 1)
ms = nt.nodes.new('ShaderNodeMixShader'); ms.inputs['Fac'].default_value = 0.15
out = nt.nodes['Material Output']
nt.links.new(nt.nodes['Principled BSDF'].outputs[0], ms.inputs[1]); nt.links.new(tr.outputs[0], ms.inputs[2]); nt.links.new(ms.outputs[0], out.inputs['Surface'])
oi2 = nt.nodes.new('ShaderNodeObjectInfo'); hsv = nt.nodes.new('ShaderNodeHueSaturation')
hsv.inputs['Color'].default_value = (0.12, 0.135, 0.065, 1)
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.75; mr.inputs['To Max'].default_value = 1.25
nt.links.new(oi2.outputs['Random'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], hsv.inputs['Value'])
nt.links.new(hsv.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
MAT['leaf'] = leaf
MAT['shrub'] = mat('Shrub', (0.10, 0.14, 0.05), 0.8)
MAT['thobe'] = mat('Thobe white', (0.86, 0.86, 0.84), 0.75, **{'Sheen Weight': 0.3})
MAT['abaya'] = mat('Abaya black', (0.025, 0.025, 0.03), 0.6, **{'Sheen Weight': 0.4})
MAT['casual_top'] = mat('Casual top', (0.30, 0.36, 0.44), 0.8)
MAT['casual_leg'] = mat('Casual trousers', (0.12, 0.12, 0.14), 0.8)
MAT['skin'] = mat('Skin', (0.42, 0.28, 0.20), 0.5)
MAT['shemagh'] = mat('Shemagh', (0.85, 0.84, 0.82), 0.8)


# ======================================================================= mesh builder
class MB:
    def __init__(self):
        self.d = {}

    def _b(self, m):
        if m not in self.d: self.d[m] = ([], [])
        return self.d[m]

    def face(self, m, pts):
        v, f = self._b(m); i = len(v); v.extend(pts); f.append(list(range(i, i + len(pts))))

    def quad(self, m, a, b, c, d):
        self.face(m, [a, b, c, d])

    def prism(self, poly, z0, z1, side, top=None, bottom=None, side_fn=None):
        n = len(poly)
        if poly[0] == poly[-1]: poly = poly[:-1]; n -= 1
        # ensure CCW
        area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
        if area < 0: poly = poly[::-1]
        for i in range(n):
            a, b_ = poly[i], poly[(i + 1) % n]
            m = side
            if side_fn:
                ex, ey = b_[0] - a[0], b_[1] - a[1]; l = math.hypot(ex, ey) or 1
                m = side_fn((ey / l, -ex / l), a, b_)
                if m is None: continue
            self.quad(m, (a[0], a[1], z0), (b_[0], b_[1], z0), (b_[0], b_[1], z1), (a[0], a[1], z1))
        if top: self.face(top, [(x, y, z1) for x, y in poly])
        if bottom: self.face(bottom, [(x, y, z0) for x, y in poly[::-1]])

    def box(self, m, c, size, rot=0.0, mtop=None):
        hx, hy = size[0] / 2, size[1] / 2
        cs, sn = math.cos(rot), math.sin(rot)
        pts = [(c[0] + x * cs - y * sn, c[1] + x * sn + y * cs) for x, y in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]
        self.prism(pts, c[2], c[2] + size[2], m, mtop or m, m)

    def build(self, name, smooth=False):
        objs = []
        for m, (v, f) in self.d.items():
            if not f: continue
            me = bpy.data.meshes.new(f'{name}_{m}')
            me.from_pydata(v, [], f); me.validate(); me.update()
            me.materials.append(MAT[m])
            ob = bpy.data.objects.new(f'{name}_{m}', me)
            bpy.context.collection.objects.link(ob)
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me); bm.free()
            for p in me.polygons: p.use_smooth = smooth
            objs.append(ob)
        return objs


def offset(p, d, v):
    return (p[0] + v[0] * d, p[1] + v[1] * d)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def edges_of(poly, tol=0.25):
    # arc-tessellated DWG fronts: simplify (sagitta over a 20 m unit is ~0.04 m) so facade features apply per facade, not per segment
    _P = SP(poly).simplify(tol, preserve_topology=True)
    poly = [tuple(p) for p in _P.exterior.coords]
    pts = poly[:-1] if poly[0] == poly[-1] else poly
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    if area < 0: pts = pts[::-1]
    out = []
    for i in range(n):
        a, b_ = pts[i], pts[(i + 1) % n]
        ex, ey = b_[0] - a[0], b_[1] - a[1]; l = math.hypot(ex, ey)
        if l < 0.05: continue
        out.append((a, b_, (ey / l, -ex / l), l))
    return pts, out


def merge_colinear(edges, front):
    """classify each edge as front/back/side relative to the unit's front vector"""
    res = []
    for a, b_, n, l in edges:
        d = n[0] * front[0] + n[1] * front[1]
        res.append((a, b_, n, l, 'front' if d > 0.75 else ('back' if d < -0.75 else 'side')))
    return res


def inset_poly(poly, d):
    from shapely.geometry import Polygon
    P = Polygon(poly).buffer(-d, join_style=2)
    return list(P.exterior.coords) if not P.is_empty else poly


def grow_poly(poly, d):
    from shapely.geometry import Polygon
    return list(Polygon(poly).buffer(d, join_style=2).exterior.coords)


mb = MB()          # buildings
Z = M['zones']

# ----------------------------------------------------------------------- showrooms
SH = {'showroom_standard': 9.0, 'showroom_premium': 10.5, 'showroom_flagship': 13.0, 'showroom_flagship_plus': 14.0}
idx = 0
for z in Z:
    if z['cls'] not in SH: continue
    H = SH[z['cls']] + random.choice((0, 0, 0.6))
    poly = z['poly']; f = z['front']
    pts, eds = edges_of(poly)
    eds = merge_colinear(eds, f)
    # facade variant within the shared district language (design bible kit-of-parts)
    if z['cls'] in ('showroom_flagship', 'showroom_flagship_plus'): var = ('frame', 'angled')[idx % 2]
    elif z['cls'] == 'showroom_premium': var = ('louvre', 'stone', 'frame')[idx % 3]
    else: var = ('minimal', 'louvre', 'minimal', 'stone')[idx % 4]
    idx += 1
    mb.prism(pts, 0, 0.35, 'stone_dark', 'floor')
    band = 2.0
    for a, b_, n, l, kind in eds:
        if kind == 'front':
            if var == 'stone':
                # 30 % solid stone pier at one end + glass
                t = 0.3 if idx % 2 else 0.7
                ms = lerp(a, b_, t)
                if idx % 2:
                    mb.quad('stone', (*a, 0.35), (*ms, 0.35), (*ms, H - band), (*a, H - band)); ga = ms; gb_ = b_
                else:
                    mb.quad('stone', (*ms, 0.35), (*b_, 0.35), (*b_, H - band), (*ms, H - band)); ga = a; gb_ = ms
                mb.quad('glass', (*ga, 0.35), (*gb_, 0.35), (*gb_, H - band), (*ga, H - band))
            else:
                mb.quad('glass', (*a, 0.35), (*b_, 0.35), (*b_, H - band), (*a, H - band))
            # mullions every 2.5 m
            k = int(l // 2.5)
            for j in range(1, k + 1):
                p = lerp(a, b_, j / (k + 1))
                mb.box('graphite', (p[0], p[1], 0.35), (0.12, 0.12, H - band - 0.35), math.atan2(b_[1] - a[1], b_[0] - a[0]))
            # brand band (left blank for brand identity — no invented logos)
            mb.quad('graphite', (*a, H - band), (*b_, H - band), (*b_, H), (*a, H))
            if var == 'louvre':
                k = int(l // 0.9)
                for j in range(1, k):
                    p = offset(lerp(a, b_, j / k), 0.3, n)
                    mb.box('bronze', (p[0], p[1], 0.35), (0.07, 0.45, H - band - 0.35), math.atan2(b_[1] - a[1], b_[0] - a[0]))
            if var == 'frame':
                for p in (a, b_):
                    q = offset(p, 0.9, n)
                    mb.box('stone', (q[0], q[1], 0.35), (1.1, 1.8, H + 0.6 - 0.35), math.atan2(b_[1] - a[1], b_[0] - a[0]))
                qa, qb = offset(a, 0.9, n), offset(b_, 0.9, n)
                mid = lerp(qa, qb, 0.5)
                mb.box('stone', (mid[0], mid[1], H - 0.1), (l + 1.1, 1.8, 0.9), math.atan2(b_[1] - a[1], b_[0] - a[0]))
        elif kind == 'back':
            mb.quad('glass_tinted', (*a, 0.35), (*b_, 0.35), (*b_, 5.0), (*a, 5.0))
            mb.quad('stone', (*a, 5.0), (*b_, 5.0), (*b_, H), (*a, H))
        else:
            mb.quad('stone', (*a, 0.35), (*b_, 0.35), (*b_, H), (*a, H))
            # bronze blade fin at each party edge, projecting toward the street
    # fins at the two front corners
    fr = [e for e in eds if e[4] == 'front']
    if fr:
        a = fr[0][0]; b_ = fr[-1][1]; n = fr[0][2]
        for p in (a, b_):
            q = offset(p, 1.0, n)
            mb.box('bronze', (q[0], q[1], 0.0), (0.35, 2.4, H + 0.55), math.atan2(n[1], n[0]) + math.pi / 2)
    # interior display wall (back-of-house behind) at ~60 % depth, parallel to the glazed front
    if fr:
        Pp = SP(pts); cpp = Pp.centroid
        depth = max(((x - cpp.x) * f[0] + (y - cpp.y) * f[1]) for x, y in pts) - min(((x - cpp.x) * f[0] + (y - cpp.y) * f[1]) for x, y in pts)
        tvec = (-f[1], f[0]); dfront = max(((x - cpp.x) * f[0] + (y - cpp.y) * f[1]) for x, y in pts)
        wpos = (cpp.x + f[0] * (dfront - depth * 0.6), cpp.y + f[1] * (dfront - depth * 0.6))
        wl = SP([(wpos[0] + tvec[0] * s_ + f[0] * e_, wpos[1] + tvec[1] * s_ + f[1] * e_) for s_, e_ in ((-60, -0.15), (60, -0.15), (60, 0.15), (-60, 0.15))]).intersection(Pp.buffer(-0.2))
        if not wl.is_empty and wl.geom_type == 'Polygon':
            mb.prism(list(wl.exterior.coords), 0.35, H - band - 0.05, 'interior_wall', 'interior_wall')
    # interior ceiling (emissive) + roof slab with front canopy
    mb.prism(inset_poly(pts, 0.05), H - band - 0.05, H - band, 'ceiling', None, 'ceiling')
    roof = pts
    from shapely.geometry import Polygon as SP
    canopy = SP(pts).union(SP([offset(p, 3.2, f) for p in pts])).convex_hull.buffer(0.25, join_style=2)
    if var == 'angled':
        cpts = list(canopy.exterior.coords)[:-1]
        cen = SP(pts).centroid
        verts_top = []
        for x, y in cpts:
            t = ((x - cen.x) * f[0] + (y - cen.y) * f[1])
            verts_top.append((x, y, H + 0.6 + max(0, t) * 0.12))
        mb.face('white_metal', verts_top)
        mb.face('white_metal', [(x, y, z_ - 0.5) for x, y, z_ in verts_top[::-1]])
        for i in range(len(verts_top)):
            p1, p2 = verts_top[i], verts_top[(i + 1) % len(verts_top)]
            mb.quad('white_metal', (p1[0], p1[1], p1[2] - 0.5), (p2[0], p2[1], p2[2] - 0.5), p2, p1)
    else:
        mb.prism(list(canopy.exterior.coords), H, H + 0.6, 'white_metal', 'roof', 'white_metal')
    # rooftop plant
    c = SP(pts).centroid
    if random.random() < 0.7:
        mb.box('mech', (c.x - f[0] * 4, c.y - f[1] * 4, H + 0.6), (2.4, 1.6, 1.4), math.atan2(f[1], f[0]))

# ----------------------------------------------------------------------- lifestyle shops + shaded arcade
for z in Z:
    if z['cls'] != 'shop': continue
    pts, eds = edges_of(z['poly']); f = z['front']; eds = merge_colinear(eds, f)
    H = 8.0
    mb.prism(pts, 0, 0.2, 'stone_dark', 'floor')
    for a, b_, n, l, kind in eds:
        if kind == 'front':
            mb.quad('glass', (*a, 0.2), (*b_, 0.2), (*b_, 4.6), (*a, 4.6))
            mb.quad('stone', (*a, 4.6), (*b_, 4.6), (*b_, H), (*a, H))
            k = int(l // 3.0)
            for j in range(1, k + 1):
                p = lerp(a, b_, j / (k + 1))
                mb.box('bronze', (p[0], p[1], 0.2), (0.1, 0.15, 4.4), math.atan2(b_[1] - a[1], b_[0] - a[0]))
            # arcade: 5.5 m deep canopy on slender columns
            qa, qb = offset(a, 5.5, n), offset(b_, 5.5, n)
            mb.face('white_metal', [(*a, 5.0), (*b_, 5.0), (*qb, 5.0), (*qa, 5.0)][::-1])
            mb.face('white_metal', [(*a, 5.45), (*b_, 5.45), (*qb, 5.45), (*qa, 5.45)])
            mb.quad('white_metal', (*qa, 5.0), (*qb, 5.0), (*qb, 5.45), (*qa, 5.45))
            mb.face('led', [(*offset(a, 5.0, n), 4.99), (*offset(b_, 5.0, n), 4.99), (*offset(b_, 5.2, n), 4.99), (*offset(a, 5.2, n), 4.99)][::-1])
            for j in range(0, int(l // 6) + 1):
                p = offset(lerp(a, b_, (j + 0.5) / (int(l // 6) + 1)), 5.1, n)
                mb.box('bronze', (p[0], p[1], 0.0), (0.22, 0.22, 5.0))
        elif kind == 'back':
            mb.quad('stone', (*a, 0.2), (*b_, 0.2), (*b_, H), (*a, H))
            m_ = lerp(a, b_, 0.5); q = offset(m_, 0.03, n)
            mb.box('door', (q[0], q[1], 0.2), (3.0, 0.05, 3.0), math.atan2(b_[1] - a[1], b_[0] - a[0]))
        else:
            mb.quad('stone', (*a, 0.2), (*b_, 0.2), (*b_, H), (*a, H))
    mb.prism(inset_poly(pts, 0.05), 4.5, 4.55, 'ceiling', None, 'ceiling')
    mb.prism(grow_poly(pts, 0.15), H, H + 0.5, 'white_metal', 'roof')
    from shapely.geometry import Polygon as SP
    c = SP(pts).centroid
    mb.box('mech', (c.x, c.y, H + 0.5), (3.0, 2.0, 1.5), math.atan2(f[1], f[0]))

# ----------------------------------------------------------------------- light service & spare-part units
for z in Z:
    if z['cls'] != 'service_unit': continue
    pts, eds = edges_of(z['poly']); f = z['front']; eds = merge_colinear(eds, f)
    H = 9.0
    mb.prism(pts, 0, H, 'shed', 'roof')
    from shapely.geometry import Polygon as SP
    for a, b_, n, l, kind in eds:
        if kind == 'front':
            m_ = lerp(a, b_, 0.62); q = offset(m_, 0.04, n)
            mb.box('door', (q[0], q[1], 0), (5.5, 0.06, 5.5), math.atan2(b_[1] - a[1], b_[0] - a[0]))
            m2 = lerp(a, b_, 0.18); q2 = offset(m2, 0.04, n)
            mb.box('glass_tinted', (q2[0], q2[1], 0.3), (5.0, 0.06, 6.2), math.atan2(b_[1] - a[1], b_[0] - a[0]))
            qa, qb = offset(a, 2.5, n), offset(b_, 2.5, n)
            mb.prism([a, b_, qb, qa], 6.4, 6.7, 'white_metal', 'white_metal', 'white_metal')
    c = SP(pts).centroid
    mb.box('roof', (c.x, c.y, H), (1.4, 14.0, 0.25), math.atan2(f[1], f[0]))

# ----------------------------------------------------------------------- arena
from shapely.geometry import Polygon as SP
from shapely.ops import unary_union
halls = unary_union([SP(z['poly']) for z in Z if z['cls'] == 'arena_hall']).buffer(1.0, join_style=2)
outer = SP(M['arena_outer'])
AH = 21.0
hall_pts = list(halls.exterior.coords)
pts, eds = edges_of(hall_pts)
# glazed concourse 0-7.5 m, then champagne metal fins over solid backing up to the roof
for a, b_, n, l, _ in [(e[0], e[1], e[2], e[3], '') for e in eds]:
    mb.quad('glass', (*a, 0.0), (*b_, 0.0), (*b_, 7.5), (*a, 7.5))
    mb.quad('stone_dark', (*a, 7.5), (*b_, 7.5), (*b_, AH), (*a, AH))
    k = int(l // 1.6)
    for j in range(k):
        p = offset(lerp(a, b_, (j + 0.5) / k), 0.55, n)
        mb.box('bronze', (p[0], p[1], 7.5), (0.12, 0.9, AH - 7.5 - 0.2), math.atan2(b_[1] - a[1], b_[0] - a[0]))
    mb.quad('white_metal', (*offset(a, 1.0, n), 7.5), (*offset(b_, 1.0, n), 7.5), (*b_, 7.5), (*a, 7.5))
mb.prism(inset_poly(hall_pts, 0.1), 0.0, 0.15, 'floor', 'floor')
mb.prism(inset_poly(hall_pts, 0.1), 7.3, 7.4, 'ceiling', None, 'ceiling')
# floating roof over the whole outer triangle (deep shade over the concourse)
roof_poly = list(outer.buffer(2.0, join_style=1).exterior.coords)
mb.prism(roof_poly, AH, AH + 3.2, 'white_metal', 'roof_metal', 'white_metal')
rp = SP(roof_poly)
# roof skylight strips parallel to the long side
minx, miny, maxx, maxy = rp.bounds
for k in range(6):
    t = (k + 1) / 7
    from shapely.geometry import LineString
    hall_c = halls.centroid
    ln = LineString([(hall_c.x - 200, miny + (maxy - miny) * t - 60), (hall_c.x + 200, miny + (maxy - miny) * t + 60)]).intersection(halls.buffer(-8))
    for g_ in getattr(ln, 'geoms', [ln]):
        if g_.is_empty or g_.length < 10: continue
        (x0_, y0_), (x1_, y1_) = g_.coords[0], g_.coords[-1]
        L = g_.length; ang = math.atan2(y1_ - y0_, x1_ - x0_)
        mb.box('glass_tinted', ((x0_ + x1_) / 2, (y0_ + y1_) / 2, AH + 3.2), (L, 3.0, 0.35), ang)
# perimeter columns along the roof edge
ring = outer.buffer(-1.0, join_style=1).exterior
s = 0
while s < ring.length:
    p = ring.interpolate(s)
    if not halls.buffer(1.5).contains(p):
        mb.prism([(p.x + 0.65 * math.cos(t_ * math.pi / 8), p.y + 0.65 * math.sin(t_ * math.pi / 8)) for t_ in range(16)], 0, AH, 'white_metal')
    s += 19.0
# glazed entrance portal on the hall face nearest the launch plaza
_opc = SP(max([z for z in Z if z['cls'] == 'outdoor_plaza'], key=lambda z: z['area'])['poly']).centroid
_e = min(eds, key=lambda e: math.dist(lerp(e[0], e[1], 0.5), (_opc.x, _opc.y)))
_a, _b, _n, _l = _e[0], _e[1], _e[2], _e[3]
_m = lerp(_a, _b, 0.5); _ang = math.atan2(_b[1] - _a[1], _b[0] - _a[0]); _w = min(34.0, _l * 0.7)
_c = offset(_m, 3.0, _n)
mb.box('glass', (_c[0], _c[1], 0), (_w, 6.0, 15.0), _ang)
for _s in (-1, 1):
    _q = (_c[0] + math.cos(_ang) * _s * (_w / 2 + 0.9), _c[1] + math.sin(_ang) * _s * (_w / 2 + 0.9))
    mb.box('bronze', (_q[0], _q[1], 0), (1.8, 7.0, 16.5), _ang)
mb.box('bronze', (_c[0], _c[1], 15.0), (_w + 3.6, 7.0, 1.5), _ang)
for _k in range(1, 8):
    _q = (_c[0] + math.cos(_ang) * (-_w / 2 + _w * _k / 8) + _n[0] * 3.0, _c[1] + math.sin(_ang) * (-_w / 2 + _w * _k / 8) + _n[1] * 3.0)
    mb.box('graphite', (_q[0], _q[1], 0), (0.18, 0.3, 15.0), _ang)

# ----------------------------------------------------------------------- collectors' club (3 levels)
cc = next(z for z in Z if z['cls'] == 'collector_club')
pts, eds = edges_of(cc['poly'])
P = SP(pts)
levels = [(0.0, 5.5), (5.5, 10.5), (10.5, 15.5)]
for i, (z0, z1) in enumerate(levels):
    inner = inset_poly(pts, 1.6 if i else 0.8)
    e_in = edges_of(inner)[1]
    for a, b_, n, l in e_in:
        mb.quad('glass_tinted' if i else 'glass', (*a, z0 + 0.6), (*b_, z0 + 0.6), (*b_, z1), (*a, z1))
        if i:
            k = int(l // 1.4)
            for j in range(k):
                p = offset(lerp(a, b_, (j + 0.5) / k), 1.0, n)
                mb.box('bronze', (p[0], p[1], z0 + 0.6), (0.1, 0.5, z1 - z0 - 0.6), math.atan2(b_[1] - a[1], b_[0] - a[0]))
    mb.prism(grow_poly(pts, 2.2 if i else 1.2), z0, z0 + 0.6, 'graphite' if i == 0 else 'white_metal', 'floor' if i == 0 else 'white_metal', 'white_metal')
    mb.prism(inset_poly(inner, 0.1), z1 - 0.06, z1 - 0.02, 'ceiling', None, 'ceiling')
mb.prism(grow_poly(pts, 2.2), 15.5, 16.4, 'white_metal', 'roof', 'white_metal')
# roof-terrace pergola
for k in range(12):
    t = (k + 0.5) / 12
    eL = max(eds, key=lambda e: e[3])
    p = lerp(eL[0], eL[1], t); q = offset(p, -12, eL[2])
    mb.box('bronze', ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, 19.2), (0.25, 12.0, 0.25), math.atan2(eL[2][1], eL[2][0]) + math.pi / 2)
for t in (0.1, 0.5, 0.9):
    eL = max(eds, key=lambda e: e[3])
    for dd in (-1.0, -11.0):
        p = offset(lerp(eL[0], eL[1], t), dd, eL[2])
        mb.box('bronze', (p[0], p[1], 16.4), (0.25, 0.25, 2.8))
# valet canopy on the long side facing the main internal drive (south)
eS = min([e for e in eds if e[3] > 50], key=lambda e: e[2][1])
mid = lerp(eS[0], eS[1], 0.5); ang = math.atan2(eS[1][1] - eS[0][1], eS[1][0] - eS[0][0])
cpos = offset(mid, 6.0, eS[2])
mb.box('white_metal', (cpos[0], cpos[1], 5.0), (26.0, 10.0, 0.5), ang)
for dx in (-11, 11):
    q = (cpos[0] + math.cos(ang) * dx + eS[2][0] * 3.5, cpos[1] + math.sin(ang) * dx + eS[2][1] * 3.5)
    mb.box('bronze', (q[0], q[1], 0), (0.4, 0.4, 5.0))

# ----------------------------------------------------------------------- other buildings
def simple_building(z, H, wall='stone', glazing=0.45, roofm='roof'):
    pts, eds = edges_of(z['poly'])
    for a, b_, n, l in eds:
        mb.quad(wall, (*a, 0), (*b_, 0), (*b_, H), (*a, H))
        if l > 6:
            nb = int(l // 7)
            for j in range(nb):
                t0 = (j + 0.5 - glazing / 2) / nb; t1 = (j + 0.5 + glazing / 2) / nb
                p0, p1 = offset(lerp(a, b_, t0), 0.03, n), offset(lerp(a, b_, t1), 0.03, n)
                for fl in range(int(H // 4.5)):
                    zz = 0.6 + fl * 4.5
                    mb.quad('glass_tinted', (*p0, zz), (*p1, zz), (*p1, zz + 3.0), (*p0, zz + 3.0))
    mb.prism(grow_poly(pts, 0.2), H, H + 0.6, 'white_metal', roofm)
    return pts, eds


for z in Z:
    c = z['cls']
    if c in ('management', 'commercial_block'):
        simple_building(z, 9.5 if c == 'management' else 10.0)
    elif c in ('mosque_small', 'mosque_large'):
        pts, eds = simple_building(z, 9.0 if c == 'mosque_small' else 12.0, glazing=0.25)
        P = SP(pts); minx, miny, maxx, maxy = P.bounds
        # minaret at the corner nearest the frontage road
        corner = min(pts, key=lambda p: math.dist(p, M['C_NW']) * -1)
        q = lerp(corner, (P.centroid.x, P.centroid.y), 0.12)
        Hm = 28 if c == 'mosque_small' else 34
        mb.box('stone', (q[0], q[1], 0), (3.6, 3.6, Hm))
        mb.box('bronze', (q[0], q[1], Hm - 5), (3.8, 3.8, 3.2))
        mb.box('white_metal', (q[0], q[1], Hm), (4.2, 4.2, 0.5))
    elif c == 'testdrive_building':
        pts, eds = edges_of(z['poly'])
        inner = inset_poly(pts, 6)
        for a, b_, n, l in edges_of(inner)[1]:
            mb.quad('glass', (*a, 0), (*b_, 0), (*b_, 5.0), (*a, 5.0))
        mb.prism(inset_poly(inner, 0.1), 0, 0.15, 'floor', 'floor')
        mb.prism(inset_poly(inner, 0.1), 4.9, 4.95, 'ceiling', None, 'ceiling')
        mb.prism(grow_poly(pts, 1.0), 5.0, 5.8, 'white_metal', 'roof', 'white_metal')
    elif c == 'testdrive_dropoff':
        pts, _ = edges_of(z['poly'])
        mb.prism(pts, 5.2, 5.7, 'white_metal', 'white_metal', 'white_metal')
        P = SP(pts); r = P.minimum_rotated_rectangle
        for k, p in enumerate(list(r.exterior.coords)[:-1]):
            q = lerp(p, (P.centroid.x, P.centroid.y), 0.15); mb.box('bronze', (q[0], q[1], 0), (0.4, 0.4, 5.2))
    elif c == 'pdi_shed':
        pts, eds = edges_of(z['poly'])
        mb.prism(pts, 0, 8.0, 'shed', 'roof')
    elif c == 'energy_hub':
        pts, eds = edges_of(z['poly'])
        P = SP(pts)
        can = P.buffer(-6, join_style=2)
        mb.prism(list(can.exterior.coords), 6.0, 6.9, 'white_metal', 'roof', 'white_metal')
        mb.face('led', [(x, y, 5.99) for x, y in list(can.buffer(-1.0).exterior.coords)[:-1][::-1]])
        r = list(can.minimum_rotated_rectangle.exterior.coords)
        L1 = math.dist(r[0], r[1]); L2 = math.dist(r[1], r[2])
        ax = (r[1][0] - r[0][0], r[1][1] - r[0][1]) if L1 > L2 else (r[2][0] - r[1][0], r[2][1] - r[1][1])
        ang = math.atan2(ax[1], ax[0]); Lmax = max(L1, L2)
        cc_ = can.centroid
        for k in range(6):
            t = -Lmax / 2 + Lmax * (k + 0.5) / 6
            for side in (-6, 6):
                p = (cc_.x + math.cos(ang) * t - math.sin(ang) * side, cc_.y + math.sin(ang) * t + math.cos(ang) * side)
                mb.box('white_metal', (p[0], p[1], 0), (5.0, 1.2, 1.4), ang)
                mb.box('pole', (p[0], p[1], 1.4), (0.5, 0.5, 4.6), ang)
        store = (cc_.x + math.cos(ang) * (Lmax / 2 + 2), cc_.y + math.sin(ang) * (Lmax / 2 + 2))
        mb.box('stone', (store[0], store[1], 0), (14, 26, 5.5), ang + math.pi / 2)

# ----------------------------------------------------------------------- outdoor launch plaza (shade sails + reveal stage)
OPz = [z for z in Z if z['cls'] == 'outdoor_plaza']
OPm = max(OPz, key=lambda z: z['area'])
P = SP(OPm['poly'])
c = P.centroid
r = list(P.minimum_rotated_rectangle.exterior.coords)
ax = (r[1][0] - r[0][0], r[1][1] - r[0][1]); L1 = math.hypot(*ax)
ax2 = (r[2][0] - r[1][0], r[2][1] - r[1][1]); L2 = math.hypot(*ax2)
if L2 > L1: ax, ax2, L1, L2 = ax2, ax, L2, L1
u = (ax[0] / L1, ax[1] / L1); v = (ax2[0] / L2, ax2[1] / L2)
ang = math.atan2(u[1], u[0])
mb.box('graphite', (c.x, c.y, 0), (14.0, 9.0, 0.7), ang)
mb.box('bronze', (c.x, c.y, 0.7), (14.4, 9.4, 0.04), ang)
STAGE = (c.x, c.y, 0.74, ang)
for k in (-1, 1):
    for side in (-1, 1):
        q = (c.x + u[0] * k * L1 * 0.28 + v[0] * side * L2 * 0.3, c.y + u[1] * k * L1 * 0.28 + v[1] * side * L2 * 0.3)
        # hypar sail on four masts
        corners = []
        for j, (du, dv, h) in enumerate(((-7, -6, 7.5), (7, -6, 4.5), (7, 6, 7.5), (-7, 6, 4.5))):
            p = (q[0] + u[0] * du + v[0] * dv, q[1] + u[1] * du + v[1] * dv)
            corners.append((p[0], p[1], h))
            mb.box('white_metal', (p[0], p[1], 0), (0.25, 0.25, h + 0.3))
        N = 10
        for i in range(N):
            for j in range(N):
                def bil(s_, t_):
                    a_, b2, c2, d2 = corners
                    x = (1 - s_) * (1 - t_) * a_[0] + s_ * (1 - t_) * b2[0] + s_ * t_ * c2[0] + (1 - s_) * t_ * d2[0]
                    y = (1 - s_) * (1 - t_) * a_[1] + s_ * (1 - t_) * b2[1] + s_ * t_ * c2[1] + (1 - s_) * t_ * d2[1]
                    z_ = (1 - s_) * (1 - t_) * a_[2] + s_ * (1 - t_) * b2[2] + s_ * t_ * c2[2] + (1 - s_) * t_ * d2[2]
                    return (x, y, z_)
                mb.quad('fabric', bil(i / N, j / N), bil((i + 1) / N, j / N), bil((i + 1) / N, (j + 1) / N), bil(i / N, (j + 1) / N))

# ----------------------------------------------------------------------- street lights (frontage service road + internal drive)
CNW, RNW = M['C_NW'], M['R_NW']
a = 1.76
while a < 3.76:
    for rr, fc in ((RNW + 15.8, 1), (RNW + 60.2, -1)):
        x, y = CNW[0] + rr * math.cos(a), CNW[1] + rr * math.sin(a)
        mb.box('pole', (x, y, 0), (0.22, 0.22, 11.0))
        for side in (-1, 1):
            hx, hy = x + math.cos(a) * side * 2.2, y + math.sin(a) * side * 2.2
            mb.box('pole', ((x + hx) / 2, (y + hy) / 2, 10.8), (2.2, 0.14, 0.14), a)
            mb.box('white_metal', (hx, hy, 10.6), (0.9, 0.35, 0.2), a)
    a += 34 / RNW

# ---------------------------------------------------------------- indicative context massing (anonymous, low detail)
ctx = MB()
_rs = random.Random(5)
a_ = 1.95
while a_ < 3.62:
    r_ = RNW + 120
    while r_ < RNW + 900:
        # one urban block 70 m x 55 m with villa plots, separated by streets
        da = 55.0 / r_
        for i_ in range(3):
            for j_ in range(2):
                if _rs.random() < 0.38: continue
                rr = r_ + 8 + i_ * 21; aa = a_ + (6 + j_ * 22) / r_
                cx_, cy_ = CNW[0] + rr * math.cos(aa), CNW[1] + rr * math.sin(aa)
                h_ = _rs.choice((6.5, 7.5, 8.5, 10.5, 11.0, 13.0))
                ctx.box('context', (cx_, cy_, 0), (_rs.uniform(13, 17), _rs.uniform(14, 19), h_), aa + _rs.uniform(-.03, .03))
        r_ += 80
    a_ += 62.0 / (RNW + 400)
ctx.build('context')
objs = mb.build('district')

# ======================================================================= off-road terrain
from shapely.geometry import Point
inner = SP(next(z for z in Z if z['cls'] == 'offroad_inner')['poly'])
obs = {z['id']: SP(z['poly']) for z in Z if z['cls'] == 'offroad_obstacle'}
minx, miny, maxx, maxy = inner.bounds
step = 1.5
nx, ny = int((maxx - minx) / step) + 1, int((maxy - miny) / step) + 1


def hfun(x, y):
    p = Point(x, y)
    if not inner.contains(p): return 0.0
    h = 0.0
    for k, poly_ in obs.items():
        if not poly_.buffer(4).contains(p): continue
        d = poly_.exterior.distance(p) * (1 if poly_.contains(p) else -1)
        if k in (197, 198):                                         # hill-climb mounds
            h = max(h, 10.0 * (0.5 - 0.5 * math.cos(math.pi * min(1, max(0, (d + 4) / 24)))))
        elif k == 201:                                              # sand dune field
            if d > -4: h = max(h, (2.2 + 1.8 * math.sin(x * 0.19) * math.cos(y * 0.15)) * min(1, (d + 4) / 8))
        elif k == 193:                                              # side-slope / camber
            if d > -3: h = max(h, min(3.2, (d + 3) * 0.5))
        elif k == 202:                                              # water crossing
            if d > 0: h = min(h, -min(0.9, d * 0.25))
        elif k == 199:                                              # rock crawl base
            if d > -3: h = max(h, 1.2 * min(1, (d + 3) / 6))
    return h


bm = bmesh.new()
grid = {}
for j in range(ny):
    for i in range(nx):
        x, y = minx + i * step, miny + j * step
        grid[(i, j)] = bm.verts.new((x, y, hfun(x, y) + 0.02))
for j in range(ny - 1):
    for i in range(nx - 1):
        q = [grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]]
        if all(inner.buffer(1).contains(Point(v.co.x, v.co.y)) for v in q):
            bm.faces.new(q)
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
me = bpy.data.meshes.new('offroad_terrain'); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
me.materials.append(MAT['ground'])
terr = bpy.data.objects.new('offroad_terrain', me); bpy.context.collection.objects.link(terr)
# water surface + boulders + axle-twister ramps
wp = obs[202]
mbx = MB()
mbx.face('water', [(x, y, -0.25) for x, y in list(wp.buffer(-0.5).exterior.coords)[:-1]])
rp_ = obs[199]
for _ in range(70):
    bx0, by0, bx1, by1 = rp_.bounds
    x, y = random.uniform(bx0, bx1), random.uniform(by0, by1)
    if rp_.buffer(-2).contains(Point(x, y)):
        s_ = random.uniform(0.6, 1.8)
        mbx.box('rock', (x, y, hfun(x, y) - 0.2), (s_ * 1.4, s_, s_ * 0.8), random.uniform(0, 3))
ap = obs[200]
r = list(ap.minimum_rotated_rectangle.exterior.coords)
e1 = (r[1][0] - r[0][0], r[1][1] - r[0][1]); e2 = (r[2][0] - r[1][0], r[2][1] - r[1][1])
if math.hypot(*e1) < math.hypot(*e2): e1, e2 = e2, e1
L = math.hypot(*e1); uu = (e1[0] / L, e1[1] / L)
cA = ap.centroid
for k in range(9):
    t = -L / 2 + 6 + k * (L - 12) / 8
    side = 2.2 if k % 2 else -2.2
    p = (cA.x + uu[0] * t - uu[1] * side, cA.y + uu[1] * t + uu[0] * side)
    mbx.box('timber', (p[0], p[1], 0), (4.0, 3.0, 0.45 + 0.25 * (k % 3)), math.atan2(uu[1], uu[0]))
mbx.build('offroad_features')

# ======================================================================= ground plane
bpy.ops.mesh.primitive_plane_add(size=1)
gp = bpy.context.active_object; gp.name = 'ground'; gp.scale = (60000, 60000, 1)
gp.data.materials.append(MAT['ground'])
hole_cut = None  # terrain sits 2 cm above the plane

# ======================================================================= assets: car, palm, figures
ASSETS = bpy.data.collections.new('ASSETS'); scene.collection.children.link(ASSETS)
ASSETS.hide_render = False


def car_mesh(name, L=4.85, W=1.90, Hh=1.45, kind='sedan'):
    """Lofted parametric car body with greenhouse, wheels and lamps (dimensions in metres)."""
    bm = bmesh.new()
    if kind == 'suv':
        prof = [(0.00, 0.30, 0.72, 0.80), (0.05, 0.25, 0.92, 0.96), (0.16, 0.22, 1.00, 1.04), (0.24, 0.22, 1.00, 1.10), (0.30, 0.22, 1.00, 1.66),
                (0.55, 0.22, 1.00, 1.74), (0.82, 0.22, 1.00, 1.72), (0.92, 0.24, 0.98, 1.55), (0.97, 0.28, 0.95, 1.05), (1.00, 0.36, 0.80, 0.90)]
    elif kind == 'coupe':
        prof = [(0.00, 0.22, 0.55, 0.60), (0.05, 0.17, 0.70, 0.72), (0.18, 0.15, 0.80, 0.80), (0.33, 0.15, 0.82, 0.86), (0.42, 0.15, 0.84, 1.20),
                (0.55, 0.15, 0.84, 1.26), (0.70, 0.15, 0.84, 1.14), (0.86, 0.17, 0.82, 0.92), (0.96, 0.22, 0.78, 0.84), (1.00, 0.30, 0.66, 0.72)]
    else:
        prof = [(0.00, 0.26, 0.62, 0.66), (0.05, 0.20, 0.78, 0.80), (0.18, 0.18, 0.86, 0.88), (0.30, 0.18, 0.90, 0.95), (0.38, 0.18, 0.92, 1.36),
                (0.55, 0.18, 0.92, 1.44), (0.72, 0.18, 0.92, 1.40), (0.82, 0.18, 0.92, 1.06), (0.95, 0.22, 0.88, 0.96), (1.00, 0.30, 0.74, 0.84)]
    sc = Hh / max(p[3] for p in prof)
    NS = 14
    rings = []
    for t, zb, zbelt, ztop in prof:
        x = (t - 0.5) * L
        zb *= sc; zbelt *= sc; ztop *= sc
        greenhouse = ztop > zbelt + 0.15
        hw = W / 2 * (0.86 if t in (0.0, 1.0) else (0.95 if t < 0.1 or t > 0.9 else 1.0))
        roof_hw = hw * (0.74 if greenhouse else 0.92)
        pts = []
        # half-profile from bottom-centre, around the side, to top-centre (then mirrored)
        half = [(0.0, zb), (hw * 0.82, zb), (hw * 0.97, zb + 0.08), (hw, zb + (zbelt - zb) * 0.45), (hw * 0.99, zbelt - 0.05),
                (hw * 0.96, zbelt), (roof_hw + (hw * 0.96 - roof_hw) * 0.45, zbelt + (ztop - zbelt) * 0.55), (roof_hw, ztop - 0.04), (roof_hw * 0.6, ztop), (0.0, ztop)]
        full = [(x, y, z) for y, z in half] + [(x, -y, z) for y, z in half[-2:0:-1]]
        rings.append(([bm.verts.new(p) for p in full], greenhouse))
    nring = len(rings[0][0])
    for k in range(len(rings) - 1):
        r0, g0 = rings[k]; r1, g1 = rings[k + 1]
        for i in range(nring):
            j = (i + 1) % nring
            f = bm.faces.new((r0[i], r1[i], r1[j], r0[j]))
            # window faces: between belt and roof on greenhouse stations
            f.material_index = 1 if (g0 and g1 and i in (5, 6, nring - 7, nring - 6)) else 0
    bm.faces.new(rings[0][0][::-1]); bm.faces.new(rings[-1][0])
    # windscreen / backlight: upper faces on stations where the greenhouse starts or ends
    bm.faces.ensure_lookup_table()
    for k in range(len(rings) - 1):
        if rings[k][1] != rings[k + 1][1]:
            for i in range(5, nring - 5):
                bm.faces[k * nring + i].material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # wheels
    wr = 0.34 if kind != 'suv' else 0.38
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx = sx * L * (0.33 if kind != 'coupe' else 0.32); cy = sy * (W / 2 - 0.12)
            ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=wr, radius2=wr, depth=0.24)
            mrot = Matrix.Rotation(math.pi / 2, 4, 'X')
            bmesh.ops.transform(bm, matrix=Matrix.Translation((cx, cy, wr)) @ mrot, verts=ret['verts'])
            for f in {f for v in ret['verts'] for f in v.link_faces}: f.material_index = 2
            ret = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=wr * 0.62, radius2=wr * 0.62, depth=0.02)
            bmesh.ops.transform(bm, matrix=Matrix.Translation((cx, cy + sy * 0.125, wr)) @ mrot, verts=ret['verts'])
            for f in {f for v in ret['verts'] for f in v.link_faces}: f.material_index = 3
    # lamps
    for sy in (-1, 1):
        for sx, mi in ((0.5, 4), (-0.5, 5)):
            ret = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.transform(bm, matrix=Matrix.Translation((sx * L * 0.985, sy * W * 0.33, Hh * (0.58 if kind != 'suv' else 0.62))) @ Matrix.Diagonal((0.06, 0.38, 0.07, 1)), verts=ret['verts'])
            for f in {f for v in ret['verts'] for f in v.link_faces}: f.material_index = mi
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in ('carpaint', 'carglass', 'tyre', 'rim', 'lamp_f', 'lamp_r'): me.materials.append(MAT[m_])
    for p in me.polygons: p.use_smooth = p.material_index in (0, 1)
    ob = bpy.data.objects.new(name, me); ASSETS.objects.link(ob)
    mod = ob.modifiers.new('ws', 'WEIGHTED_NORMAL') if False else None
    return ob


CARS = [car_mesh('car_sedan', 4.85, 1.88, 1.45, 'sedan'), car_mesh('car_suv', 4.90, 1.98, 1.78, 'suv'),
        car_mesh('car_coupe', 4.50, 1.95, 1.26, 'coupe'), car_mesh('car_sedan_s', 4.55, 1.80, 1.44, 'sedan')]


def palm_mesh(name, H=8.0, fronds=18):
    bm = bmesh.new()
    lean = random.uniform(-0.3, 0.3)
    segs = 12
    prev = None
    for k in range(segs + 1):
        t = k / segs
        r = 0.24 - 0.07 * t + (0.05 if k == 0 else 0)
        cx = lean * t * t; z = H * t
        ring = [bm.verts.new((cx + r * math.cos(a), r * math.sin(a), z)) for a in [i * 2 * math.pi / 10 for i in range(10)]]
        if prev:
            for i in range(10):
                bm.faces.new((prev[i], prev[(i + 1) % 10], ring[(i + 1) % 10], ring[i]))
        prev = ring
    top = Vector((lean, 0, H))
    for i in range(10): pass
    nbark = len(bm.faces)
    # crown boss
    ret = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.30)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(top + Vector((0, 0, 0.15))) @ Matrix.Diagonal((1, 1, 1.5, 1)), verts=ret['verts'])
    nboss = len(bm.faces)
    for fI in range(fronds):
        az = fI * 2.399 + random.uniform(-.15, .15)
        tier = fI / fronds
        elev = math.radians(58 - 105 * tier + random.uniform(-8, 8))
        Lf = random.uniform(3.2, 4.0) * (1.0 - 0.12 * tier)
        d = Vector((math.cos(az) * math.cos(elev), math.sin(az) * math.cos(elev), math.sin(elev)))
        side = Vector((-math.sin(az), math.cos(az), 0))
        n = 30
        spine = [top + d * Lf * (k / n) + Vector((0, 0, -1.1 * (k / n) ** 2 * (1 + 0.7 * tier))) for k in range(n + 1)]
        # rachis
        for k in range(n):
            p, q = spine[k], spine[k + 1]
            w_ = 0.035 * (1 - k / n) + 0.008
            v1 = bm.verts.new(p - side * w_); v2 = bm.verts.new(p + side * w_); v3 = bm.verts.new(q + side * w_ * .8); v4 = bm.verts.new(q - side * w_ * .8)
            bm.faces.new((v1, v2, v3, v4))
        for k in range(3, n):
            t = k / n
            p = spine[k]; q = spine[min(n, k + 1)]
            fwd = (q - p).normalized()
            ll = (0.75 * math.sin(math.pi * min(1, t * 1.05)) + 0.18) * random.uniform(.9, 1.1)
            for sgn in (-1, 1):
                up = Vector((0, 0, 1)) * 0.15
                dirv = (side * sgn + up + fwd * 0.75).normalized()
                tip = p + dirv * ll + Vector((0, 0, -0.38 * ll))
                b0 = p - fwd * 0.03; b1 = p + fwd * 0.03
                v1 = bm.verts.new(b0); v2 = bm.verts.new(b1); v3 = bm.verts.new(tip)
                bm.faces.new((v1, v2, v3) if sgn > 0 else (v2, v1, v3))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(MAT['bark']); me.materials.append(MAT['leaf'])
    for i, p in enumerate(me.polygons):
        p.material_index = 0 if i < nboss else 1
        p.use_smooth = i < nboss
    ob = bpy.data.objects.new(name, me); ASSETS.objects.link(ob)
    return ob


PALMS = [palm_mesh(f'palm_{k}', H=random.uniform(7.0, 9.5), fronds=34) for k in range(4)]


def lathe(bm, prof, segs=12, cx=0.0, cy=0.0, mi=0, sy=1.0):
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((cx + r * math.cos(a), cy + r * sy * math.sin(a), z)) for a in [i * 2 * math.pi / segs for i in range(segs)]])
    fs = []
    for k in range(len(rings) - 1):
        for i in range(segs):
            f = bm.faces.new((rings[k][i], rings[k][(i + 1) % segs], rings[k + 1][(i + 1) % segs], rings[k + 1][i])); f.material_index = mi; fs.append(f)
    return fs


def figure(name, kind):
    bm = bmesh.new()
    if kind == 0:     # thobe + shemagh
        lathe(bm, [(0.16, 0.0), (0.22, 0.06), (0.21, 0.6), (0.18, 1.0), (0.21, 1.38), (0.23, 1.44), (0.10, 1.52), (0.0, 1.53)], mi=0, sy=0.62)
        lathe(bm, [(0.0, 1.50), (0.075, 1.53), (0.10, 1.62), (0.09, 1.70), (0.0, 1.76)], mi=1)
        lathe(bm, [(0.16, 1.38), (0.14, 1.55), (0.12, 1.70), (0.11, 1.76), (0.0, 1.79)], mi=2, sy=0.9)
        mats = ('thobe', 'skin', 'shemagh')
    elif kind == 1:   # abaya
        lathe(bm, [(0.17, 0.0), (0.23, 0.05), (0.21, 0.6), (0.17, 1.0), (0.19, 1.30), (0.20, 1.38), (0.09, 1.46), (0.10, 1.56), (0.09, 1.66), (0.0, 1.70)], mi=0, sy=0.62)
        mats = ('abaya', 'abaya', 'abaya')
    else:             # casual
        lathe(bm, [(0.07, 0.0), (0.08, 0.45), (0.15, 0.85), (0.16, 0.95)], mi=1, sy=0.75)
        lathe(bm, [(0.16, 0.95), (0.18, 1.2), (0.21, 1.40), (0.10, 1.48), (0.0, 1.49)], mi=0, sy=0.62)
        lathe(bm, [(0.0, 1.47), (0.07, 1.50), (0.095, 1.60), (0.085, 1.70), (0.0, 1.74)], mi=2)
        mats = ('casual_top', 'casual_leg', 'skin')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in mats: me.materials.append(MAT[m_])
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ASSETS.objects.link(ob)
    return ob


FIGS = [figure('fig_thobe', 0), figure('fig_abaya', 1), figure('fig_casual', 2)]


def shrub_mesh():
    bm = bmesh.new()
    for k in range(5):
        ret = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=random.uniform(0.5, 0.9))
        bmesh.ops.transform(bm, matrix=Matrix.Translation((random.uniform(-.7, .7), random.uniform(-.7, .7), 0.35)) @ Matrix.Diagonal((1, 1, .7, 1)), verts=ret['verts'])
    me = bpy.data.meshes.new('shrub'); bm.to_mesh(me); bm.free(); me.materials.append(MAT['shrub'])
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new('shrub', me); ASSETS.objects.link(ob); return ob


SHRUB = shrub_mesh()
for ob in ASSETS.objects: ob.location = (0, 0, -1000)


# ======================================================================= instancing (geometry nodes on point clouds)
def point_cloud(name, pts, asset_objs, rot_key=2, scale_key=None):
    """pts: list of (x, y, z, rot, scale, variant). One object per variant, GN Instance-on-Points."""
    for vi, src in enumerate(asset_objs):
        sel = [p for p in pts if p[5] == vi]
        if not sel: continue
        me = bpy.data.meshes.new(f'{name}_{vi}_pts')
        me.from_pydata([(p[0], p[1], p[2]) for p in sel], [], [])
        rot = me.attributes.new('rot', 'FLOAT', 'POINT'); scl = me.attributes.new('scl', 'FLOAT', 'POINT')
        for i, p in enumerate(sel): rot.data[i].value = p[3]; scl.data[i].value = p[4]
        ob = bpy.data.objects.new(f'{name}_{vi}', me); bpy.context.collection.objects.link(ob)
        mod = ob.modifiers.new('inst', 'NODES')
        ng = bpy.data.node_groups.new(f'gn_{name}_{vi}', 'GeometryNodeTree')
        ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
        ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        gi = ng.nodes.new('NodeGroupInput'); go = ng.nodes.new('NodeGroupOutput')
        iop = ng.nodes.new('GeometryNodeInstanceOnPoints')
        oinfo = ng.nodes.new('GeometryNodeObjectInfo'); oinfo.inputs['Object'].default_value = src
        try: oinfo.transform_space = 'ORIGINAL'
        except Exception: pass
        ar = ng.nodes.new('GeometryNodeInputNamedAttribute'); ar.data_type = 'FLOAT'; ar.inputs['Name'].default_value = 'rot'
        asx = ng.nodes.new('GeometryNodeInputNamedAttribute'); asx.data_type = 'FLOAT'; asx.inputs['Name'].default_value = 'scl'
        cmb = ng.nodes.new('ShaderNodeCombineXYZ')
        ng.links.new(ar.outputs['Attribute'], cmb.inputs['Z'])
        ng.links.new(gi.outputs[0], iop.inputs['Points'])
        ng.links.new(oinfo.outputs['Geometry'], iop.inputs['Instance'])
        ng.links.new(cmb.outputs['Vector'], iop.inputs['Rotation'])
        ng.links.new(asx.outputs['Attribute'], iop.inputs['Scale'])
        ng.links.new(iop.outputs['Instances'], go.inputs[0])
        mod.node_group = ng


carpts = [(x, y, 0.0, h, 1.0, int(r * 997) % 4) for x, y, h, r in M['cars']]
carpts += [(x, y, 0.35, h, 1.0, int(r * 991) % 4) for x, y, h, r in M['display_cars']]
# off-road demonstration vehicles (SUVs) on terrain and loop
for _ in range(16):
    while True:
        x, y = random.uniform(minx, maxx), random.uniform(miny, maxy)
        if inner.buffer(-10).contains(Point(x, y)): break
    carpts.append((x, y, hfun(x, y), random.uniform(0, 6.28), 1.0, 1))
loop = SP(next(z for z in Z if z['cls'] == 'offroad_outer')['poly']).difference(inner)
lring = SP(next(z for z in Z if z['cls'] == 'offroad_outer')['poly']).buffer(-(math.sqrt(loop.area / 1.0) * 0 + 6)).exterior
for k in range(5):
    s = random.uniform(0, lring.length); p = lring.interpolate(s); p2 = lring.interpolate((s + 2) % lring.length)
    carpts.append((p.x, p.y, 0.0, math.atan2(p2.y - p.y, p2.x - p.x), 1.0, random.choice((0, 1, 2))))
point_cloud('cars', carpts, CARS)
palmpts = [(x, y, 0.0, rot, s, int(s * 1000) % 4) for x, y, s, rot in M['palms']]
point_cloud('palms', palmpts, PALMS)
pp = [(x, y, 0.0, rot, s, k) for x, y, rot, k, s in M['people']]
point_cloud('people', pp, FIGS)
# planting under palms in landscape belt & plaza beds
shr = [(x + random.uniform(-2, 2), y + random.uniform(-2, 2), 0.0, random.uniform(0, 6), random.uniform(.6, 1.1), 0) for x, y, s, r in M['palms'] for _ in range(1) if random.random() < 0.35]
point_cloud('shrubs', shr, [SHRUB])

# reveal car under cover on the launch stage
cov = bpy.data.objects.new('reveal_car', CARS[2].data.copy()); bpy.context.collection.objects.link(cov)
cov.data.materials.clear(); [cov.data.materials.append(MAT['cover']) for _ in range(6)]
cov.location = (STAGE[0], STAGE[1], STAGE[2]); cov.rotation_euler = (0, 0, STAGE[3]); cov.scale = (1.04, 1.06, 1.05)
sub = cov.modifiers.new('sub', 'SUBSURF'); sub.levels = 2; sub.render_levels = 2

# ======================================================================= world + render defaults
w = bpy.data.worlds.new('Sky'); scene.world = w; w.use_nodes = True
nt = w.node_tree; bg = nt.nodes['Background']
sky = nt.nodes.new('ShaderNodeTexSky'); sky.sky_type = 'MULTIPLE_SCATTERING'
nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
sky.name = 'sky'
sun = bpy.data.lights.new('Sun', 'SUN'); sun.angle = math.radians(0.6)
so = bpy.data.objects.new('Sun', sun); bpy.context.collection.objects.link(so)
cam = bpy.data.cameras.new('Cam'); co = bpy.data.objects.new('Cam', cam); bpy.context.collection.objects.link(co); scene.camera = co
cam.clip_end = 20000; cam.clip_start = 0.5

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.use_denoising = True
scene.view_settings.view_transform = 'AgX'
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('saved', OUT, len(bpy.data.objects), 'objects')
