import bpy
import math
from mathutils import Vector

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, metallic=0.0, roughness=0.35, emission=None):
    current = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    current.diffuse_color = (*color, 1.0)
    current.use_nodes = True
    shader = current.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1.0)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    if emission:
        shader.inputs['Emission Color'].default_value = (*emission, 1.0)
        shader.inputs['Emission Strength'].default_value = 6.0
    return current

outline = material('Outline Dark', (0.012, 0.008, 0.018), 0.15, 0.3)
blue = material('Hero Blue', (0.015, 0.16, 0.62), 0.65, 0.23)
blue_light = material('Blue Highlight', (0.02, 0.42, 0.95), 0.5, 0.18)
red = material('Hero Red', (0.72, 0.025, 0.035), 0.65, 0.23)
red_dark = material('Red Shadow', (0.24, 0.008, 0.015), 0.55, 0.26)
silver = material('Face Silver', (0.62, 0.67, 0.74), 0.55, 0.25)
white = material('Trim White', (0.86, 0.9, 0.96), 0.25, 0.2)
cyan = material('Cyan Glow', (0.005, 0.22, 0.95), 0.25, 0.16, (0.0, 0.16, 0.85))
yellow = material('Warm Gold', (0.95, 0.55, 0.05), 0.65, 0.2)
floor_mat = material('Floor', (0.015, 0.02, 0.045), 0.2, 0.3)

def smooth_bevel(obj, amount=0.08, segments=3):
    modifier = obj.modifiers.new('Rounded edges', 'BEVEL')
    modifier.width = amount
    modifier.segments = segments
    modifier.limit_method = 'ANGLE'
    return obj

def cube(name, location, dimensions, shader, bevel=0.08, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        smooth_bevel(obj, bevel)
    obj.data.materials.append(shader)
    return obj

def cylinder(name, location, radius, depth, shader, rotation=(0, 0, 0), bevel=0.04, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    if bevel:
        smooth_bevel(obj, bevel, 2)
    obj.data.materials.append(shader)
    return obj

def uv_sphere(name, location, dimensions, shader):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(shader)
    return obj

def cone(name, location, r1, r2, depth, shader, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r1, radius2=r2, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    smooth_bevel(obj, 0.035, 2)
    obj.data.materials.append(shader)
    return obj

def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

cube('Body Silhouette', (0, 0, 3.95), (3.35, 1.32, 2.3), outline, 0.24)
cube('Torso Blue Shell', (0, -0.04, 4.6), (3.12, 1.42, 1.58), blue, 0.17)
cube('Upper Red Chest', (0, -0.77, 4.95), (3.05, 0.23, 0.82), red, 0.09)
cube('Lower Red Chest', (0, -0.79, 4.22), (2.48, 0.2, 0.52), red_dark, 0.06)
cube('Chest Window L Outline', (-0.72, -0.895, 4.98), (1.16, 0.12, 0.56), outline, 0.07, rotation=(0, math.radians(-5), 0))
cube('Chest Window R Outline', (0.72, -0.895, 4.98), (1.16, 0.12, 0.56), outline, 0.07, rotation=(0, math.radians(5), 0))
cube('Chest Window L', (-0.72, -0.97, 4.98), (0.98, 0.1, 0.38), cyan, 0.04, rotation=(0, math.radians(-5), 0))
cube('Chest Window R', (0.72, -0.97, 4.98), (0.98, 0.1, 0.38), cyan, 0.04, rotation=(0, math.radians(5), 0))
for x in (-1.05, 1.05):
    cube('Chest White Border', (x, -0.95, 4.98), (0.08, 0.07, 0.62), white, 0.02)
cube('Chest Center Badge', (0, -0.96, 4.57), (0.25, 0.08, 0.45), yellow, 0.025)
for z in (3.96, 3.74):
    cube('Abdominal Segment', (0, -0.73, z), (1.38, 0.18, 0.14), silver, 0.025)

cube('Helmet Outer', (0, 0, 7.02), (3.45, 1.62, 2.62), outline, 0.38)
cube('Helmet Blue Front', (0, -0.76, 7.18), (3.08, 0.26, 1.98), blue, 0.23)
cube('Helmet Crown', (0, -0.05, 8.14), (1.72, 1.12, 0.42), blue_light, 0.1)
cube('Helmet Forehead Panel', (0, -0.9, 7.84), (1.18, 0.1, 0.56), cyan, 0.04)
cube('Face Outline', (0, -1.0, 6.62), (2.48, 0.34, 1.34), outline, 0.22)
cube('Face Base', (0, -1.15, 6.62), (2.24, 0.18, 1.12), silver, 0.16)
cube('Face Lower Plate', (0, -1.28, 6.16), (0.92, 0.1, 0.27), white, 0.04)
cube('Eye L Outline', (-0.7, -1.29, 6.96), (0.92, 0.12, 0.5), outline, 0.16, rotation=(0, math.radians(-10), 0))
cube('Eye R Outline', (0.7, -1.29, 6.96), (0.92, 0.12, 0.5), outline, 0.16, rotation=(0, math.radians(10), 0))
cube('Eye L', (-0.7, -1.37, 6.96), (0.72, 0.08, 0.3), cyan, 0.11, rotation=(0, math.radians(-10), 0))
cube('Eye R', (0.7, -1.37, 6.96), (0.72, 0.08, 0.3), cyan, 0.11, rotation=(0, math.radians(10), 0))
cube('Forehead Grille', (0, -1.02, 7.32), (0.56, 0.08, 0.72), white, 0.03)
for grille_z in (7.06, 7.18, 7.30, 7.42, 7.54):
    cube('Forehead Grille Slat', (0, -1.08, grille_z), (0.42, 0.04, 0.045), outline, 0.01)
for x in (-1.58, 1.58):
    cube('Helmet Side Armor', (x, 0, 6.98), (0.52, 1.2, 2.12), blue, 0.14)
    cylinder('Ear Disc', (x, -1.0, 6.82), 0.58, 0.28, outline, rotation=(math.pi/2, 0, 0), bevel=0.07)
    cylinder('Ear Disc Silver', (x, -1.16, 6.82), 0.46, 0.12, silver, rotation=(math.pi/2, 0, 0), bevel=0.04)
    cylinder('Ear Inner', (x, -1.25, 6.82), 0.29, 0.10, red, rotation=(math.pi/2, 0, 0), bevel=0.025)
    cone('Side Antenna', (x, 0.02, 7.92), 0.18, 0.03, 1.85, blue_light, rotation=(0, math.radians(8 if x < 0 else -8), 0))

for side, x in (('L', -1.98), ('R', 1.98)):
    cube(side + ' Shoulder Outline', (x, 0, 5.26), (1.26, 1.5, 1.42), outline, 0.18, rotation=(0, 0, math.radians(8 if x < 0 else -8)))
    cube(side + ' Shoulder Blue', (x, -0.04, 5.36), (1.1, 1.38, 1.25), blue, 0.14, rotation=(0, 0, math.radians(8 if x < 0 else -8)))
    cube(side + ' Shoulder Wing', (x * 1.3, 0.02, 5.9), (0.48, 0.9, 2.5), blue_light, 0.1, rotation=(0, math.radians(8 if x < 0 else -8), math.radians(8 if x < 0 else -8)))
    cube(side + ' Shoulder Red Plate', (x, -0.76, 5.16), (0.68, 0.15, 0.52), red, 0.05)
    cube(side + ' Shoulder Symbol', (x, -0.86, 5.16), (0.32, 0.06, 0.2), white, 0.02)
    cylinder(side + ' Upper Joint', (x * 0.82, 0, 4.45), 0.35, 0.5, outline, rotation=(math.pi/2, 0, 0))
    cube(side + ' Upper Arm', (x, 0, 4.22), (0.75, 1.0, 1.22), red, 0.14, rotation=(0, 0, math.radians(-5 if x < 0 else 5)))
    cube(side + ' Elbow', (x, -0.02, 3.48), (0.72, 0.95, 0.42), silver, 0.09)
    cube(side + ' Forearm', (x, -0.02, 2.95), (0.92, 1.12, 0.95), red, 0.14, rotation=(0, 0, math.radians(5 if x < 0 else -5)))
    cube(side + ' Forearm Trim', (x, -0.65, 3.1), (0.47, 0.12, 0.5), white, 0.04)
    cylinder(side + ' Forearm Cannon', (x + (-0.35 if x < 0 else 0.35), -0.8, 3.38), 0.1, 1.3, silver, rotation=(0, math.radians(90), 0), bevel=0.025)
    cylinder(side + ' Cannon Tip', (x + (-0.78 if x < 0 else 0.78), -0.8, 3.38), 0.15, 0.18, outline, rotation=(0, math.radians(90), 0), bevel=0.025)
    cube(side + ' Fist', (x, -0.04, 2.24), (0.95, 1.0, 0.72), blue, 0.16)
    for finger_x in (-0.24, 0, 0.24):
        cube(side + ' Knuckle', (x + finger_x, -0.58, 2.35), (0.17, 0.12, 0.22), silver, 0.025)

cube('Pelvis Outline', (0, 0, 3.08), (2.45, 1.28, 0.72), outline, 0.16)
cube('Pelvis Armor', (0, -0.04, 3.18), (2.2, 1.25, 0.58), silver, 0.13)
cube('Pelvis Red Center', (0, -0.72, 3.2), (0.85, 0.16, 0.33), red, 0.04)
for x in (-0.78, 0.78):
    cylinder('Hip', (x, 0, 2.72), 0.34, 0.5, outline, rotation=(math.pi/2, 0, 0))
    cube('Thigh Blue', (x, 0, 2.25), (0.86, 1.0, 1.02), blue, 0.13)
    cube('Thigh Red', (x, -0.61, 2.28), (0.54, 0.13, 0.62), red, 0.05)
    cube('Knee Silver', (x, -0.68, 1.57), (0.68, 0.2, 0.46), silver, 0.07)
    cube('Shin Outline', (x, 0, 0.77), (1.08, 1.2, 1.25), outline, 0.15)
    cube('Shin Blue', (x, -0.02, 0.82), (0.86, 1.08, 1.08), blue, 0.12)
    cube('Shin White Panel', (x, -0.6, 0.83), (0.36, 0.1, 0.64), white, 0.03)
    cube('Shin Vent Frame', (x, -0.68, 1.05), (0.42, 0.05, 0.58), outline, 0.02)
    for vent_z in (0.86, 0.98, 1.10, 1.22):
        cube('Shin Vent Slat', (x, -0.72, vent_z), (0.28, 0.03, 0.04), silver, 0.008)
    cube('Foot', (x, -0.33, -0.12), (1.28, 1.78, 0.62), blue, 0.13)
    cube('Toe Red', (x, -1.0, -0.06), (1.15, 0.48, 0.34), red, 0.08)

cube('Central Vent Frame', (0, -0.76, 4.0), (0.58, 0.1, 0.56), outline, 0.04)
for z in (3.83, 3.98, 4.13):
    cube('Central Vent', (0, -0.84, z), (0.36, 0.06, 0.06), white, 0.01)

bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.48))
floor = bpy.context.object
floor.name = 'Studio Floor'
floor.data.materials.append(floor_mat)
cylinder('Circular Display Stand', (0, 0, -0.33), 3.7, 0.22, outline, bevel=0.06)
cylinder('Display Glow Ring', (0, 0, -0.19), 3.5, 0.06, cyan, bevel=0.01)

bpy.ops.object.camera_add(location=(0, -22.5, 4.8))
camera = bpy.context.object
camera.name = 'Chibi Hero Camera'
bpy.context.scene.camera = camera
look_at(camera, (0, -0.05, 4.0))
camera.data.lens = 68

bpy.ops.object.light_add(type='AREA', location=(5.0, -8.0, 12.0))
key = bpy.context.object
key.name = 'Soft Key'
key.data.energy = 1450
key.data.size = 5.0
look_at(key, (0, 0, 3.8))
bpy.ops.object.light_add(type='AREA', location=(-6.0, -2.0, 7.0))
fill = bpy.context.object
fill.name = 'Cool Blue Fill'
fill.data.energy = 1050
fill.data.color = (0.05, 0.2, 1.0)
fill.data.size = 4.0
look_at(fill, (0, 0, 4.2))
bpy.ops.object.light_add(type='AREA', location=(3.0, 5.0, 9.0))
rim = bpy.context.object
rim.name = 'Warm Rim'
rim.data.energy = 1600
rim.data.color = (1.0, 0.08, 0.02)
rim.data.size = 3.0
look_at(rim, (0, 0, 4.8))

scene = bpy.context.scene
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.92, 0.94, 0.98, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = '/Users/wuyong/Documents/ChatGPT/3D/transformer_chibi.png'
scene.render.film_transparent = False
scene.view_settings.look = 'AgX - Medium High Contrast'
bpy.context.scene.camera.data.type = 'ORTHO'
bpy.context.scene.camera.data.ortho_scale = 10.0
bpy.ops.wm.save_as_mainfile(filepath='/Users/wuyong/Documents/ChatGPT/3D/transformer_chibi.blend')
bpy.ops.render.render(write_still=True)
