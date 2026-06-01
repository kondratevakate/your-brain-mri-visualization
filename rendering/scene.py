"""Adaptive brain rendering — composable Scene system.

The core idea: a render is a *composition* of independent, swappable parts, so
the SAME base meshes can serve many purposes (anatomical figure, glass art,
coral, tractography) by recombining layers + materials + lighting + camera.

    Scene(
        layers=[
            Layer(shell_mesh,   Material(kind="glass")),
            Layer(nuclei_mesh,  Material(kind="emission", emission_color=...)),
            # Layer(tract_curves, Material(kind="emission")),   # tracts  (next)
            # Layer(tentacles,    Material(kind="sss")),        # anemone (later)
        ],
        light=LightRig("studio"),
        camera=CameraRig(dof=True),
    )

Each Layer carries an optional Surface (procedural displacement texture), so a
shell can become "brain coral" without changing its mesh — just its surface.

This module is the GENERIC compositor. Style presets (glass / coral / atlas)
are thin factory functions that fill these dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import trimesh

# Reuse the truly generic Blender helpers already written for the glass style.
from rendering.style_glass_blender import (
    _reset_scene,
    _import_trimesh,
    _add_subdivision,
)


# ---------------------------------------------------------------------------
# The four orthogonal axes of an adaptive render.
# ---------------------------------------------------------------------------

@dataclass
class Material:
    """A swappable surface appearance. kind dispatches the shader graph."""
    kind: str = "diffuse"          # glass | sss | stone | emission | diffuse
    color: tuple = (0.80, 0.80, 0.82, 1.0)
    roughness: float = 0.35
    ior: float = 1.45
    transmission: float = 0.0       # glass
    absorption_color: tuple = (1.0, 1.0, 1.0)
    absorption_density: float = 0.0  # glass volume tint (mm-scale, ~0.003-0.02)
    sss_weight: float = 0.0          # sss
    sss_radius: tuple = (6.0, 2.0, 1.0)   # mm; R scatters farthest -> warm glow
    emission_color: tuple = (0.0, 0.0, 0.0)
    emission_strength: float = 0.0   # emission / tracts


@dataclass
class Surface:
    """Procedural displacement applied to a layer's mesh (the 'texture' slot)."""
    texture: str = "none"            # none | WOOD | STUCCI | MUSGRAVE | VORONOI | CLOUDS
    strength: float = 0.0            # mm of displacement
    noise_scale: float = 8.0
    turbulence: float = 5.0
    subdivide: int = 3               # subsurf levels before displacing


@dataclass
class Layer:
    mesh: trimesh.Trimesh
    material: Material
    surface: Surface | None = None
    smooth: bool = True
    subdivision: int = 0             # render-time Catmull-Clark for the shell
    name: str = "layer"


@dataclass
class LightRig:
    preset: str = "studio"           # studio | reef | dramatic
    strength: float = 1.0
    background: tuple = (1.0, 1.0, 1.0)


@dataclass
class CameraRig:
    azim_deg: float = 25.0
    elev_deg: float = 8.0
    distance_factor: float = 2.4
    lens_mm: float = 50.0
    dof: bool = False
    fstop: float = 2.8
    focus_factor: float = 1.0        # 1.0 = focus on front surface


@dataclass
class Scene:
    layers: list[Layer]
    light: LightRig = field(default_factory=LightRig)
    camera: CameraRig = field(default_factory=CameraRig)
    resolution: tuple = (1200, 1200)
    samples: int = 96
    use_denoise: bool = True


# ---------------------------------------------------------------------------
# Compositor
# ---------------------------------------------------------------------------

def render_scene(scene: Scene, out_path: str | Path, preview: bool = False) -> Path:
    import bpy

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _write_sidecar(scene, out_path, preview)

    _reset_scene()

    objs = []
    for i, layer in enumerate(scene.layers):
        obj = _import_trimesh(layer.mesh, name=layer.name or f"Layer_{i}")
        if layer.material.kind == "tract" and _has_vertex_colors(layer.mesh):
            _set_vertex_colors(obj, layer.mesh.visual.vertex_colors)
        # preview skips geometry-heavy displacement/subdivision (layout-only pass)
        if not preview and layer.surface and layer.surface.texture != "none":
            _apply_surface(obj, layer.surface)
        if not preview and layer.subdivision > 0:
            _add_subdivision(obj, levels=layer.subdivision)
        _apply_material(obj, layer.material)
        objs.append(obj)

    # All layers were pre-centered together by the caller; use first as anchor.
    anchor = scene.layers[0].mesh
    _setup_world(scene.light)
    _setup_lights(anchor, scene.light)
    _setup_camera(anchor, scene.camera)
    _setup_render(scene, out_path, preview)

    bpy.ops.render.render(write_still=True)
    return out_path


def _has_vertex_colors(mesh) -> bool:
    try:
        return mesh.visual.vertex_colors is not None and len(mesh.visual.vertex_colors)
    except Exception:
        return False


def _set_vertex_colors(obj, rgba_uint8):
    """Transfer trimesh per-vertex RGBA into a Blender POINT color attribute."""
    import numpy as np
    me = obj.data
    col = me.color_attributes.new(name="dir", type="BYTE_COLOR", domain="POINT")
    flat = (np.asarray(rgba_uint8, dtype=float) / 255.0).ravel()
    col.data.foreach_set("color", flat)


def _write_sidecar(scene: Scene, out_path: Path, preview: bool):
    """Write a reproducibility JSON next to the render (no raw geometry)."""
    import json
    from dataclasses import asdict

    def layer_dict(lyr: Layer):
        return {
            "name": lyr.name,
            "faces": int(len(lyr.mesh.faces)),
            "verts": int(len(lyr.mesh.vertices)),
            "subdivision": lyr.subdivision,
            "material": asdict(lyr.material),
            "surface": asdict(lyr.surface) if lyr.surface else None,
        }

    doc = {
        "output": out_path.name,
        "preview": preview,
        "resolution": list(scene.resolution),
        "samples": scene.samples,
        "light": asdict(scene.light),
        "camera": asdict(scene.camera),
        "layers": [layer_dict(l) for l in scene.layers],
    }
    out_path.with_suffix(".json").write_text(json.dumps(doc, indent=2))


def _apply_material(obj, mat: Material):
    import bpy
    m = bpy.data.materials.new(name=f"{mat.kind}_{obj.name}")
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")

    if mat.kind == "tract":
        vc = nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "dir"
        emit = nodes.new("ShaderNodeEmission")
        emit.inputs["Strength"].default_value = mat.emission_strength or 2.0
        links.new(vc.outputs["Color"], emit.inputs["Color"])
        links.new(emit.outputs["Emission"], out.inputs["Surface"])
        obj.data.materials.append(m)
        return

    if mat.kind == "emission":
        emit = nodes.new("ShaderNodeEmission")
        emit.inputs["Color"].default_value = (*mat.emission_color, 1.0)
        emit.inputs["Strength"].default_value = mat.emission_strength
        links.new(emit.outputs["Emission"], out.inputs["Surface"])
        obj.data.materials.append(m)
        return

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = mat.color
    bsdf.inputs["Roughness"].default_value = mat.roughness
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = mat.ior

    if mat.kind == "glass":
        bsdf.inputs["Transmission Weight"].default_value = mat.transmission or 1.0
    if mat.kind == "sss":
        bsdf.inputs["Subsurface Weight"].default_value = mat.sss_weight or 1.0
        bsdf.inputs["Subsurface Radius"].default_value = mat.sss_radius
    # 'stone' / 'diffuse' just use base color + roughness as-is.

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    if mat.kind == "glass" and mat.absorption_density > 0:
        vol = nodes.new("ShaderNodeVolumeAbsorption")
        vol.inputs["Color"].default_value = (*mat.absorption_color, 1.0)
        vol.inputs["Density"].default_value = mat.absorption_density
        links.new(vol.outputs["Volume"], out.inputs["Volume"])

    obj.data.materials.append(m)


def _apply_surface(obj, surf: Surface):
    """Subdivide + Displace via a legacy procedural texture datablock.

    Modifier order matters: SUBSURF first (adds vertices), then DISPLACE acts on
    the denser evaluated geometry. This is how the same base mesh accepts any
    surface texture without re-meshing.
    """
    import bpy
    sub = obj.modifiers.new(name="PreSubsurf", type="SUBSURF")
    sub.levels = surf.subdivide
    sub.render_levels = surf.subdivide

    tex = bpy.data.textures.new(name=f"disp_{obj.name}", type=surf.texture)
    # Set common params defensively — not every texture type has every attr.
    for attr, val in (("noise_scale", surf.noise_scale),
                      ("turbulence", surf.turbulence),
                      ("noise_basis", "BLENDER_ORIGINAL")):
        if hasattr(tex, attr):
            try:
                setattr(tex, attr, val)
            except Exception:
                pass

    disp = obj.modifiers.new(name="Displace", type="DISPLACE")
    disp.texture = tex
    disp.strength = surf.strength
    disp.mid_level = 0.5
    disp.texture_coords = "LOCAL"


def _setup_world(light: LightRig):
    import bpy
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputWorld")
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = light.strength
    links.new(bg.outputs["Background"], out.inputs["Surface"])

    if light.preset == "studio":
        # bright gradient sky -> studio highlights on glossy/glass
        _studio_gradient(nodes, links, bg)
    elif light.preset == "underwater":
        # blue-green gradient water (NO world volume — infinite volume renders
        # black; bounded haze should be a box layer instead, added per-scene).
        _water_gradient(nodes, links, bg, strength=max(light.strength, 0.6))
    else:
        bg.inputs["Color"].default_value = (*light.background, 1.0)


def _studio_gradient(nodes, links, bg):
    tex_coord = nodes.new("ShaderNodeTexCoord")
    grad = nodes.new("ShaderNodeTexGradient")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    comb = nodes.new("ShaderNodeCombineXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.90, 0.92, 0.95, 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    mid = ramp.color_ramp.elements.new(0.75)
    mid.color = (2.2, 2.2, 2.2, 1.0)
    links.new(tex_coord.outputs["Generated"], sep.inputs["Vector"])
    links.new(sep.outputs["Z"], comb.inputs["X"])
    links.new(comb.outputs["Vector"], grad.inputs["Vector"])
    links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bg.inputs["Color"])


def _water_gradient(nodes, links, bg, strength=1.0):
    """Vertical blue-green gradient: brighter (sunlit) top, deep teal bottom."""
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    grad = nodes.new("ShaderNodeTexGradient")
    comb = nodes.new("ShaderNodeCombineXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.01, 0.08, 0.12, 1.0)   # deep
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.20, 0.55, 0.62, 1.0)   # sunlit
    links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    links.new(sep.outputs["Z"], comb.inputs["X"])
    links.new(comb.outputs["Vector"], grad.inputs["Vector"])
    links.new(grad.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength


def _lookat_quat(loc, target, track="-Z", up="Y"):
    from mathutils import Vector
    return Vector(np.asarray(target) - np.asarray(loc)).normalized().to_track_quat(track, up)


def _setup_lights(anchor: trimesh.Trimesh, light: LightRig):
    import bpy
    bounds = anchor.bounds
    radius = float(np.linalg.norm(bounds[1] - bounds[0]) / 2)
    center = anchor.centroid

    presets = {
        "studio":   [("Key",  (2.0, -1.5, 1.5), 1500, 1.5),
                     ("Rim",  (-2.0, 1.0, 0.5), 1000, 2.0),
                     ("Fill", (0.0, -2.5, -0.5), 350, 2.5)],
        "reef":     [("Key",  (-1.5, -1.5, 2.0), 900, 2.0),
                     ("Fill", (1.5, 0.5, 0.0), 150, 2.5)],
        "dramatic": [("Key",  (2.2, -1.0, 1.2), 1800, 1.0),
                     ("Rim",  (-1.5, 1.5, 1.0), 1400, 1.2)],
        # strong top light = sun through water surface (drives god-rays + tip SSS)
        "underwater": [("Sun",  (0.3, -0.4, 3.0), 2200, 2.5),
                       ("Fill", (-1.5, -1.0, 0.5), 250, 3.0)],
    }
    for name, off, energy, sizef in presets.get(light.preset, presets["studio"]):
        ld = bpy.data.lights.new(name=name, type="AREA")
        ld.energy = energy
        ld.size = radius * sizef
        o = bpy.data.objects.new(name, ld)
        o.location = center + radius * np.array(off)
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = _lookat_quat(o.location, center)
        bpy.context.collection.objects.link(o)


def _setup_camera(anchor: trimesh.Trimesh, cam: CameraRig):
    import bpy
    bounds = anchor.bounds
    radius = float(np.linalg.norm(bounds[1] - bounds[0]) / 2)
    center = anchor.centroid

    az, el = np.deg2rad(cam.azim_deg), np.deg2rad(cam.elev_deg)
    dist = radius * cam.distance_factor
    loc = center + dist * np.array([np.cos(el) * np.cos(az),
                                    np.cos(el) * np.sin(az),
                                    np.sin(el)])
    cd = bpy.data.cameras.new("Camera")
    cd.lens = cam.lens_mm
    if cam.dof:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = cam.fstop
        # focus on the near surface of the subject
        cd.dof.focus_distance = (dist - radius * cam.focus_factor)
    co = bpy.data.objects.new("Camera", cd)
    co.location = loc
    co.rotation_mode = "QUATERNION"
    co.rotation_quaternion = _lookat_quat(loc, center)
    bpy.context.collection.objects.link(co)
    bpy.context.scene.camera = co


def _setup_render(scene: Scene, out_path: Path, preview: bool = False):
    import bpy
    s = bpy.context.scene
    if preview:
        # EEVEE: rasterizer, ~seconds. Glass/SSS are faked, but form / light /
        # composition read fine for fast iteration before a final Cycles pass.
        s.render.engine = "BLENDER_EEVEE"
        try:
            s.eevee.taa_render_samples = max(16, scene.samples // 4)
        except Exception:
            pass
        res = (max(1, scene.resolution[0] // 2), max(1, scene.resolution[1] // 2))
        s.render.resolution_x, s.render.resolution_y = res
    else:
        s.render.engine = "CYCLES"
        try:
            s.cycles.device = "GPU"
        except Exception:
            s.cycles.device = "CPU"
        s.cycles.samples = scene.samples
        s.cycles.use_denoising = scene.use_denoise
        s.cycles.transparent_max_bounces = 16
        s.cycles.volume_max_steps = 64
        s.render.resolution_x, s.render.resolution_y = scene.resolution
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    # 'Standard' preserves saturated emission (DTI colors); AgX/Filmic desaturate.
    try:
        s.view_settings.view_transform = "Standard"
    except Exception:
        pass
    s.render.filepath = str(out_path.resolve())
