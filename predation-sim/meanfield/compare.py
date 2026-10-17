"""
meanfield/compare.py — draw the average-world model against the full simulation for every run:
living E. coli and Myxo against bio-hours, one small panel per run.

Usage (from predation-sim/):  python meanfield/compare.py [out_name]
Uses meanfield/fitted.json; writes checks/output/<out_name>.png (default meanfield_vs_sim).
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                 # noqa: E402
import numpy as np                                              # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as mf                                              # noqa: E402
import runs as mr                                               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
INK = {"secondary": "#52514e", "muted": "#898781", "grid": "#e1e0d9", "surface": "#fcfcfb"}
COLOURS = {"E": "#e63ca0", "H": "#1f9d3a"}                     # the sim's own colours (B41)
NAMES = {"E": "E. coli", "H": "Myxo"}


def load_fitted():
    """The fitted numbers and which runs were held out."""
    with open(os.path.join(HERE, "fitted.json"), encoding="utf8") as fh:
        data = json.load(fh)
    return mf.Fitted(**data["fitted"]), set(data.get("held_out", []))


def panel(ax, run, fitted, held_out):
    """One run: the sim as thin lines, the model as dashed lines, on a log scale."""
    d = mr.load(run)
    out = mf.simulate(mf.world_for(run), fitted, hours=d["h"][-1])
    for key in ("E", "H"):
        ax.semilogy(d["h"], np.maximum(d[key], 1), color=COLOURS[key], lw=1.4)
        ax.semilogy(out["h"], np.maximum(out[key], 1), color=COLOURS[key], lw=1.4, ls=(0, (4, 2)))
    title = run.label + ("  (held out)" if run.name in held_out else "")
    ax.set_title(title, loc="left", fontsize=9, color=INK["secondary"])
    ax.set_facecolor(INK["surface"])
    ax.grid(True, color=INK["grid"], lw=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK["muted"], labelsize=8)
    ax.set_ylim(1, 5000)


def main():
    """Draw every available run in a grid and save the picture."""
    name = sys.argv[1] if len(sys.argv) > 1 else "meanfield_vs_sim"
    fitted, held_out = load_fitted()
    runs_ = mr.available()
    cols = 4
    rows = int(np.ceil(len(runs_) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(16, 3.6 * rows), dpi=100, squeeze=False)
    fig.patch.set_facecolor(INK["surface"])
    for ax, run in zip(axes.ravel(), runs_):
        panel(ax, run, fitted, held_out)
    for ax in axes.ravel()[len(runs_):]:
        ax.axis("off")
    handles = [plt.Line2D([], [], color=COLOURS[k], lw=1.4, label=NAMES[k]) for k in ("E", "H")]
    handles += [plt.Line2D([], [], color="0.4", lw=1.4, label="full simulation"),
                plt.Line2D([], [], color="0.4", lw=1.4, ls=(0, (4, 2)), label="average-world model")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=5, frameon=False)
    fig.supxlabel("biological time (h)", color=INK["secondary"], y=0.045)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    path = os.path.join(HERE, "..", "checks", "output", name + ".png")
    fig.savefig(path, facecolor=fig.get_facecolor())
    print("saved", os.path.normpath(path))


if __name__ == "__main__":
    main()
