"""Render one named view of the JMD model.

run: bvenv/bin/python render_view.py jmd.blend VIEW out.png WIDTH HEIGHT SAMPLES [local_tile.jpg x0 y0 x1 y1]
"""
import bpy, math, sys, json
from mathutils import Vector

a = sys.argv[1:]
BLEND, VIEW, OUT, W, H, SPP = a[0], a[1], a[2], int(a[3]), int(a[4]), int(a[5])
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
exec(open(__file__.replace('render_view.py', 'views.py')).read())   # defines VIEWS
v = VIEWS[VIEW]

cam = sc.camera
cam.location = Vector(v['cam'])
d = Vector(v['look']) - Vector(v['cam'])
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
if v.get('roll'): cam.rotation_euler.rotate_axis('Z', math.radians(v['roll']))
if v.get('ortho'):
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = v['ortho']
else:
    cam.data.lens = v.get('lens', 35)
cam.data.shift_x = v.get('shift_x', 0); cam.data.shift_y = v.get('shift_y', 0)
cam.data.sensor_width = 36

# sun: azimuth from north clockwise, elevation above horizon
az, el = math.radians(v['sun'][0]), math.radians(v['sun'][1])
to_sun = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
sun = bpy.data.objects['Sun']
sun.rotation_euler = to_sun.to_track_quat('Z', 'Y').to_euler()
sun.data.energy = v.get('sun_strength', 3.4)
sun.data.color = v.get('sun_color', (1.0, 0.95, 0.88))
sky = sc.world.node_tree.nodes['sky']
sky.sun_elevation = el
sky.sun_rotation = (math.pi / 2 - az)   # Blender sky: rotation measured from +X, counter-clockwise
sky.sun_disc = False
sky.altitude = 50
sky.air_density = v.get('air', 1.0)
bg = sc.world.node_tree.nodes['Background']
bg.inputs['Strength'].default_value = v.get('sky_strength', 0.22)

# interior lights / headlamps for dusk views
for m in bpy.data.materials:
    if m.name == 'Interior ceiling light':
        m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = v.get('interior', 1.6)
    if m.name == 'Linear light':
        m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = v.get('led', 0.0)

# optional hi-res ground tile
if len(a) > 6:
    tile, x0, y0, x1, y1 = a[6], *map(float, a[7:11])
    g = bpy.data.materials['Ground'].node_tree
    g.nodes['tex_local'].image = bpy.data.images.load(tile)
    g.nodes['local_mx'].inputs['From Min'].default_value = x0; g.nodes['local_mx'].inputs['From Max'].default_value = x1
    g.nodes['local_my'].inputs['From Min'].default_value = y0; g.nodes['local_my'].inputs['From Max'].default_value = y1

# clear instances close to the lens (toy-like at <10 m)
import bmesh
for prefix, rad in (('people_', v.get('clear_people', 0)), ('cars_', v.get('clear_cars', 0))):
    if not rad: continue
    for ob in bpy.data.objects:
        if ob.name.startswith(prefix) and ob.type == 'MESH':
            bm = bmesh.new(); bm.from_mesh(ob.data)
            dv = [vv for vv in bm.verts if ((vv.co.x - cam.location.x) ** 2 + (vv.co.y - cam.location.y) ** 2) ** 0.5 < rad]
            bmesh.ops.delete(bm, geom=dv, context='VERTS'); bm.to_mesh(ob.data); bm.free()
for name in v.get('hide', []):
    for ob in bpy.data.objects:
        if ob.name.startswith(name): ob.hide_render = True

r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
r.image_settings.file_format = 'PNG'; r.image_settings.color_depth = '8'
sc.cycles.samples = SPP
sc.cycles.adaptive_threshold = 0.02
sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 6; sc.cycles.transmission_bounces = 6; sc.cycles.glossy_bounces = 3; sc.cycles.diffuse_bounces = 3
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.cycles.blur_glossy = 1.0
sc.render.threads_mode = 'AUTO'
sc.view_settings.view_transform = 'AgX'
for look in (v.get('look', 'AgX - Medium High Contrast'), 'Medium High Contrast', 'AgX - Base Contrast', 'None'):
    try:
        sc.view_settings.look = look; break
    except Exception:
        continue
sc.view_settings.exposure = v.get('exposure', 0.0)
sc.render.film_transparent = False
r.filepath = OUT
bpy.ops.render.render(write_still=True)
print('wrote', OUT)
