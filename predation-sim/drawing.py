"""
drawing.py — draws the world onto a pygame Surface, shared by the live window and the recorded
video (build manual §5, milestone 7).

What is shown, back to front:
- the ground: cream where it's empty, light brown where nutrients are rich;
- prey remains (the matrix): a faint mauve tint, where Myxo can ripple;
- slime trails: grey;
- Myxo spores: pale green dots;
- E. coli: magenta rods (B41, the paper's mCherry prey); dormant cells darker, dead cells waiting to
  burst grey-pink;
- Myxo: green chains (the paper's GFP cells); brighter = fuller food store; scouts yellow-green;
  cells killing a prey outlined white;
- a scale bar, a short legend and a line of numbers.

A View picks what is drawn: the whole world, or a square close-up around a point (wrap-around safe).
"""
from dataclasses import dataclass

import numpy as np
import pygame

import geometry as geo
import myxo_modes
import state

GROUND_EMPTY = np.array([255, 250, 232])
GROUND_RICH = np.array([226, 168, 92])
MATRIX_TINT = np.array([196, 150, 214])
SLIME = (95, 95, 95)
ECOLI = (230, 60, 160)
ECOLI_DORMANT = (150, 35, 105)
ECOLI_DEAD = (190, 160, 178)
MYXO_DIM = np.array([25, 95, 40])
MYXO_BRIGHT = np.array([70, 225, 95])
SCOUT = (200, 235, 60)
SPORE_FILL, SPORE_EDGE = (205, 240, 165), (31, 157, 58)
TEXT, BAR = (255, 255, 255), (20, 20, 20, 170)


@dataclass
class View:
    """The part of the world a picture shows: the whole box, or a square `span` µm wide around
    `centre`; drawn `size` pixels wide."""
    box: float
    size: int
    centre: tuple = None
    span: float = None

    @property
    def width(self):
        """µm across the picture."""
        return self.box if self.centre is None else self.span

    @property
    def scale(self):
        """Pixels per µm."""
        return self.size / self.width

    def to_screen(self, points):
        """µm → pixels: x to the right, y up the screen (the world's y axis points up)."""
        if self.centre is None:
            pts = np.mod(points, self.box)
        else:
            pts = geo.min_image(points - np.asarray(self.centre), self.box) + self.span / 2
        pts = pts * self.scale
        return np.stack([pts[..., 0], self.size - pts[..., 1]], axis=-1)

    def crop(self, grid, spacing):
        """The part of a wrap-around ground map inside the view."""
        if self.centre is None:
            return grid
        n = grid.shape[0]
        c = np.asarray(self.centre) / spacing
        g = np.roll(grid, (int(round(n / 2 - c[0])), int(round(n / 2 - c[1]))), axis=(0, 1))
        half = int(round(self.span / 2 / spacing))
        return g[n // 2 - half:n // 2 + half, n // 2 - half:n // 2 + half]


def grid_surface(rgb, alpha=None):
    """A map (x first, y up) as a pygame Surface, flipped so y points up the screen."""
    rgb = np.ascontiguousarray(rgb[:, ::-1].astype(np.uint8))
    if alpha is None:
        return pygame.surfarray.make_surface(rgb)
    surf = pygame.Surface(rgb.shape[:2], pygame.SRCALPHA)
    pygame.surfarray.blit_array(surf, rgb)
    pygame.surfarray.pixels_alpha(surf)[:] = np.ascontiguousarray(alpha[:, ::-1].astype(np.uint8))
    return surf


def draw_background(surf, world, view):
    """Ground nutrients with prey remains tinted on top, then the slime trails."""
    s, f = world.settings, world.fields
    rich = np.clip(view.crop(f.nutrients, f.spacing), 0.0, 1.0)[..., None]
    rgb = GROUND_EMPTY + (GROUND_RICH - GROUND_EMPTY) * rich
    tint = np.clip(view.crop(f.matrix, f.spacing) / s.matrix_ripple_threshold, 0.0, 1.0)[..., None] * 0.55
    rgb = rgb + (MATRIX_TINT - rgb) * tint
    surf.blit(pygame.transform.smoothscale(grid_surface(rgb), (view.size, view.size)), (0, 0))
    slime = np.clip(view.crop(f.eps + f.eps_scout, f.eps_spacing) / 0.5, 0.0, 1.0)
    rgb_slime = np.broadcast_to(np.array(SLIME), slime.shape + (3,))
    layer = grid_surface(rgb_slime, alpha=150 * slime)
    surf.blit(pygame.transform.smoothscale(layer, (view.size, view.size)), (0, 0))


def crosses_edge(a, b, view):
    """True where a segment joins two points on opposite sides of the wrap-around edge."""
    return np.abs(a - b).max(axis=-1) > view.box / 2 * view.scale


def draw_rod(surf, colour, p0, p1, width):
    """A thick line with round ends."""
    pygame.draw.line(surf, colour, p0, p1, width)
    if width >= 3:
        pygame.draw.circle(surf, colour, p0, width / 2)
        pygame.draw.circle(surf, colour, p1, width / 2)


def draw_ecoli(surf, world, view):
    """Each rod as a thick line, as wide as the cell (1 µm), coloured by its state."""
    s, e = world.settings, world.ecoli
    if state.count(e) == 0:
        return
    ends = view.to_screen(geo.rod_points(e.centre, e.angle, e.length, 2, s.ecoli_width))
    width = max(1, int(round(s.ecoli_width * view.scale)))
    dead = e.lysis_timer >= 0
    colours = np.where(dead[:, None], ECOLI_DEAD, np.where(e.dormant[:, None], ECOLI_DORMANT, ECOLI))
    keep = ~crosses_edge(ends[:, 0], ends[:, 1], view)
    for (p0, p1), c in zip(ends[keep], colours[keep]):
        draw_rod(surf, tuple(int(v) for v in c), p0, p1, width)


def myxo_colours(world):
    """Green, brighter with a fuller store (100 = a newborn, 200 = ready to divide); scouts
    yellow-green."""
    m = world.myxo
    full = np.clip(m.energy / 200.0, 0.0, 1.0)[:, None]
    colours = (MYXO_DIM + (MYXO_BRIGHT - MYXO_DIM) * full).astype(int)
    colours[m.scout] = SCOUT
    return colours


def draw_chain(surf, colour, pts, width, view):
    """One Myxo cell as a polyline through its discs, split where it crosses the edge."""
    jumps = np.nonzero(crosses_edge(pts[:-1], pts[1:], view))[0]
    for piece in np.split(pts, jumps + 1):
        if len(piece) >= 2:
            pygame.draw.lines(surf, colour, False, piece, width)
        for p in (piece[0], piece[-1]):
            pygame.draw.circle(surf, colour, p, width / 2)


def draw_myxo(surf, world, view):
    """Each Myxo as a green chain 0.7 µm wide; cells pausing to kill get a white outline."""
    s, m = world.settings, world.myxo
    if state.count(m) == 0:
        return
    pts = view.to_screen(m.nodes)
    width = max(1, int(round(s.disc_diam * view.scale)))
    colours = myxo_colours(world)
    rim = width + max(4, int(0.8 * width))
    for i in np.nonzero(m.pause_left > 0)[0]:
        draw_chain(surf, (255, 255, 255), pts[i], rim, view)
    for i in range(len(pts)):
        draw_chain(surf, tuple(int(v) for v in colours[i]), pts[i], width, view)


def draw_spores(surf, world, view):
    """Spores as small pale dots, about 1.5 µm across (B80)."""
    if len(world.spores) == 0:
        return
    radius = max(2, int(round(0.75 * view.scale)))
    for p in view.to_screen(world.spores):
        pygame.draw.circle(surf, SPORE_FILL, p, radius)
        pygame.draw.circle(surf, SPORE_EDGE, p, radius, 1)


def text_bar(surf, lines, font, top):
    """Lines of white text on a dark see-through bar, across the top or the bottom."""
    height = font.get_linesize() * len(lines) + 8
    bar = pygame.Surface((surf.get_width(), height), pygame.SRCALPHA)
    bar.fill(BAR)
    y0 = 0 if top else surf.get_height() - height
    surf.blit(bar, (0, y0))
    for k, line in enumerate(lines):
        surf.blit(font.render(line, True, TEXT), (10, y0 + 4 + k * font.get_linesize()))
    return y0, height


def draw_scale_bar(surf, view, font, y):
    """A bar of a round length (20, 10 or 5 µm) at the bottom right."""
    length = 20 if view.width > 80 else 10 if view.width > 30 else 5
    px, x1 = length * view.scale, view.size - 20
    pygame.draw.line(surf, (30, 30, 30), (x1 - px, y), (x1, y), 4)
    label = font.render(f"{length} µm", True, (30, 30, 30))
    surf.blit(label, (x1 - px / 2 - label.get_width() / 2, y - label.get_height() - 2))


LEGEND = ["magenta: E. coli (dark = dormant)    grey: slime trails    mauve: prey remains",
          "green: M. xanthus (bright = well fed, yellow = scout, white rim = killing)"]


def draw_hud(surf, world, font, view, title="", legend=True):
    """Time and counts on top; a scale bar and (for videos) a legend at the bottom."""
    e, m = world.ecoli, world.myxo
    alive = e.lysis_timer < 0
    n_e, n_m = int(alive.sum()), state.count(m)
    dormant = int((alive & e.dormant).sum())
    starving = int(myxo_modes.stringent(world).sum()) if n_m else 0
    killing = int((m.pause_left > 0).sum()) if n_m else 0
    top = [f"{world.bio_t / 60:5.1f} h of biology    E. coli {n_e:,} ({dormant:,} dormant)    "
           f"M. xanthus {n_m:,} ({killing} killing, {starving} starving)"]
    text_bar(surf, ([title] if title else []) + top, font, top=True)
    y0 = text_bar(surf, LEGEND, font, top=False)[0] if legend else surf.get_height()
    draw_scale_bar(surf, view, font, y0 - 18)


GRAPH_BG, GRAPH_GRID, GRAPH_TEXT = (26, 26, 31), (55, 55, 62), (175, 175, 182)
SERIES = [("ecoli", "E. coli", ECOLI, 2), ("ecoli_dormant", "dormant", ECOLI_DORMANT, 1),
          ("myxo", "M. xanthus", (70, 205, 95), 2), ("myxo_stringent", "starving", (35, 120, 55), 1)]


def nice_top(value):
    """A round number at or above `value` for the top of an axis (1, 2 or 5 × a power of ten)."""
    power = 10 ** np.floor(np.log10(max(value, 1.0)))
    return next(m * power for m in (1, 2, 5, 10) if m * power >= value)


def draw_counts_graph(surf, rect, stats, font):
    """Cell counts against biological time: E. coli and M. xanthus (thick), dormant E. coli and
    starving Myxo (thin), with the latest numbers in the legend."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, GRAPH_BG, rect)
    if len(stats.rows) < 2:
        return
    t = stats.column("bio_t") / 60.0
    data = {key: stats.column(key) for key, *_ in SERIES}
    plot = pygame.Rect(rect.x + 52, rect.y + 26, rect.w - 64, rect.h - 50)
    top, t_end = nice_top(max(d.max() for d in data.values()) * 1.05), max(t[-1], 1.0)
    for frac in (0.0, 0.5, 1.0):
        y = plot.bottom - frac * plot.h
        pygame.draw.line(surf, GRAPH_GRID, (plot.x, y), (plot.right, y))
        label = font.render(f"{top * frac:,.0f}", True, GRAPH_TEXT)
        surf.blit(label, (plot.x - label.get_width() - 6, y - label.get_height() / 2))
    for frac in (0.0, 0.5, 1.0):
        label = font.render(f"{t_end * frac:.{0 if t_end >= 10 else 1}f} h", True, GRAPH_TEXT)
        surf.blit(label, (plot.x + frac * plot.w - label.get_width() / 2, plot.bottom + 4))
    keep = np.unique(np.linspace(0, len(t) - 1, min(len(t), plot.w)).astype(int))
    xs = plot.x + t[keep] / t_end * plot.w
    x_legend = rect.x + 10
    for key, name, colour, width in SERIES:
        ys = plot.bottom - data[key][keep] / top * plot.h
        pygame.draw.lines(surf, colour, False, np.stack([xs, ys], axis=1), width)
        text = font.render(f"{name} {data[key][-1]:,.0f}", True, colour)
        surf.blit(text, (x_legend, rect.y + 5))
        x_legend += text.get_width() + 18
    surf.blit(font.render("cells vs h of biology", True, GRAPH_TEXT), (rect.right - 150, rect.y + 5))


def draw_world(surf, world, font=None, view=None, title="", legend=True):
    """The whole picture onto `surf` (square): the whole world, or the close-up `view`."""
    view = view or View(world.settings.box, surf.get_width())
    draw_background(surf, world, view)
    draw_spores(surf, world, view)
    draw_ecoli(surf, world, view)
    draw_myxo(surf, world, view)
    if font is not None:
        draw_hud(surf, world, font, view, title, legend)
