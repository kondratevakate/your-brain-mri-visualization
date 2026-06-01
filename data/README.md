# Data

Large assets are **not** baked into git history. They are either tracked with
**Git LFS** (`.gitattributes`) or fetched on demand by `scripts/fetch_data.py`.

## Layout

```
data/
├── brains/                 # subject brains as LABEL volumes or meshes (LFS)
│   └── kondratevakate/
│       ├── aparc+aseg.nii.gz      # FreeSurfer parcellation (no face data)
│       └── meshes/*.stl           # optional pre-built surfaces
└── tracts/                 # tractography streamlines (LFS or fetched)
    └── hcp/*.trk
```

> A canonical sample (`example_data/aparc+aseg.nii.gz`) ships in plain git so the
> pipeline runs out of the box without any download.

## Get the data

```bash
python scripts/fetch_data.py --tracts        # download public HCP-style bundles
python scripts/fetch_data.py --all
```

The author's brain and HCP tracts are distributed as **compressed** assets:
- **meshes** → `.stl` / `.ply` via Git LFS, or attached to a GitHub Release / Zenodo DOI
- **tracts** → `.trk` via Git LFS (binary, already compact), fetched by the script

## Privacy (read before adding a brain)

- **NEVER commit a raw whole-head T1** — it can be used to reconstruct a face.
  Deface first (`mri_deface` / `pydeface`), and prefer committing only **label
  volumes** (`aparc+aseg`) or **surface meshes**, which carry no facial geometry.
- Label volumes and cortical/subcortical meshes are safe to share.
- See the repository root `README.md` "Privacy first" note.
