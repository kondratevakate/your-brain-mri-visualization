# your-brain-mri-visualization

Turn your own brain MRI into 3D-printable / render-ready models you can spin
around in **Blender**. Run a FreeSurfer (or FastSurfer / SynthSeg) segmentation,
export the structures you care about as `.stl` meshes, and render them.

![viz](https://github.com/kondratevakate/your-brain-mri-visualization/blob/master/viz/aseg_nd_aparc.png)

> **Privacy first.** Everything here is *surface meshes* (cortex + deep
> structures) — no skin, skull, or facial features, so nothing is
> face-reconstructable. Do **not** commit raw T1 volumes: a whole-head T1 can be
> used to reconstruct a face. If you ever share raw volumes, deface them first
> (`mri_deface` / `pydeface`).

## Where the models live

Mesh binaries (`.stl`) are **not stored in git** — they bloat the history and git
packs them poorly. Download the ready-made example meshes from the
[**Releases**](https://github.com/kondratevakate/your-brain-mri-visualization/releases)
page, or generate your own with the pipeline below. The repo keeps only the
scripts, a small label volume, the tutorial, and the render.

## Pipeline (recon → STL → Blender)

**0. Segment** your T1 with FreeSurfer or FastSurfer. Contrast/resolution-agnostic
option (works on non-1mm, non-MPRAGE scans too):
```bash
mri_synthseg --i T1.nii.gz --o seg.nii.gz --robust
```

**1. Name & convert** recon outputs to NIfTI:
```bash
bash save_nii_named.sh /path/to/SUBJECTS_DIR
```

**2. Binarize** the label(s) you want — e.g. the subcortical group:
```bash
mri_binarize --i aparc+aseg.nii.gz \
  --match 17 53 18 54 10 49 11 50 12 51 13 52 \
  --o subcortical_bin.nii.gz   # hippo, amygdala, thalamus, caudate, putamen, pallidum
```

**3. Mesh** each binarized volume to `.stl`:
```bash
bash stl_files_creation.sh /path/to/folder_of_bin_niftis   # mri_tessellate + mris_convert
mris_convert lh.pial lh.pial.stl                           # cortical surface (no binarize)
```

**4. Render** in Blender: `File → Import → STL`, assign materials, done. Overlay
several scanners / sessions to compare how the same structures move.

## Requirements
- **FreeSurfer 7.4+** (or **FastSurfer**) — recon + `mri_binarize` / `mri_tessellate` / `mris_convert`.
- **Blender 3.x+** — STL importer is built in.
- A FreeSurfer license for the recon step (free: https://surfer.nmr.mgh.harvard.edu/registration.html).

## Label reference
Subcortical FreeSurfer label IDs: hippocampus 17/53, amygdala 18/54, thalamus
10/49, caudate 11/50, putamen 12/51, pallidum 13/52. Full list:
`$FREESURFER_HOME/FreeSurferColorLUT.txt`.

## Example: one brain, three scanners (MIDL 2026)
The Releases include a `kate-3scanners-2026` set: the *same* brain segmented from a
GE 3T, a Siemens 1.5T, and a Philips 1.5T scan — overlay the three subcortical
meshes in Blender to see scanner-driven differences (companion to *Benchmarking
the Reproducibility of Brain Tissue Segmentation Across MRI Scanners*).

---

**Keywords / tags:** brain MRI visualization · FreeSurfer · FastSurfer · SynthSeg
· brain segmentation · subcortical structures · cortical surface · STL · Blender
· 3D brain model · 3D printing brain · neuroimaging · medical imaging · NIfTI ·
aseg · aparc · T1-weighted MRI · neuroscience · reproducibility
`#neuroimaging #brainMRI #freesurfer #fastsurfer #synthseg #blender #3dbrain #STL #medicalimaging`
