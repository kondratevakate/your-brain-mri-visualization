"""Fill the PVS report template + render its charts/thumbnail.

    python -m contributions.reports.pvs.build

Replace DATA with your own perivascular-space quantification output.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent

DATA = {
    "report_title": "Perivascular Spaces (PVS) Report",
    "patient": "Demo Patient 1 (46, M)", "pid": "6698", "age": "45",
    "scan": "189140", "date": "May 26 2023", "branch": "Sample Clinic",
    "regions": [
        # name, volume cm3, score 0-4
        ("Summary", "Moderate", 2.0),
        ("Basal Ganglia", "0.1", 1.0),
        ("Centrum Semiovale", "1.48", 3.0),
    ],
    "r1": ("Basal Ganglia", "Perivascular space in the normal range for age",
           45, 0.30),     # age-frac, score-frac (0..1) of the dot
    "r2": ("Centrum Semiovale", "Perivascular space in the abnormal range for age",
           45, 0.72),
}
SCORE_COLORS = {0: "#2563eb", 1: "#3b82f6", 2: "#93c5fd", 3: "#f87171", 4: "#ef4444"}


def _score_row(name, vol, score):
    pct = score / 4 * 100
    color = SCORE_COLORS[round(score)]
    return (f"<tr><td class='region'>{name}</td><td class='vol'>{vol}</td>"
            f"<td><div class='slider'><div class='knob' style='left:{pct}%;"
            f"background:{color}'>{score:g}</div></div></td></tr>")


def _range_plot(path, note_abnormal):
    fig, ax = plt.subplots(figsize=(3.4, 2.2), dpi=120)
    ax.axhspan(0.5, 1.0, color="#fdd", zorder=0)   # abnormal band
    ax.axhspan(0.0, 0.5, color="#dde6ff", zorder=0)  # normal band
    y = 0.72 if note_abnormal else 0.30
    ax.scatter([0.5], [y], color="#c0392b" if note_abnormal else "#2563eb",
               s=60, zorder=3)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([0, 0.5, 1]); ax.set_xticklabels(["34", "Age", "56"], fontsize=8)
    ax.set_yticks([0.25, 0.75]); ax.set_yticklabels(["0-20\nNormal", "20-40\nAbn"],
                                                    fontsize=7)
    fig.tight_layout(); fig.savefig(path, facecolor="white"); plt.close(fig)


def _surfaces_placeholder(path):
    fig, ax = plt.subplots(figsize=(5, 2.2), dpi=120)
    ax.text(0.5, 0.5, "3D PVS surfaces\n(render via rendering.scene:\n"
            "glass shell + emission PVS + ventricles)", ha="center",
            va="center", fontsize=10, color="#555")
    ax.axis("off"); fig.savefig(path, facecolor="white"); plt.close(fig)


def _slice_strip(path):
    import numpy as np
    fig, axes = plt.subplots(1, 10, figsize=(10, 1.1), dpi=110)
    rng = np.random.default_rng(0)
    for a in axes:
        a.imshow(rng.random((40, 40)), cmap="gray"); a.axis("off")
    fig.tight_layout(pad=0.1); fig.savefig(path, facecolor="black"); plt.close(fig)


def build():
    rows = "\n".join(_score_row(*r) for r in DATA["regions"])
    _slice_strip(HERE / "slices.png")
    _surfaces_placeholder(HERE / "surfaces.png")
    _range_plot(HERE / "r1.png", note_abnormal=False)
    _range_plot(HERE / "r2.png", note_abnormal=True)

    t = (HERE / "template.html").read_text(encoding="utf-8")
    repl = {
        "REPORT_TITLE": DATA["report_title"], "PATIENT": DATA["patient"],
        "PID": DATA["pid"], "AGE": DATA["age"], "SCAN": DATA["scan"],
        "DATE": DATA["date"], "BRANCH": DATA["branch"], "ROWS": rows,
        "SLICE_STRIP": "slices.png", "SURFACES": "surfaces.png",
        "R1_NAME": DATA["r1"][0], "R1_NOTE": DATA["r1"][1], "R1_PLOT": "r1.png",
        "R2_NAME": DATA["r2"][0], "R2_NOTE": DATA["r2"][1], "R2_PLOT": "r2.png",
    }
    for k, v in repl.items():
        t = t.replace(f"%%{k}%%", str(v))
    (HERE / "pvs_report.html").write_text(t, encoding="utf-8")

    # gallery thumbnail = the abnormal range chart
    _range_plot(HERE / "thumbnail.png", note_abnormal=True)
    print("wrote pvs_report.html + assets + thumbnail.png")


if __name__ == "__main__":
    build()
