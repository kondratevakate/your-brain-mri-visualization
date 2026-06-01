"""Styles #1 (clear glass) and #2 (frosted blue glass) via Blender Cycles.

Run inside a Python with `bpy` installed (headless Blender wheel). Same scene
graph for both styles — they differ only in the GlassStyle dataclass.

Pipeline:
  1. reset scene
  2. import brain trimesh(es) as bpy meshes
  3. apply glass material (Principled BSDF + Volume Absorption)
  4. set up HDRI environment + key/rim area lights
  5. position camera, render to PNG

References:
  - Cycles Principled BSDF: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html
  - Volume Absorption gives wavelength-dependent tint by Beer's law:
    transmitted = base_color ** (density * thickness)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh


@dataclass
class GlassStyle:
    name: str = "clear"
    # mesh quality
    subdivision_levels: int = 0          # 0 = off; 2 = ultra-smooth (16x faces)
    # Principled BSDF
    base_color: tuple = (0.95, 0.97, 1.00, 1.0)    # near-white for clear glass
    roughness: float = 0.05                          # 0 = mirror-clear, 0.3 = frosted
    ior: float = 1.45                                # crown glass
    transmission: float = 1.0
    # Volume Absorption (Beer's law tint) — color light is *absorbed* as it passes
    # through the volume. base="warm white" + absorption=blue gives cyan-glass.
    absorption_color: tuple = (1.0, 1.0, 1.0)       # no tint for clear
    absorption_density: float = 0.0                  # 0 = no volume effect
    # scene
    background_color: tuple = (1.0, 1.0, 1.0)       # solid white backdrop
    hdri_strength: float = 1.2
    studio_env: bool = False                         # procedural studio HDRI-like
    key_light_energy: float = 800.0                  # watts (area light)
    rim_light_energy: float = 400.0
    # render
    resolution: tuple = (1600, 1600)
    samples: int = 128                               # Cycles samples
    use_denoise: bool = True
    # camera
    camera_azim_deg: float = 25.0                    # rotation around vertical
    camera_elev_deg: float = 8.0
    camera_distance_factor: float = 2.2              # x bounding sphere radius
    camera_lens_mm: float = 50.0


def style_clear_glass() -> GlassStyle:
    """Style #1 — iStock-like clear cut glass, white background, sharp highlights."""
    return GlassStyle(
        name="clear",
        base_color=(0.96, 0.98, 1.00, 1.0),
        roughness=0.0,
        ior=1.52,
        absorption_color=(0.95, 0.97, 1.00),
        # mesh is in mm. Beer's law: T = color**(density*thickness_mm).
        absorption_density=0.003,
        hdri_strength=2.0,
        studio_env=True,
        subdivision_levels=2,
        key_light_energy=1500.0,
        rim_light_energy=1200.0,
    )


def style_frosted_blue() -> GlassStyle:
    """Style #2 — soft frosted blue glass on a cool gradient background."""
    return GlassStyle(
        name="frosted_blue",
        base_color=(0.75, 0.85, 0.95, 1.0),
        roughness=0.22,
        ior=1.45,
        absorption_color=(0.55, 0.75, 0.95),         # blue tint via absorption
        absorption_density=0.012,                     # mm-scale (see Beer's law note)
        background_color=(0.78, 0.85, 0.92),         # cool gradient applied in setup
        hdri_strength=1.0,
        key_light_energy=600.0,
        rim_light_energy=500.0,
    )


# ---------------------------------------------------------------------------
# Blender side — only imported when actually rendering, so that the wireframe
# pipeline can import this module to inspect GlassStyle without needing bpy.
# ---------------------------------------------------------------------------

def render_glass(
    brain: trimesh.Trimesh,
    rois: list[trimesh.Trimesh] | None,
    out_path: str | Path,
    style: GlassStyle | None = None,
) -> Path:
    import bpy  # local import: bpy is heavy and may be absent

    style = style or style_clear_glass()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    _reset_scene()
    brain_obj = _import_trimesh(brain, name="Brain")
    _apply_glass_material(brain_obj, style)
    if style.subdivision_levels > 0:
        _add_subdivision(brain_obj, levels=style.subdivision_levels)

    # ROIs go inside the glass shell as Emission-shaded solids
    roi_objs = []
    for i, roi in enumerate(rois or []):
        obj = _import_trimesh(roi, name=f"ROI_{i}")
        _apply_emission_material(obj, color=(0.95, 0.25, 0.20), strength=3.0)
        roi_objs.append(obj)

    _setup_world(style)
    _setup_lights(brain, style)
    _setup_camera(brain, style)
    _setup_render(style, out_path)

    bpy.ops.render.render(write_still=True)
    return out_path


def _reset_scene():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _import_trimesh(mesh: trimesh.Trimesh, name: str):
    import bpy
    me = bpy.data.meshes.new(name)
    me.from_pydata(mesh.vertices.tolist(), [], mesh.faces.tolist())
    me.update()
    # Blender 4.1+ removed Mesh.use_auto_smooth (moved to a modifier);
    # per-poly smooth flag still works for our use-case.
    for p in me.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    return obj


def _apply_glass_material(obj, style: GlassStyle):
    import bpy
    mat = bpy.data.materials.new(name=f"Glass_{style.name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = style.base_color
    bsdf.inputs["Roughness"].default_value = style.roughness
    bsdf.inputs["IOR"].default_value = style.ior
    # Transmission input name changed across Blender versions
    for key in ("Transmission Weight", "Transmission"):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = style.transmission
            break

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    if style.absorption_density > 0:
        vol = nodes.new("ShaderNodeVolumeAbsorption")
        vol.inputs["Color"].default_value = (*style.absorption_color, 1.0)
        vol.inputs["Density"].default_value = style.absorption_density
        links.new(vol.outputs["Volume"], out.inputs["Volume"])

    obj.data.materials.append(mat)


def _add_subdivision(obj, levels: int = 2):
    """Catmull-Clark subdivision — Cycles renders this without baking, so the
    on-disk mesh stays small but the rendered surface is ultra-smooth."""
    import bpy
    mod = obj.modifiers.new(name="Subsurf", type="SUBSURF")
    mod.levels = levels         # viewport
    mod.render_levels = levels  # render


def _apply_emission_material(obj, color, strength=2.0):
    import bpy
    mat = bpy.data.materials.new(name=f"Emit_{obj.name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*color, 1.0)
    emit.inputs["Strength"].default_value = strength
    mat.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    obj.data.materials.append(mat)


def _setup_world(style: GlassStyle):
    """Build a procedural studio environment.

    studio_env=True chains: TexCoord -> Mapping -> Gradient -> ColorRamp -> Background.
    This produces a bright top / soft bottom — like a softbox above a sweep —
    which is what creates the iStock cut-glass highlights when the brain reflects
    the bright top hemisphere off its top curves.
    """
    import bpy
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputWorld")
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = style.hdri_strength
    links.new(bg.outputs["Background"], out.inputs["Surface"])

    if not style.studio_env:
        bg.inputs["Color"].default_value = (*style.background_color, 1.0)
        return

    # studio gradient: bright top -> soft bottom
    tex_coord = nodes.new("ShaderNodeTexCoord")
    grad = nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "LINEAR"
    sep = nodes.new("ShaderNodeSeparateXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    # 0 = bottom, 1 = top
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.92, 0.94, 0.97, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    # mid kick: bright softbox highlight
    mid = ramp.color_ramp.elements.new(0.75)
    mid.color = (2.5, 2.5, 2.5, 1.0)   # HDR > 1 produces specular highlights

    # use generated Z coord -> linear gradient top to bottom
    links.new(tex_coord.outputs["Generated"], sep.inputs["Vector"])
    # remap Z (0..1) into the gradient input via a Combine
    combine = nodes.new("ShaderNodeCombineXYZ")
    links.new(sep.outputs["Z"], combine.inputs["X"])
    links.new(combine.outputs["Vector"], grad.inputs["Vector"])
    links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bg.inputs["Color"])


def _setup_lights(brain: trimesh.Trimesh, style: GlassStyle):
    import bpy
    bounds = brain.bounds
    radius = float(np.linalg.norm(bounds[1] - bounds[0]) / 2)
    center = brain.centroid

    def _add_area(name, loc, energy, size_factor=1.5):
        light_data = bpy.data.lights.new(name=name, type="AREA")
        light_data.energy = energy
        light_data.size = radius * size_factor
        obj = bpy.data.objects.new(name=name, object_data=light_data)
        obj.location = loc
        # point at centroid
        direction = center - np.asarray(loc)
        # rotation_euler — use track-to via simple lookat (z-up)
        from mathutils import Vector
        d = Vector(direction).normalized()
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = d.to_track_quat("-Z", "Y")
        bpy.context.collection.objects.link(obj)
        return obj

    _add_area("Key",  center + np.array([radius * 2.0, -radius * 1.5, radius * 1.5]),
              style.key_light_energy)
    _add_area("Rim",  center + np.array([-radius * 2.0, radius * 1.0, radius * 0.5]),
              style.rim_light_energy, size_factor=2.0)
    _add_area("Fill", center + np.array([0.0, -radius * 2.5, -radius * 0.5]),
              style.key_light_energy * 0.25, size_factor=2.5)


def _setup_camera(brain: trimesh.Trimesh, style: GlassStyle):
    import bpy
    from mathutils import Vector
    bounds = brain.bounds
    radius = float(np.linalg.norm(bounds[1] - bounds[0]) / 2)
    center = brain.centroid

    az = np.deg2rad(style.camera_azim_deg)
    el = np.deg2rad(style.camera_elev_deg)
    dist = radius * style.camera_distance_factor
    cam_loc = center + dist * np.array([np.cos(el) * np.cos(az),
                                        np.cos(el) * np.sin(az),
                                        np.sin(el)])

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = style.camera_lens_mm
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    cam_obj.location = cam_loc
    direction = Vector(center - cam_loc).normalized()
    cam_obj.rotation_mode = "QUATERNION"
    cam_obj.rotation_quaternion = direction.to_track_quat("-Z", "Y")
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj


def _setup_render(style: GlassStyle, out_path: Path):
    import bpy
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    # Prefer GPU if available
    prefs = bpy.context.preferences.addons.get("cycles")
    if prefs is not None:
        try:
            prefs.preferences.compute_device_type = "OPTIX"
            scene.cycles.device = "GPU"
        except Exception:
            scene.cycles.device = "CPU"
    scene.cycles.samples = style.samples
    scene.cycles.use_denoising = style.use_denoise
    scene.cycles.transparent_max_bounces = 12   # glass needs many bounces
    scene.cycles.volume_max_steps = 64
    scene.render.resolution_x, scene.render.resolution_y = style.resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.render.filepath = str(out_path.resolve())
