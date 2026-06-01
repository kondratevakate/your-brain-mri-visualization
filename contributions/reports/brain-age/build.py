"""Fill the brain-age report template with data and render a thumbnail.

    python -m contributions.reports.brain-age.build

Edit DATA (or load from your own pipeline) to produce a real report. The output
is a self-contained HTML you can open or print to PDF.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent

# --- report data (replace with your real metrics) --------------------------
DATA = {
    "complete": "100%",
    "delta": "11.0",
    "direction": "younger",        # younger | older
    "rec_text": "We've put together a few recommendations to help you improve "
                "your brain function",
    "neuro": 40.6, "blood": 47.0, "mri": 57.0, "gen": 17.0,
    "brain_img": "thumbnail_brain.png",
    "brain_age": 51.46,
}
MAX_AGE = 70.0   # bar scale for the green metrics


def fill_html():
    t = (HERE / "template.html").read_text(encoding="utf-8")
    age_int, age_dec = f"{DATA['brain_age']:.2f}".split(".")
    repl = {
        "COMPLETE": DATA["complete"],
        "DELTA": DATA["delta"], "DIRECTION": DATA["direction"],
        "REC_TEXT": DATA["rec_text"], "BRAIN_IMG": DATA["brain_img"],
        "NEURO": f"{DATA['neuro']:.1f}", "BLOOD": f"{DATA['blood']:.1f}",
        "MRI": f"{DATA['mri']:.1f}", "GEN": f"{DATA['gen']:.1f}",
        "W_NEURO": f"{DATA['neuro']/MAX_AGE*100:.0f}",
        "W_BLOOD": f"{DATA['blood']/MAX_AGE*100:.0f}",
        "W_MRI": f"{DATA['mri']/MAX_AGE*100:.0f}",
        "W_GEN": f"{DATA['gen']:.0f}",
        "AGE_INT": age_int, "AGE_DEC": age_dec,
    }
    for k, v in repl.items():
        t = t.replace(f"%%{k}%%", str(v))
    (HERE / "brain_age_report.html").write_text(t, encoding="utf-8")


def thumbnail():
    labels = ["NeuroGames", "Blood", "Brain MRI", "Genetic %"]
    vals = [DATA["neuro"], DATA["blood"], DATA["mri"], DATA["gen"]]
    colors = ["#26431f", "#26431f", "#26431f", "#e91e63"]
    fig, ax = plt.subplots(figsize=(4, 2.4), dpi=120)
    ax.barh(labels[::-1], vals[::-1], color=colors[::-1])
    ax.set_title(f"Brain age: {DATA['brain_age']:.1f} yrs "
                 f"({DATA['delta']} {DATA['direction']})", fontsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(HERE / "thumbnail.png", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    fill_html()
    thumbnail()
    print("wrote brain_age_report.html + thumbnail.png")
