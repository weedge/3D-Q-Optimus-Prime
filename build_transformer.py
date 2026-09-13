import bpy
import math
from mathutils import Vector

# Clear the default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    pass

def mat(name, color, metallic=0.0, roughness=0.4, emission=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emission:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1)
        bsdf.inputs['Emission Strength'].default_value = 5.0
    return m

steel = mat('Titanium Steel', (0.18, 0.23, 0.28), 0.85, 0.24)
steel2 = mat('Edge Steel', (0.38, 0.44, 0.50), 0.8, 0.2)
dark = mat('Joint Graphite', (0.025, 0.035, 0.05), 0.7, 0.25)
red = mat('Crimson Armor', (0.55, 0.025, 0.035), 0.65, 0.24)
blue = mat('Optic Blue', (0.02, 0.18, 0.8), 0.4, 0.18, (0.01, 0.08, 1.0))
gold = mat('Signal Gold', (0.95, 0.42, 0.04), 0.7, 0.22)
white = mat('Bright White', (0.75, 0.82, 0.9), 0.35, 0.2)
ground_mat = mat('Floor', (0.018, 0.025, 0.04), 0.25, 0.3)

def bevel(obj, amount=0.08, segments=3):
    mod = obj.modifiers.new('Precision bevel', 'BEVEL')
    mod.width = amount
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    return obj

def box(name, loc, scale, material, bevel_amt=0.08, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_amt:
        bevel(o, bevel_amt)
    o.data.materials.append(material)
    return o

def cyl(name, loc, radius, depth, material, rot=(0,0,0), verts=32, bevel_amt=0.05):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    if bevel_amt:
        bevel(o, bevel_amt, 2)
    o.data.materials.append(material)
    return o

def sphere(name, loc, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o

def cone(name, loc, r1, r2, depth, material, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    bevel(o, 0.04, 2)
    o.data.materials.append(material)
    return o

def torus(name, loc, major, minor, material, rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=40, minor_segments=12, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    return o

# Lower torso and pelvis
box('Pelvis Core', (0, 0, 2.95), (2.35, 1.25, 0.9), dark, 0.16)
box('Pelvis Armor', (0, -0.06, 3.18), (2.7, 1.35, 0.55), steel, 0.14)
box('Pelvis Red Plate', (0, -0.76, 3.15), (1.45, 0.12, 0.38), red, 0.04)
for x in (-0.78, 0.78):
    cyl('Hip Joint', (x, 0, 2.55), 0.38, 0.55, dark, rot=(math.pi/2,0,0))
    sphere('Hip Cap', (x, -0.12, 2.55), (0.46,0.4,0.46), steel2)

# Main torso, shoulder line and chest
box('Torso Core', (0, 0, 4.55), (3.1, 1.45, 2.25), dark, 0.18)
box('Torso Armor', (0, -0.08, 4.75), (3.35, 1.55, 1.95), steel, 0.2)
box('Chest Red Frame', (0, -0.88, 5.25), (3.0, 0.18, 1.05), red, 0.07)
box('Chest Window Left', (-0.78, -0.99, 5.26), (1.25, 0.10, 0.52), blue, 0.05, rot=(0, math.radians(-8), 0))
box('Chest Window Right', (0.78, -0.99, 5.26), (1.25, 0.10, 0.52), blue, 0.05, rot=(0, math.radians(8), 0))
box('Chest Center Crest', (0, -1.01, 4.7), (0.35, 0.12, 0.75), gold, 0.04)
box('Ab Plate', (0, -0.84, 3.95), (1.4, 0.2, 0.48), steel2, 0.06)
for z in (3.72, 3.48):
    box('Ab Rib', (0, -0.76, z), (1.7, 0.12, 0.12), dark, 0.025)

# Neck and head
cyl('Neck', (0, 0, 5.95), 0.42, 0.55, dark)
box('Head Helmet', (0, -0.02, 6.85), (1.45, 1.25, 1.15), steel2, 0.17)
box('Face Plate', (0, -0.68, 6.68), (1.18, 0.20, 0.62), white, 0.07)
box('Visor', (0, -0.83, 6.98), (1.05, 0.08, 0.23), blue, 0.03)
box('Mouth Guard', (0, -0.84, 6.52), (0.65, 0.08, 0.15), dark, 0.02)
box('Helmet Crown', (0, 0, 7.48), (1.0, 0.95, 0.22), red, 0.05)
for x in (-0.68, 0.68):
    cone('Ear Antenna', (x, 0, 7.32), 0.15, 0.02, 0.72, gold, rot=(0, math.radians(10 if x < 0 else -10), 0))
box('Forehead Crest', (0, -0.67, 7.32), (0.22, 0.10, 0.50), gold, 0.03)

# Shoulders and arms
for side, x in (('L', -2.05), ('R', 2.05)):
    box(f'{side} Shoulder Joint', (x*0.83, 0, 5.45), (0.60, 1.15, 0.65), dark, 0.16)
    box(f'{side} Shoulder Armor', (x, -0.02, 5.45), (0.95, 1.55, 1.05), red, 0.18, rot=(0, 0, math.radians(-8 if x < 0 else 8)))
    box(f'{side} Shoulder Trim', (x, -0.82, 5.45), (0.58, 0.10, 0.68), gold, 0.03)
    cyl(f'{side} Elbow Joint', (x, 0, 4.15), 0.32, 0.52, dark, rot=(math.pi/2,0,0))
    box(f'{side} Upper Arm', (x, 0, 4.75), (0.72, 0.95, 1.35), steel2, 0.12, rot=(0, 0, math.radians(4 if x < 0 else -4)))
    box(f'{side} Forearm', (x, -0.02, 3.55), (0.85, 1.1, 1.25), steel, 0.14, rot=(0, 0, math.radians(-6 if x < 0 else 6)))
    box(f'{side} Forearm Red Plate', (x, -0.62, 3.65), (0.5, 0.12, 0.65), red, 0.04)
    box(f'{side} Fist', (x, -0.02, 2.65), (0.95, 1.0, 0.82), dark, 0.16)
    for fx in (-0.25, 0, 0.25):
        box(f'{side} Knuckle', (x+fx, -0.55, 2.82), (0.18, 0.18, 0.24), steel2, 0.03)

# Legs with layered armor
for side, x in (('L', -0.85), ('R', 0.85)):
    cyl(f'{side} Knee Joint', (x, 0, 1.62), 0.36, 0.55, dark, rot=(math.pi/2,0,0))
    box(f'{side} Thigh', (x, 0, 2.12), (0.92, 1.1, 1.55), steel2, 0.14, rot=(0, 0, math.radians(2 if x < 0 else -2)))
    box(f'{side} Thigh Red Guard', (x, -0.60, 2.25), (0.58, 0.13, 0.82), red, 0.04)
    box(f'{side} Knee Guard', (x, -0.70, 1.62), (0.72, 0.22, 0.52), gold, 0.06)
    box(f'{side} Shin', (x, 0, 0.85), (1.08, 1.25, 1.55), steel, 0.16)
    box(f'{side} Shin Blue Light', (x, -0.68, 0.88), (0.34, 0.10, 0.62), blue, 0.03)
    box(f'{side} Ankle', (x, 0, -0.03), (0.72, 0.92, 0.35), dark, 0.07)
    box(f'{side} Foot', (x, -0.32, -0.36), (1.38, 2.0, 0.62), steel2, 0.13)
    box(f'{side} Toe Armor', (x, -1.16, -0.26), (1.2, 0.5, 0.35), red, 0.08)

# Small mechanical details
for x in (-1.1, -0.55, 0.55, 1.1):
    cyl('Torso Vent', (x, -0.87, 4.15), 0.07, 0.08, gold, rot=(math.pi/2,0,0), verts=16, bevel_amt=0.01)
for x in (-1.2, 1.2):
    torus('Shoulder Ring', (x, -0.84, 5.55), 0.22, 0.055, gold, rot=(math.pi/2,0,0))

# Ground and backdrop
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.7))
floor = bpy.context.object
floor.name = 'Display Floor'
floor.data.materials.append(ground_mat)
bevel(floor, 0.02, 1)

# Add a subtle circular platform
cyl('Display Plinth', (0, 0, -0.58), 4.0, 0.25, dark, bevel_amt=0.06)
cyl('Plinth Light Ring', (0, 0, -0.43), 3.72, 0.06, blue, bevel_amt=0.01)

# Camera
bpy.ops.object.camera_add(location=(10.8, -17.5, 8.2))
camera = bpy.context.object
camera.name = 'Hero Camera'
bpy.context.scene.camera = camera
def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()
point_at(camera, (0, 0, 3.4))
camera.data.lens = 56

# Lights
bpy.ops.object.light_add(type='AREA', location=(4.5, -7, 12))
key = bpy.context.object
key.name = 'Key Light'
key.data.energy = 1300
key.data.shape = 'DISK'
key.data.size = 5.0
point_at(key, (0,0,3.5))
bpy.ops.object.light_add(type='AREA', location=(-6, -3, 7))
fill = bpy.context.object
fill.name = 'Blue Fill'
fill.data.energy = 900
fill.data.color = (0.12, 0.25, 1.0)
fill.data.size = 4.0
point_at(fill, (0,0,3.5))
bpy.ops.object.light_add(type='AREA', location=(2, 5, 8))
rim = bpy.context.object
rim.name = 'Rim Light'
rim.data.energy = 1400
rim.data.color = (1.0, 0.12, 0.04)
rim.data.size = 3.0
point_at(rim, (0,0,4.5))

# World and render settings
world = bpy.context.scene.world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.006, 0.015, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.25
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 700
scene.render.resolution_y = 700
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = '/Users/wuyong/Documents/ChatGPT/3D/transformer_robot.png'
scene.render.film_transparent = False
scene.view_settings.look = 'AgX - Medium High Contrast'

# Slight bevel-friendly ambient occlusion via world lighting and contact shadows
scene.render.image_settings.color_mode = 'RGBA'
bpy.ops.wm.save_as_mainfile(filepath='/Users/wuyong/Documents/ChatGPT/3D/transformer_robot.blend')
bpy.ops.render.render(write_still=True)
