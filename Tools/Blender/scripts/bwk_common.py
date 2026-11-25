"""Shared helpers for Bubble Wash Kingdom Blender asset scripts (Blender 5.3, headless).

Usage inside an asset script:
    import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bwk_common as C
    C.reset_scene()
    ...
    C.export_fbx([obj], C.model_path("Props", "SM_Coin"))
    C.render_preview(C.preview_path("SM_Coin"), target=(0, 0, 0), distance=2.0)

Conventions (see Docs/AssetSpec.md): meters, Z up, asset front faces -Y, right side is -X.
"""
import math
import os

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
MODELS = os.path.join(ROOT, "Assets", "BubbleWashKingdom", "Art", "Models")
PREVIEWS = os.path.join(ROOT, "Docs", "AssetPreviews")
WORK = os.path.join(ROOT, "Tools", "Blender", "work")
BW = 0.85  # mascot body width in meters


# ------------------------------------------------------------------ paths
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def model_path(group, name):
    return os.path.join(ensure_dir(os.path.join(MODELS, group)), name + ".fbx")


def preview_path(name):
    return os.path.join(ensure_dir(PREVIEWS), name + ".png")


def work_path(name):
    return os.path.join(ensure_dir(WORK), name + ".blend")


# ------------------------------------------------------------------ scene
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = 30
    return scene


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), alpha)


def material(name, color="#FFFFFF", metallic=0.0, roughness=0.5, emission=None, emission_strength=0.0,
             alpha=1.0, coat=0.0):
    """Get or create a Principled BSDF material whose slot name is the Unity remap key."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_rgba(color)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    if emission:
        bsdf.inputs["Emission Color"].default_value = hex_rgba(emission)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            mat.surface_render_method = 'BLENDED'
        except Exception:
            pass
    mat.diffuse_color = hex_rgba(color, alpha)
    return mat


def assign_materials(obj, mats):
    obj.data.materials.clear()
    for m in mats:
        obj.data.materials.append(m)


def select_only(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def apply_transforms(obj, location=False):
    select_only([obj])
    bpy.ops.object.transform_apply(location=location, rotation=True, scale=True)


def shade_smooth(obj, angle_deg=40.0):
    """Smooth shading with sharp edges above the angle (Blender 4.1+ 'smooth by angle')."""
    select_only([obj])
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle_deg))
    except Exception:
        bpy.ops.object.shade_smooth()


def join(objs, name):
    select_only(objs)
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.data.name = name
    return o


def mesh_from_bmesh(name, bm, collection=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def tri_count(obj):
    deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    me = ev.to_mesh()
    n = sum(len(p.vertices) - 2 for p in me.polygons)
    ev.to_mesh_clear()
    return n


# ------------------------------------------------------------------ export
def export_fbx(objs, path, anim=False):
    select_only(objs)
    # include children (e.g. meshes parented to an armature)
    for o in objs:
        for c in o.children_recursive:
            c.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={'MESH', 'ARMATURE', 'EMPTY'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
        bake_space_transform=False, use_mesh_modifiers=True, mesh_smooth_type='FACE', use_tspace=True,
        add_leaf_bones=False, primary_bone_axis='Y', secondary_bone_axis='X', use_armature_deform_only=True,
        bake_anim=anim, bake_anim_use_all_actions=anim, bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0, path_mode='AUTO',
        embed_textures=False)
    print("EXPORTED", path)
    return path


def save_work(name):
    bpy.ops.wm.save_as_mainfile(filepath=work_path(name), compress=True)


# ------------------------------------------------------------------ preview render
def _set_engine(scene):
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            scene.render.engine = engine
            return engine
        except TypeError:
            continue
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32
    return 'CYCLES'


def setup_preview_scene(background="#2A1B4A", strength=0.6):
    scene = bpy.context.scene
    engine = _set_engine(scene)
    try:
        scene.eevee.taa_render_samples = 32
    except Exception:
        pass
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    world = bpy.data.worlds.get("PreviewWorld") or bpy.data.worlds.new("PreviewWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = hex_rgba(background)
    bg.inputs[1].default_value = strength
    scene.world = world
    return engine


def _light(name, kind, energy, color, loc, target, size=2.0):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = hex_rgba(color)[:3]
    if kind == 'AREA':
        data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    direction = Vector(target) - Vector(loc)
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return obj


def add_studio_lights(target=(0, 0, 0.5), scale=1.0):
    t = Vector(target)
    lights = [
        _light("Key", 'AREA', 600 * scale * scale, "#FFE7C2", t + Vector((2.5, -3.0, 3.0)) * scale, t, 2.5 * scale),
        _light("Fill", 'AREA', 250 * scale * scale, "#BFD8FF", t + Vector((-3.0, -2.0, 1.5)) * scale, t, 3.0 * scale),
        _light("Rim", 'AREA', 500 * scale * scale, "#FF8AD8", t + Vector((0.0, 3.5, 2.5)) * scale, t, 2.0 * scale),
    ]
    return lights


def add_camera(location, target, lens=50.0):
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    direction = Vector(target) - Vector(location)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    return cam


def render_preview(path, camera_location, target, lens=50.0, resolution=(1000, 1000), light_scale=1.0,
                   background="#2A1B4A", keep_rig=False):
    """Render one preview image. Creates a temporary camera + 3-point lights around `target`."""
    scene = bpy.context.scene
    engine = setup_preview_scene(background)
    temp = add_studio_lights(target, light_scale)
    cam = add_camera(camera_location, target, lens)
    temp.append(cam)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", engine, path)
    if not keep_rig:
        for o in temp:
            bpy.data.objects.remove(o, do_unlink=True)
    return path
