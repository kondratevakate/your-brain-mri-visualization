# your-brain-mri-visualization

Turn your own brain MRI into 3D models you can spin around in **Blender**.
Run a FreeSurfer (or FastSurfer) segmentation, export the structures you care
about as `.stl` meshes, and render them.

![viz](https://github.com/kondratevakate/your-brain-mri-visualization/blob/master/viz/aseg_nd_aparc.png)

> **Privacy first.** Everything here is *surface meshes* (cortex + deep
> structures) — no skin, skull, or facial features, so nothing is
> face-reconstructable. Do **not** commit raw T1 volumes: a whole-head T1 can be
> used to reconstruct a face. If you ever publish raw volumes, deface them first
> (`mri_deface` / `pydeface`).

## What you get

| Folder | Contents |
|---|---|
| `my-brain-models/` | Example meshes: cortical lobes (`aparc/`), deep structures (`subcortical/`), and a merged `subcortical.stl`. |
| `my-brain-models/kate_3scanners_2026/` | Demo for *"my brain, 3 scanners, 6 years"* (MIDL 2026): the same brain segmented from a GE 3T, a Siemens 1.5T, and a Philips 1.5T scan — overlay the three in Blender to see how deep structures shift across scanners. |
| `tutorials/` | `saving-brain-regions.ipynb` (label → mesh walkthrough) and `freesurfer_stats_to_csv.py` (pull volumes out of `aseg.stats`). |
| `viz/` | Rendered example image. |
| `save_nii_named.sh`, `stl_files_creation.sh` | The two pipeline scripts (below). |

## Pipeline (recon → STL → Blender)

**0. Segment** your T1 with FreeSurfer or FastSurfer (resolution/contrast-agnostic
option: `mri_synthseg --i T1.nii.gz --o seg.nii.gz --robust`).

**1. Name & convert** the recon outputs to NIfTI:
```bash
bash save_nii_named.sh /path/to/SUBJECTS_DIR
```
This finds each subject's `norm.mgz` / `aparc+aseg.mgz` and writes
`<dir>_<subject>_norm.nii.gz` and `..._aparc+aseg.nii.gz`.

**2. Binarize** the label(s) you want (one structure or a group), e.g. subcortical:
```bash
mri_binarize --i aparc+aseg.nii.gz \
  --match 17 53 18 54 10 49 11 50 12 51 13 52 \
  --o subcortical_bin.nii.gz   # hippo, amygdala, thalamus, caudate, putamen, pallidum
```

**3. Mesh** each binarized volume to `.stl`:
```bash
bash stl_files_creation.sh /path/to/folder_of_bin_niftis
# (mri_tessellate + mris_convert under the hood)
```
For cortical surfaces, skip binarization and convert the recon surface directly:
```bash
mris_convert lh.pial lh.pial.stl
```

**4. Render** in Blender: `File → Import → STL`, drop in the meshes, assign
materials, done. Overlay multiple scanners/sessions to compare.

## Requirements
- **FreeSurfer 7.4+** (or FastSurfer) for recon + `mri_binarize` / `mri_tessellate` / `mris_convert`.
- **Blender 3.x+** for rendering (the STL importer is built in).
- A FreeSurfer license for the recon step (free: https://surfer.nmr.mgh.harvard.edu/registration.html).

## Label reference
Subcortical FreeSurfer label IDs used above: hippocampus 17/53, amygdala 18/54,
thalamus 10/49, caudate 11/50, putamen 12/51, pallidum 13/52. Full list:
`$FREESURFER_HOME/FreeSurferColorLUT.txt`.
