# Rendering toolkit

Code-driven, **composable** brain rendering. A render is a composition of four
orthogonal axes — so the same brain serves many purposes by recombining them.

```python
from rendering.mesh_prep import label_to_mesh, center_to_origin
from rendering.presets import glass_frosted
from rendering.scene import render_scene

shell = label_to_mesh("example_data/aparc+aseg.nii.gz",
                      list(range(1000, 3000)), envelope=True)
(shell,) = center_to_origin(shell)
render_scene(glass_frosted(shell), "out.png", preview=True)  # fast EEVEE
render_scene(glass_frosted(shell), "out.png")                # final Cycles
```

## The axes

| Axis | Where | Options |
|---|---|---|
| **Form** | `mesh_prep`, `forms/quills`, `forms/tentacles` | envelope / detail mesh, pins, tentacles |
| **Material** | `scene.Material` | `glass`, `sss`, `stone`, `emission`, `tract` |
| **Surface** | `scene.Surface` | `WOOD`/`STUCCI`/`MUSGRAVE`/`VORONOI` displacement |
| **Light** | `scene.LightRig` | `studio`, `reef`, `dramatic`, `underwater` |
| **Camera** | `scene.CameraRig` | angle, distance, lens, depth-of-field |

`Scene(layers=[Layer(mesh, material, surface)], light, camera)` → `render_scene`.

## Presets (`presets.py`)
`glass_clear` · `glass_frosted` · `pin_brain` · `dti` · `anemone` · `atlas`

## Animation (`animate.py`)
Turntable + **inertial whip physics** (a damped oscillator driven by the body's
angular acceleration → hair-like lag/overshoot). Profiles: `whip_schedule`
(gentle turn) and `shake_schedule` (dog-shake). Seamless loops by phase-matching.
`build_whip_pins` bends pins (root planted, tip lags) for true secondary motion.

## Examples (`examples/`)
| # | File | Shows |
|---|---|---|
| 01–02 | `*_wireframe_*` | wireframe + ROI (precentral, hippocampus, amygdala) |
| 03 | `03_glass_frosted_blue` | frosted blue glass |
| 05 | `05_glass_clear_cutglass` | clear cut glass |
| 07 | `07_glass_shell_internal_nuclei` | glass + glowing internal nuclei |
| 08/10 | `*_pins_*` | radial pin field (sea-urchin / coral) |
| 09/11 | `*_tracts*` | DTI tractography, direction-coloured |
| 13 | `13_glass_textured` | textured glass on dark |
| 14 | `14_pins_gif` | turntable + whip GIF |
| 15 | `15_anemone_underwater` | curled tentacles, underwater SSS |
| 16 | `16_furry_dogshake` | furry brain shaking off like a dog |

## Notes
- **No VTK** path for wireframe (matplotlib) — works where VTK DLLs are blocked.
- **Cycles** (`pip install bpy`) for glass/sss/pins/tracts; **EEVEE** `preview=True`
  for ~10× faster iteration (skips displacement/subdivision).
- Use `view_transform="Standard"` (handled in `scene.py`) for data colours (DTI);
  AgX/Filmic desaturate.
- Every render writes a reproducibility **sidecar `.json`**.
