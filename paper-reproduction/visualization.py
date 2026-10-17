"""
visualization.py — drawing only. Reads result dictionaries (from engine.results()
or the saved .npz files); never changes the simulation.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

# Colours: categorical slots 1-2 of the reference palette; neutral inks for text/reference
RIPPLE, SWARM = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
MODE_COLOR = {"rippling": RIPPLE, "swarming": SWARM}

# Paper values to compare against [Saulnier et al. 2026, Fig. 3e]
PAPER_QUARTILES = {"rippling": [0.092, 0.155, 0.247, 0.505], "swarming": [0.114, 0.181, 0.269, 0.436]}
PAPER_SIM_QUARTILES = {"rippling": [0.03, 0.04, 0.17, 0.75], "swarming": [0.02, 0.07, 0.31, 0.57]}  # ≈ Fig. 5d,h
PAPER_MEAN_TBR = {"rippling": (3.21, 5.02), "swarming": (3.73, 3.27)}   # (experiment, paper's simulation)

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
})


def draw_cells(ax, nodes, box, color):
    """Each cell as a 0.7 µm-thick line through its discs, wrapped into the periodic box."""
    pts = np.mod(nodes, box)
    seg = np.stack([pts[:, :-1], pts[:, 1:]], axis=2).reshape(-1, 2, 2)
    seg = seg[np.linalg.norm(seg[:, 0] - seg[:, 1], axis=1) < 1.0]      # drop box-edge jumps
    ax.set_xlim(0, box); ax.set_ylim(0, box); ax.set_aspect("equal")
    width_pts = ax.get_window_extent().width * 72 / ax.figure.dpi / box * 0.7
    ax.add_collection(LineCollection(seg, colors=color, linewidths=width_pts, capstyle="round"))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True); s.set_color(GRID)


def tbr_peaks(tbr, width=1 / 3, top=15.0):
    """Histogram peaks of the TBR distribution: one peak = unimodal, two = bimodal."""
    from scipy.signal import find_peaks
    from scipy.ndimage import gaussian_filter1d
    h, e = np.histogram(tbr, bins=np.arange(0, top + width, width), density=True)
    smooth = gaussian_filter1d(h, 1.0)
    idx, _ = find_peaks(smooth, prominence=0.04 * smooth.max())
    return 0.5 * (e[idx] + e[idx + 1])


def plot_tbr(ax, tbr, color, title, ref=None, mode=None):
    bins = np.arange(0, 15 + 1 / 3, 1 / 3)
    ax.hist(tbr, bins=bins, density=True, color=color, alpha=0.85, label=f"this model (mean {tbr.mean():.2f} min)")
    if ref is not None and len(ref):
        ax.hist(ref, bins=bins, density=True, histtype="step", color=INK, linewidth=1.5,
                label=f"authors' code (mean {ref.mean():.2f} min)")
    ax.set_title(title, loc="left", fontsize=10, color=INK)
    if mode in PAPER_MEAN_TBR:
        exp, sim = PAPER_MEAN_TBR[mode]
        ax.text(0.98, 0.62, f"paper: simulation {sim:.2f} min\nexperiment {exp:.2f} min",
                transform=ax.transAxes, ha="right", fontsize=7.5, color=INK2)
    ax.set_xlabel("time between reversals (min)")
    ax.set_ylabel("density")
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)


def plot_order(ax, results):
    for mode, r in results.items():
        ax.plot(r["order_r"], r["order"], color=MODE_COLOR[mode], linewidth=2, label=mode)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("distance (µm)")
    ax.set_ylabel("nematic order O(r)")
    ax.set_title("Alignment vs distance", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(color=GRID, linewidth=0.6)


def plot_quartiles(ax, mode, quartiles):
    """This model vs the paper's simulation (Fig. 5d,h) vs the paper's experiment (Fig. 3e)."""
    labels = ["<25%", "25–50%", "50–75%", ">75%"]
    x, w, c = np.arange(4), 0.27, MODE_COLOR[mode]
    ax.bar(x - w, quartiles, w * 0.9, color=c, label="this model")
    ax.bar(x, PAPER_SIM_QUARTILES[mode], w * 0.9, color=c, alpha=0.4, label="paper sim (≈ Fig. 5)")
    ax.bar(x + w, PAPER_QUARTILES[mode], w * 0.9, color="none", edgecolor=c, linewidth=1.3,
           hatch="////", label="paper experiment")
    ax.axhline(0.25, color=INK2, linewidth=0.8, linestyle="--")
    ax.text(-0.45, 0.265, "25% = no link", fontsize=7.5, color=INK2)
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("cell's own frustration quartile at reversal")
    ax.set_ylabel("fraction of reversals")
    ax.set_title(f"{mode.capitalize()}: reversals vs frustration", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.grid(axis="y", color=GRID, linewidth=0.6)


def plot_frustration(ax, results):
    """Distribution of the smoothed frustration (s × 2, back on the 0–2 scale)."""
    bins = np.linspace(0, 0.8, 61)
    for mode, r in results.items():
        f = 2 * r["signal_samples"].ravel()
        ax.hist(f, bins=bins, density=True, histtype="step", linewidth=1.8, color=MODE_COLOR[mode],
                label=f"{mode} (median {np.median(f):.2f})")
    ax.set_xlabel("smoothed frustration f")
    ax.set_ylabel("density")
    ax.set_title("Frustration experienced", loc="left", fontsize=10, color=INK)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)


def plot_kymograph(ax, kymo, box, minutes=30):
    minutes = min(minutes, len(kymo) * 0.1)
    rows = int(round(minutes / 0.1))
    data = kymo[-rows:]
    ax.imshow(data, aspect="auto", cmap="Blues", origin="upper",
              extent=[0, box, minutes, 0], interpolation="nearest")
    ax.set_xlabel("position along the rippling axis (µm)")
    ax.set_ylabel(f"time (min, last {minutes})")
    ax.set_title("Kymograph: counter-propagating waves", loc="left", fontsize=10, color=INK)


def validation_figure(results, refs, path):
    fig = plt.figure(figsize=(11, 10.5), dpi=130)
    gs = fig.add_gridspec(3, 3, height_ratios=[1.15, 1, 1], hspace=0.45, wspace=0.32)
    if "rippling" in results:
        ax = fig.add_subplot(gs[0, 0]); draw_cells(ax, results["rippling"]["final_nodes"], results["rippling"]["box"], RIPPLE)
        ax.set_title("Rippling, final frame", loc="left", fontsize=10, color=INK)
        plot_kymograph(fig.add_subplot(gs[0, 1]), results["rippling"]["kymo"], results["rippling"]["box"])
    if "swarming" in results:
        ax = fig.add_subplot(gs[0, 2]); draw_cells(ax, results["swarming"]["final_nodes"], results["swarming"]["box"], SWARM)
        ax.set_title("Swarming, final frame", loc="left", fontsize=10, color=INK)
    for col, mode in enumerate(["rippling", "swarming"]):
        if mode in results:
            plot_tbr(fig.add_subplot(gs[1, col]), results[mode]["tbr"], MODE_COLOR[mode],
                     f"{mode.capitalize()} TBR (last 50 min)", refs.get(mode), mode)
            plot_quartiles(fig.add_subplot(gs[2, col]), mode, results[mode]["quartiles"])
    plot_order(fig.add_subplot(gs[1, 2]), results)
    plot_frustration(fig.add_subplot(gs[2, 2]), results)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
