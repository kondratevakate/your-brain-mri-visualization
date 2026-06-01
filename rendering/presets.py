"""Curated style presets — the UX layer over the raw Scene compositor.

Each preset bakes in the "good defaults" discovered through iteration, so a
caller supplies only geometry and gets a publication-ready Scene. Override any
field afterward (presets return a normal Scene dataclass).

    from rendering.presets import pin_brain
    scene = pin_brain(shell, pins, color=(0.78, 0.07, 0.09, 1.0))
    scene.samples = 128                      # tweak freely
    render_scene(scene, "out.png")
"""
from __future__ import annotations

import trimesh

from rendering.scene import (Scene, Layer, Material, Surface,
                             LightRig, CameraRig)


def glass_clear(shell: trimesh.Trimesh) -> Scene:
    return Scene(
        layers=[Layer(shell, Material(kind="glass", color=(0.96, 0.98, 1.0, 1.0),
                                      roughness=0.02, ior=1.5,
                                      absorption_color=(0.95, 0.97, 1.0),
                                      absorption_density=0.004),
                      subdivision=1, name="GlassCortex")],
        light=LightRig("studio", strength=1.4),
        camera=CameraRig(azim_deg=28, elev_deg=10, distance_factor=2.4),
        samples=128,
    )


def glass_frosted(shell: trimesh.Trimesh) -> Scene:
    return Scene(
        layers=[Layer(shell, Material(kind="glass", color=(0.88, 0.94, 1.0, 1.0),
                                      roughness=0.22, ior=1.45,
                                      absorption_color=(0.30, 0.55, 0.92),
                                      absorption_density=0.022),
                      surface=Surface("STUCCI", strength=1.3, subdivide=2),
                      name="GlassCortex")],
        light=LightRig("studio", strength=1.1),
        camera=CameraRig(azim_deg=28, elev_deg=10, distance_factor=2.4),
        samples=128,
    )


def pin_brain(shell, pins, color=(0.90, 0.90, 0.91, 1.0),
              bg=(0.72, 0.72, 0.74)) -> Scene:
    """Dense radial pin field (sea-urchin / coral aesthetic)."""
    return Scene(
        layers=[
            Layer(shell, Material(kind="stone", color=color, roughness=0.55),
                  name="Body"),
            Layer(pins, Material(kind="stone", color=color, roughness=0.34),
                  name="Pins"),
        ],
        light=LightRig("reef", strength=1.0, background=bg),
        camera=CameraRig(azim_deg=45, elev_deg=33, distance_factor=3.0),
        samples=64,
    )


def dti(tracts: trimesh.Trimesh, azim=90, elev=8) -> Scene:
    return Scene(
        layers=[Layer(tracts, Material(kind="tract", emission_strength=1.1),
                      name="Tracts")],
        light=LightRig("reef", strength=0.3, background=(0.01, 0.01, 0.02)),
        camera=CameraRig(azim_deg=azim, elev_deg=elev, distance_factor=2.2),
        samples=48,
    )


def anemone(floor, column, tentacles, color=(0.95, 0.58, 0.58, 1.0)) -> Scene:
    return Scene(
        layers=[
            Layer(floor, Material(kind="stone", color=(0.80, 0.72, 0.55, 1.0),
                                  roughness=0.95), name="Sand"),
            Layer(column, Material(kind="sss", color=color, sss_weight=1.0,
                                   sss_radius=(7.0, 3.0, 1.8), roughness=0.45),
                  name="Column"),
            Layer(tentacles, Material(kind="sss", color=color, sss_weight=1.0,
                                      sss_radius=(8.0, 3.5, 2.2), roughness=0.4),
                  name="Tentacles"),
        ],
        light=LightRig("underwater", strength=1.0),
        camera=CameraRig(azim_deg=35, elev_deg=7, distance_factor=2.6),
        samples=96,
    )


def atlas(shell, nuclei_layers: list[Layer]) -> Scene:
    """Glass cortex + caller-supplied colored internal-volume layers."""
    glass = Layer(shell, Material(kind="glass", color=(0.92, 0.95, 1.0, 1.0),
                                  roughness=0.05, ior=1.45,
                                  absorption_color=(0.85, 0.92, 1.0),
                                  absorption_density=0.004),
                  subdivision=1, name="Cortex")
    return Scene(
        layers=[glass, *nuclei_layers],
        light=LightRig("reef", strength=0.6, background=(0.02, 0.03, 0.05)),
        camera=CameraRig(azim_deg=25, elev_deg=10, distance_factor=2.3),
        samples=80,
    )
