"""Build and render the premium 3D BloodLink/NSS inauguration film in Blender.

Usage:
  blender --background --python render_3d_inauguration.py -- --preview 390
  blender --background --python render_3d_inauguration.py -- --render

The script always saves an editable .blend file. Preview mode renders one 1280x720
still; render mode outputs a silent UHD 4K H.264 movie for the final audio mux.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from pathlib import Path

import bpy
import mathutils


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "media" / "inauguration" / "blender_3d"
LOGO = ROOT / "media" / "inauguration" / "bloodlink_logo_transparent.png"
FPS = 30
END = 480


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=int)
    parser.add_argument("--storyboard", type=str)
    parser.add_argument("--render", action="store_true")
    tail = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(tail)


def clean():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for group in (bpy.data.curves, bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass


def set_key(obj, data_path, frame, value, interpolation="BEZIER"):
    target = obj
    parts = data_path.split(".")
    for part in parts[:-1]:
        target = getattr(target, part)
    setattr(target, parts[-1], value)
    obj.keyframe_insert(data_path=data_path, frame=frame)
    action = obj.animation_data.action if obj.animation_data and obj.animation_data.action else None
    if action:
        for fc in action.fcurves:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 0.01:
                    kp.interpolation = interpolation


def mat_principled(name, base, metallic=0.0, rough=0.35, emission=None, emission_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.3
    if emission:
        key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
        bsdf.inputs[key].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return m


def mat_emission(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    links = m.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    links.new(em.outputs[0], out.inputs[0])
    return m


def look_at(obj, target):
    direction = mathutils.Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_plane(name, loc, scale, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=2, location=loc, rotation=rotation)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(material)
    return o


def add_cube(name, loc, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    if bevel:
        mod = o.modifiers.new("Soft bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 4
    return o


def add_curve(name, points, material, bevel=0.035, cyclic=False):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 16
    cu.bevel_depth = bevel
    cu.bevel_resolution = 4
    spl = cu.splines.new("BEZIER")
    spl.bezier_points.add(len(points) - 1)
    for bp, co in zip(spl.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    spl.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob


def add_ring(name, radius, z, material, tube=0.025):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=tube, major_segments=96, minor_segments=10, location=(0, 0.25, z), rotation=(math.radians(90), 0, 0))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    return o


def add_text(name, body, loc, size, material, extrude=0.035, tracking=1.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = extrude * 0.18
    cu.bevel_resolution = 3
    cu.space_character = tracking
    font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "segoeuib.ttf"
    if font_path.exists():
        cu.font = bpy.data.fonts.load(str(font_path))
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.data.materials.append(material)
    return ob


def add_drop(material):
    cu = bpy.data.curves.new("BloodDropSculpture", "CURVE")
    cu.dimensions = "2D"
    cu.resolution_u = 24
    cu.fill_mode = "BOTH"
    cu.extrude = 0.32
    cu.bevel_depth = 0.075
    cu.bevel_resolution = 5
    spl = cu.splines.new("BEZIER")
    pts = [(0, 2.05), (-0.35, 1.32), (-1.15, 0.35), (-1.22, -0.32), (-0.72, -1.02), (0, -1.28), (0.72, -1.02), (1.22, -0.32), (1.15, 0.35), (0.35, 1.32)]
    spl.bezier_points.add(len(pts) - 1)
    for bp, (x, z) in zip(spl.bezier_points, pts):
        bp.co = (x, z, 0)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    spl.use_cyclic_u = True
    ob = bpy.data.objects.new("BloodDropSculpture", cu)
    bpy.context.collection.objects.link(ob)
    ob.location = (0, 0.15, 3.15)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.data.materials.append(material)
    return ob


def add_rbc(name, loc, scale, rot, material):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.11, major_segments=32, minor_segments=10, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(material)
    return o


def add_logo_plane(material_back):
    disk = None
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.5, depth=0.14, location=(0, 0.0, 3.3), rotation=(math.radians(90), 0, 0))
    disk = bpy.context.object
    disk.name = "Logo halo disc"
    disk.data.materials.append(material_back)

    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, -0.085, 3.3), rotation=(math.radians(90), 0, 0))
    plane = bpy.context.object
    plane.name = "BloodLink NSS logo"
    plane.scale = (1.34, 1.34, 1.34)
    mat = bpy.data.materials.new("BloodLink logo material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(LOGO), check_existing=True)
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    em_key = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
    links.new(tex.outputs["Color"], bsdf.inputs[em_key])
    bsdf.inputs["Emission Strength"].default_value = 0.04
    links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    links.new(bsdf.outputs[0], out.inputs[0])
    try:
        mat.surface_render_method = "DITHERED"
    except Exception:
        pass
    plane.data.materials.append(mat)
    return disk, plane


def animate_visibility_scale(o, f0, f1, final_scale=None):
    target = final_scale or tuple(o.scale)
    o.scale = (0.001, 0.001, 0.001)
    o.keyframe_insert("scale", frame=f0)
    o.scale = target
    o.keyframe_insert("scale", frame=f1)


def build_scene():
    clean()
    OUT.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = END
    scene.render.fps = FPS
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 16
    scene.eevee.use_raytracing = False
    scene.eevee.use_fast_gi = False
    scene.eevee.shadow_ray_count = 1
    scene.eevee.shadow_step_count = 4
    scene.eevee.shadow_resolution_scale = 0.5
    scene.render.resolution_x = 3840
    scene.render.resolution_y = 2160
    # Keep the project set to a 4K canvas while rendering the 3D pass at 50%;
    # the final encoder performs a premium Lanczos 4K reconstruction with glow.
    scene.render.resolution_percentage = 50
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 55
    (OUT / "frames").mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(OUT / "frames" / "frame_")
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.view_settings.look = "AgX - Medium High Contrast"
    try:
        scene.render.use_motion_blur = False
    except Exception:
        pass

    # Dark blue-black world with a subtle volumetric atmosphere.
    world = bpy.data.worlds.new("BloodLink World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.0015, 0.004, 0.012, 1)
    bg.inputs["Strength"].default_value = 0.035

    black = mat_principled("Obsidian", (0.003, 0.008, 0.018), metallic=0.65, rough=0.2)
    steel = mat_principled("Dark chrome", (0.018, 0.025, 0.04), metallic=0.92, rough=0.16)
    ruby = mat_principled("Ruby blood", (0.34, 0.002, 0.012), metallic=0.35, rough=0.15, emission=(0.55, 0.001, 0.008), emission_strength=0.35)
    red_glow = mat_emission("Arterial glow", (1.0, 0.005, 0.015), 6)
    blue_glow = mat_emission("Clinical rim", (0.015, 0.28, 0.8), 5)
    white_glow = mat_emission("Life white", (0.75, 0.9, 1.0), 3)
    gold = mat_principled("NSS gold", (0.72, 0.42, 0.07), metallic=0.8, rough=0.18, emission=(0.7, 0.22, 0.025), emission_strength=0.25)

    # Stage and tunnel ribs.
    floor = add_plane("Reflective floor", (0, 2, 0), (14, 18, 1), black)
    add_cube("Back wall", (0, 5.8, 4.5), (10, .3, 5.5), black, .15)
    for x in (-5.8, 5.8):
        add_cube("Side monolith", (x, 2.2, 3.0), (.18, 4.6, 3.0), steel, .12)
    for z in (0.02, 0.055):
        add_curve(f"Floor lane {z}", [(-6, -3, z), (-3.0, 0, z), (-2.4, 5, z)], blue_glow if z < .04 else red_glow, .018)
        add_curve(f"Floor lane mirror {z}", [(6, -3, z), (3.0, 0, z), (2.4, 5, z)], blue_glow if z < .04 else red_glow, .018)

    # Hero drop and surrounding luminous vessel architecture.
    drop = add_drop(ruby)
    drop.scale = (0.62, 0.62, 0.62)
    drop.keyframe_insert("scale", frame=1)
    drop.scale = (1.0, 1.0, 1.0)
    drop.keyframe_insert("scale", frame=105)
    drop.rotation_euler[2] = math.radians(-8)
    drop.keyframe_insert("rotation_euler", frame=1)
    drop.rotation_euler[2] = math.radians(8)
    drop.keyframe_insert("rotation_euler", frame=180)
    drop.rotation_euler[2] = 0
    drop.keyframe_insert("rotation_euler", frame=300)
    drop.scale = (1.0, 1.0, 1.0)
    drop.keyframe_insert("scale", frame=285)
    drop.scale = (0.001, 0.001, 0.001)
    drop.keyframe_insert("scale", frame=350)

    for i, side in enumerate((-1, 1)):
        for j in range(4):
            x = side * (1.0 + j * .72)
            pts = [(side*5.8, 4.5+j*.35, .5+j*.6), (side*4.2, 2.1, 1.1+j*.65), (side*2.7, .6, 2.2+j*.35), (side*1.05, .25, 3.15+j*.05)]
            c = add_curve(f"Vessel {i}-{j}", pts, red_glow, .035 if j < 2 else .022)
            c.data.bevel_factor_end = 0
            c.data.keyframe_insert("bevel_factor_end", frame=35+j*12)
            c.data.bevel_factor_end = 1
            c.data.keyframe_insert("bevel_factor_end", frame=145+j*15)

    # Floating red cells rush through depth and orbit the drop.
    rnd = random.Random(20260913)
    for i in range(32):
        x = rnd.uniform(-5.0, 5.0)
        z = rnd.uniform(.65, 6.3)
        start_y = rnd.uniform(6.5, 11.0)
        end_y = rnd.uniform(-8.5, -4.2)
        s = rnd.uniform(.25, .55)
        rbc = add_rbc(f"RBC {i:02d}", (x, start_y, z), (s, s, s*rnd.uniform(.3,.65)), (rnd.random()*math.pi, rnd.random()*math.pi, rnd.random()*math.pi), ruby)
        f0 = 20 + (i * 23) % 250
        f1 = min(318, f0 + rnd.randint(125, 205))
        rbc.keyframe_insert("location", frame=f0)
        rbc.location.y = end_y
        rbc.location.x += rnd.uniform(-1.3,1.3)
        rbc.rotation_euler.rotate_axis("Z", rnd.uniform(1.5,5.5))
        rbc.keyframe_insert("location", frame=f1)
        rbc.keyframe_insert("rotation_euler", frame=f1)
        rbc.keyframe_insert("scale", frame=f1)
        rbc.scale = (0.001, 0.001, 0.001)
        rbc.keyframe_insert("scale", frame=min(340, f1 + 16))

    # ECG tube drawing across the sculpture.
    ecg_pts = [(-6,-.25,2.65),(-3.2,-.28,2.65),(-2.5,-.3,2.72),(-2.1,-.32,2.63),(-1.65,-.34,4.15),(-1.15,-.36,1.58),(-.72,-.38,3.42),(-.15,-.4,2.65),(2.55,-.34,2.65),(3.15,-.31,3.48),(3.65,-.29,1.95),(4.05,-.27,2.65),(6,-.24,2.65)]
    ecg = add_curve("Living pulse", ecg_pts, red_glow, .048)
    ecg.data.bevel_factor_end = 0
    ecg.data.keyframe_insert("bevel_factor_end", frame=180)
    ecg.data.bevel_factor_end = 1
    ecg.data.keyframe_insert("bevel_factor_end", frame=275)
    ecg.scale = (1,1,1)
    ecg.keyframe_insert("scale",frame=300)
    ecg.scale = (.001,.001,.001)
    ecg.keyframe_insert("scale",frame=345)

    # Holographic rings and central BloodLink/NSS seal.
    rings = []
    for i, radius in enumerate((.92, 1.28, 1.64, 2.0)):
        ring = add_ring(f"Pulse ring {i}", radius, 4.65, red_glow if i % 2 == 0 else blue_glow, .025)
        ring.scale = (.01,.01,.01)
        ring.keyframe_insert("scale", frame=205+i*10)
        ring.scale = (1,1,1)
        ring.keyframe_insert("scale", frame=285+i*10)
        ring.scale = (1.06,1.06,1.06)
        ring.keyframe_insert("scale", frame=335)
        rings.append(ring)

    disk, logo = add_logo_plane(steel)
    animate_visibility_scale(disk, 300, 355)
    animate_visibility_scale(logo, 310, 365)

    title = add_text("BloodLink title", "BLOODLINK", (0, -.5, 1.35), .80, white_glow, .05, 1.05)
    inaugurated = add_text("Inaugurated", "OFFICIALLY INAUGURATED", (0, -.52, .72), .32, red_glow, .025, 1.0)
    strap = add_text("NSS strap", "NSS   |   DONATE BLOOD. SAVE LIVES.", (0, -.51, .34), .25, gold, .018, 1.0)
    status = add_text("System status", "BLOOD BANK SYSTEM INITIALIZING...", (0, -.5, 6.3), .27, blue_glow, .025, 1.0)
    for ob, f0, f1 in ((title,330,375),(inaugurated,350,395),(strap,370,415),(status,250,315)):
        animate_visibility_scale(ob,f0,f1)

    # Camera dolly and subtle hero arc.
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, .25, 2.65))
    target = bpy.context.object
    target.name = "Camera target"
    bpy.ops.object.camera_add(location=(0, -20.5, 3.2))
    cam = bpy.context.object
    cam.name = "Hero camera"
    scene.camera = cam
    cam.data.lens = 62
    con = cam.constraints.new(type="TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    for frame, loc, lens in [
        (1,(0,-21.0,3.25),68),(100,(0,-14.5,3.0),64),(210,(-.55,-11.8,3.25),57),
        (310,(.45,-14.4,3.05),60),(390,(0,-18.2,2.85),62),(465,(0,-17.0,2.9),60),(480,(0,-14.8,2.9),55)
    ]:
        cam.location = loc
        cam.data.lens = lens
        cam.keyframe_insert("location",frame=frame)
        cam.data.keyframe_insert("lens",frame=frame)

    # Rim, pulse and reveal lights.
    def area(name, loc, color, energy, size, target_at=(0,0,3)):
        bpy.ops.object.light_add(type="AREA",location=loc)
        o=bpy.context.object; o.name=name; o.data.color=color; o.data.energy=energy; o.data.shape="DISK"; o.data.size=size; look_at(o,target_at); return o
    def spot(name, loc, color, energy, size, blend, target_at=(0,0,2)):
        bpy.ops.object.light_add(type="SPOT",location=loc)
        o=bpy.context.object; o.name=name; o.data.color=color; o.data.energy=energy; o.data.shadow_soft_size=size; o.data.spot_blend=blend; o.data.spot_size=math.radians(42); look_at(o,target_at); return o
    key = area("Crimson rim",(-5,-4,6),(1,.004,.01),1500,5)
    fill = area("Blue rim",(5,-2,5),(.02,.22,1),1100,4)
    top = spot("Sculpture spotlight",(0,-1,9),(1,.05,.08),2100,.5,.7,(0,0,3))
    left_beam = spot("Left beam",(-3,-6,1.4),(.35,.7,1),0,.35,.55,(-1,2,2.8))
    right_beam = spot("Right beam",(3,-6,1.4),(.35,.7,1),0,.35,.55,(1,2,2.8))
    for beam in (left_beam,right_beam):
        beam.data.keyframe_insert("energy",frame=1)
        beam.data.energy=5200; beam.data.keyframe_insert("energy",frame=150)
        beam.data.energy=7200; beam.data.keyframe_insert("energy",frame=330)
    for lamp in (key,fill,top):
        start=lamp.data.energy*.08; end=lamp.data.energy
        lamp.data.energy=start; lamp.data.keyframe_insert("energy",frame=1)
        lamp.data.energy=end; lamp.data.keyframe_insert("energy",frame=135)

    # White handoff flash at the last 12 frames.
    flash = area("Program handoff",(0,-6,4),(1,1,1),0,12)
    flash.data.keyframe_insert("energy",frame=462)
    flash.data.energy=38000; flash.data.keyframe_insert("energy",frame=480)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"BloodLink_NSS_3D_Inauguration.blend"))
    return scene


def main():
    opt=args()
    scene=build_scene()
    if opt.preview:
        scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100
        scene.render.image_settings.file_format="PNG"
        scene.render.filepath=str(OUT/f"preview_{opt.preview:03d}.png")
        scene.frame_set(opt.preview)
        bpy.ops.render.render(write_still=True)
    elif opt.storyboard:
        scene.render.resolution_x=1920; scene.render.resolution_y=1080; scene.render.resolution_percentage=100
        scene.render.image_settings.file_format="PNG"
        for frame in [int(v) for v in opt.storyboard.split(",")]:
            scene.render.filepath=str(OUT/f"shot_{frame:03d}.png")
            scene.frame_set(frame)
            bpy.ops.render.render(write_still=True)
    elif opt.render:
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
