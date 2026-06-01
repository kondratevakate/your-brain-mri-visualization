"""Fetch large data assets (tracts, optional brains) on demand.

Keeps heavy binaries out of git history. Public tractography comes from DIPY's
bundled datasets; subject brains are expected via Git LFS or a Release/Zenodo URL.

Usage:
    python scripts/fetch_data.py --tracts
    python scripts/fetch_data.py --all
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def fetch_tracts() -> None:
    """Download public DIPY bundles (arcuate/CST/CC) and export compact .trk."""
    try:
        from dipy.data import read_bundles_2_subjects, fetch_bundles_2_subjects
        import nibabel as nib
        from nibabel.streamlines import Tractogram
    except ImportError:
        sys.exit("dipy + nibabel required:  pip install dipy nibabel")

    fetch_bundles_2_subjects()
    out = DATA / "tracts" / "hcp"
    out.mkdir(parents=True, exist_ok=True)
    dix = read_bundles_2_subjects(subj_id="subj_1", metrics=["t1"],
                                  bundles=["af.left", "cst.right", "cc_1"])
    for name in ("af.left", "cst.right", "cc_1"):
        sl = list(dix[name])
        trk = out / f"{name.replace('.', '_')}.trk"
        nib.streamlines.save(Tractogram(sl, affine_to_rasmm="same"), str(trk))
        print(f"  wrote {trk}  ({len(sl)} streamlines)")
    print(f"tracts ready in {out}")


def fetch_brains() -> None:
    """Placeholder: subject brains arrive via Git LFS or a Release/Zenodo URL."""
    print("Subject brains are distributed via Git LFS (data/brains/...) or a "
          "GitHub Release / Zenodo DOI. Run `git lfs pull` after cloning, or "
          "see data/README.md for the download link.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tracts", action="store_true", help="download public tracts")
    ap.add_argument("--brains", action="store_true", help="info on subject brains")
    ap.add_argument("--all", action="store_true", help="everything")
    args = ap.parse_args()
    if not any([args.tracts, args.brains, args.all]):
        ap.print_help()
        return
    if args.tracts or args.all:
        fetch_tracts()
    if args.brains or args.all:
        fetch_brains()


if __name__ == "__main__":
    main()
