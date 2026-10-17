"""
app_live.py — the interactive window (milestones 7, B1, B91): the live world runs as you watch.

Layout (the user's design, 17 Oct 2026):
- left: the world, with a Settings button at its top right;
- below the world: cell counts against hours of biology;
- right: playback speed (×1 = real time), Run/Pause, Reset, Recommended, Record video, Save, and
  the major settings (app_params.MAIN): those marked "live" change the running world at once, the
  others apply to the next world (Reset);
- the Settings panel: advanced settings, switches that turn a rule off, rules where studies
  disagree (the recommended option marked with a star), and the fixed values (measured or from
  the paper), which can't be changed.
The app starts from the recommended settings (app_params.RECOMMENDED). Mouse wheel scrolls the
panels. Keys: space run/pause, r reset, s screenshot (to ../videos/), Esc closes the Settings panel.

Usage (from predation-sim/):  python app_live.py      (python app_live.py --test N: N frames
headless, then a screenshot; add --settings to open the Settings panel for it)
"""
import dataclasses
import json
import os
import subprocess
import sys
import time

import pygame

import app_params as P
import drawing
from engine import Simulation
from settings import make_settings
from ui_widgets import DIM, MUTED, STAR, TEXT, Button, Choice, Slider, Toggle

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEOS = os.path.join(HERE, "..", "videos")
PANEL_W, GRAPH_H = 400, 190
PANEL_BG, OVERLAY_BG = (34, 34, 40), (22, 22, 27)
SPEEDS = [1, 5, 15, 30, 60, 120, 300, 600, 0]          # × real time; 0 = as fast as the computer can
FRAME_BUDGET = 0.12                                     # s of computing per drawn frame, at most


class ScrollList:
    """A column of headers, widgets and text lines inside `area`, scrolled with the mouse wheel."""

    def __init__(self, area):
        self.area, self.rows, self.scroll, self.height = pygame.Rect(area), [], 0, 0

    def header(self, text, colour=MUTED):
        """A section title."""
        self.rows.append(dict(h=30, text=text, colour=colour, bold=True))

    def text(self, text, colour=DIM, h=20):
        """A line of plain text."""
        self.rows.append(dict(h=h, text=text, colour=colour))

    def widget(self, widget, h, offset):
        """A widget whose rect sits `offset` px below the row's top."""
        self.rows.append(dict(h=h, widget=widget, offset=offset))
        return widget

    def layout(self):
        """Place every row for the current scroll position."""
        y = self.area.y + 8 - self.scroll
        for row in self.rows:
            row["y"] = y
            if "widget" in row:
                row["widget"].rect.y = y + row["offset"]
            y += row["h"]
        self.height = y + self.scroll - self.area.y + 10

    def handle(self, event):
        """Scroll, or pass the event to the widgets; the widget that changed, or None."""
        inside = self.area.collidepoint(pygame.mouse.get_pos())
        if event.type == pygame.MOUSEWHEEL and inside:
            self.scroll = min(max(self.scroll - 40 * event.y, 0), max(self.height - self.area.h, 0))
            return None
        if event.type == pygame.MOUSEBUTTONDOWN and not self.area.collidepoint(event.pos):
            return None
        self.layout()
        for row in self.rows:
            if "widget" in row and row["widget"].handle(event):
                return row["widget"]
        return None

    def draw(self, surf, font, bold):
        """Draw the visible rows, clipped to the area."""
        self.layout()
        surf.set_clip(self.area)
        for row in self.rows:
            if row["y"] + row["h"] < self.area.y or row["y"] > self.area.bottom:
                continue
            if "widget" in row:
                row["widget"].draw(surf, font)
            else:
                f = bold if row.get("bold") else font
                surf.blit(f.render(row["text"], True, row["colour"]), (self.area.x + 10, row["y"] + 6))
        surf.set_clip(None)


class App:
    """The window, its controls and the running simulation."""

    def __init__(self, test=False):
        pygame.init()
        pygame.display.set_caption("MyxoHunt: Myxococcus xanthus hunting E. coli (live)")
        info = pygame.display.Info()
        avail = (info.current_h if info.current_h > 0 else 1000) - 90
        self.S = int(min(max(avail - GRAPH_H, 420), 820)) if not test else 700
        self.screen = pygame.display.set_mode((self.S + PANEL_W, self.S + GRAPH_H))
        self.canvas = pygame.Surface((self.S, self.S))
        self.font = pygame.font.SysFont("segoeui,arial,helvetica", 15)
        self.bold = pygame.font.SysFont("segoeui,arial,helvetica", 16, bold=True)
        self.small = pygame.font.SysFont("segoeui,arial,helvetica", 13)
        self.values = dict(P.RECOMMENDED)              # the settings the user chose (overrides)
        self.saved_on = {}                              # values a switch replaced when turned off
        self.running, self.show_settings, self.message = True, False, ""
        self.debt, self.achieved = 0.0, 0.0
        self.build_panel()
        self.build_settings()
        self.reset()

    # ------------------------------------------------------------ settings bookkeeping
    def desired(self):
        """The settings the controls describe (those marked 'reset' apply to the next world)."""
        return make_settings("live", **self.values)

    def set_values(self, changes, live):
        """Record changes; apply them to the running world too if they are live."""
        self.values.update(changes)
        if live:
            for k, v in changes.items():
                setattr(self.sim.world.settings, k, v)
        self.refresh()

    def refresh(self):
        """Show every slider, switch and option as the chosen settings say."""
        d = self.desired()
        for param, slider in self.param_sliders:
            slider.value = param.value_from(d)
        for switch, toggle in self.switches:
            toggle.value = not all(getattr(d, k) == v for k, v in switch.off.items())
        for rule, choice in self.evidence:
            match = [i for i, (_, ch) in enumerate(rule.options) if all(getattr(d, k) == v for k, v in ch.items())]
            choice.index = match[0] if match else choice.index

    # ------------------------------------------------------------ building the panels
    def slider_for(self, panel, param):
        """A slider row for one Param."""
        note = "" if param.when == "live" else "on Reset"
        slider = Slider(param.label, param.lo, param.hi, param.lo, param.step,
                        (panel.area.x + 12, 0, panel.area.w - 30, 6), fmt=param.fmt, note=note)
        self.param_sliders.append((param, panel.widget(slider, 48, 36)))

    def build_panel(self):
        """The right-hand panel: playback, buttons and the major settings."""
        x, w = self.S + 10, PANEL_W - 20
        self.param_sliders = []
        self.speed = Slider("Speed", 0, len(SPEEDS) - 1, len(SPEEDS) - 1, 1, (x + 2, 60, w - 20, 6),
                            fmt=lambda i: "as fast as possible" if SPEEDS[i] == 0 else
                            ("×1 = real time" if SPEEDS[i] == 1 else f"×{SPEEDS[i]} real time"))
        self.run_button = Button("Pause", self.toggle_run, (x, 78, 120, 30))
        self.buttons = [self.run_button, Button("New world", self.reset, (x + 128, 78, 120, 30)),
                        Button("Recommended", self.recommended, (x + 256, 78, 124, 30)),
                        Button("Record video", self.record, (x, 114, 185, 30)),
                        Button("Save settings", self.save_settings, (x + 195, 114, 185, 30))]
        self.panel = ScrollList((self.S, 168, PANEL_W, self.S + GRAPH_H - 168))
        self.panel.header("Main settings (live: change the running world)")
        for param in P.MAIN:
            if param.when == "live":
                self.slider_for(self.panel, param)
        self.panel.header("Next world (press New world to apply)")
        for param in P.MAIN:
            if param.when == "reset":
                self.slider_for(self.panel, param)
        self.panel.header("Colours")
        for line in ["magenta: E. coli (dark = dormant, grey = dead)", "green: M. xanthus (bright = well fed)",
                     "white dot: a Myxo's leading pole", "orange: reversed in the last 15 s",
                     "yellow: scouts; white rim: killing a prey", "grey: slime trails; mauve: prey remains",
                     "brown: ground nutrients (darker = richer)"]:
            self.panel.text(line)

    def build_settings(self):
        """The Settings panel over the world: advanced settings, switches, evidence options, fixed values."""
        self.settings_list = ScrollList((0, 40, self.S, self.S + GRAPH_H - 40))
        sl = self.settings_list
        self.close_button = Button("Close", lambda: setattr(self, "show_settings", False), (self.S - 90, 6, 80, 28))
        sl.header("Advanced settings (tuned or assumed)")
        for param in P.ADVANCED:
            self.slider_for(sl, param)
        sl.header("Switch a rule off")
        self.switches = []
        for switch in P.EFFECTS:
            toggle = Toggle(switch.label, True, (12, 0, self.S - 30, 22), note=switch.note)
            self.switches.append((switch, sl.widget(toggle, 44 if switch.note else 28, 2)))
        sl.header("Where studies disagree (star = recommended)", colour=STAR)
        self.evidence = []
        for rule in P.EVIDENCE:
            choice = Choice(rule.label, [o[0] for o in rule.options], rule.best, (12, 0, self.S - 30, 26), best=rule.best)
            self.evidence.append((rule, sl.widget(choice, 56, 24)))
        sl.header("Fixed: measured or from the paper (not adjustable)")
        for name, value, source in P.FIXED:
            sl.text(f"{name}: {value}", colour=TEXT, h=18)
            sl.text(f"    {source}", h=22)

    # ------------------------------------------------------------ actions
    def toggle_run(self):
        """Run or pause."""
        self.running = not self.running
        self.run_button.label = "Pause" if self.running else "Run"

    def reset(self):
        """A new world from the chosen settings."""
        self.sim = Simulation(self.desired())
        self.debt = 0.0
        self.refresh()
        self.message = "new world"

    def recommended(self):
        """Back to the recommended settings, in a new world."""
        self.values, self.saved_on = dict(P.RECOMMENDED), {}
        self.reset()
        self.message = "recommended settings, new world"

    def save_settings(self):
        """Write the chosen settings to settings_live.json."""
        path = os.path.join(HERE, "settings_live.json")
        with open(path, "w", encoding="utf8") as fh:
            json.dump(dataclasses.asdict(self.desired()), fh, indent=2)
        self.message = "saved settings_live.json"

    def record(self):
        """Start a 60 bio-h video of the chosen settings in the background (run_record.py)."""
        s, base = self.desired(), make_settings("live")
        changed = {f.name: getattr(s, f.name) for f in dataclasses.fields(s)
                   if getattr(s, f.name) != getattr(base, f.name) and f.name not in ("seed", "colors")}
        name = time.strftime("app_%Y%m%d_%H%M%S")
        args = [sys.executable, "-X", "utf8", "run_record.py", name, "--minutes", f"{3600 / s.speedup:g}",
                "--seed", str(s.seed), "--quality", "5"] + [f"{k}={v}" for k, v in changed.items()]
        os.makedirs(VIDEOS, exist_ok=True)
        log = open(os.path.join(VIDEOS, name + ".log"), "w", encoding="utf8")
        subprocess.Popen(args, cwd=HERE, stdout=log, stderr=subprocess.STDOUT)
        self.message = f"recording videos/{name}.mp4 in the background"

    def screenshot(self):
        """Save the window as a picture."""
        os.makedirs(VIDEOS, exist_ok=True)
        path = os.path.join(VIDEOS, time.strftime("screenshot_%Y%m%d_%H%M%S.png"))
        pygame.image.save(self.screen, path)
        self.message = f"saved {os.path.basename(path)}"

    # ------------------------------------------------------------ events
    def on_change(self, widget):
        """A control changed: turn it into settings."""
        for param, slider in self.param_sliders:
            if slider is widget:
                self.set_values(param.settings_for(slider.value, self.desired()), param.when == "live")
                if param.when == "reset":
                    self.message = f"{param.label}: applies to the next world"
                return
        for switch, toggle in self.switches:
            if toggle is widget:
                if toggle.value:
                    self.set_values(self.saved_on.pop(switch.label, {}), True)
                else:
                    d = self.desired()
                    self.saved_on[switch.label] = {k: getattr(d, k) for k in switch.off}
                    self.set_values(dict(switch.off), True)
                return
        for rule, choice in self.evidence:
            if choice is widget:
                self.set_values(dict(rule.options[choice.index][1]), True)
                return

    def handle(self, event):
        """Keys and clicks."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.show_settings = False
            {pygame.K_SPACE: self.toggle_run, pygame.K_r: self.reset, pygame.K_s: self.screenshot}.get(
                event.key, lambda: None)()
            return
        self.speed.handle(event)
        for button in self.buttons:
            button.handle(event)
        changed = self.panel.handle(event)
        if self.show_settings:
            self.close_button.handle(event)
            changed = changed or self.settings_list.handle(event)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.settings_rect().collidepoint(event.pos):
            self.show_settings = True
        if changed is not None:
            self.on_change(changed)

    # ------------------------------------------------------------ running and drawing
    def advance(self, wall_dt):
        """Step the world to keep up with the chosen speed, within the time budget of one frame."""
        if not self.running:
            return
        dt, warp, t0 = self.sim.world.settings.dt, SPEEDS[self.speed.value], time.perf_counter()
        start_t, budget = self.sim.world.t, FRAME_BUDGET if warp else 2 * FRAME_BUDGET
        self.debt = min(self.debt + warp * wall_dt / 60.0, 50 * dt) if warp else float("inf")
        while self.debt >= dt and time.perf_counter() - t0 < budget:
            self.sim.step()
            self.debt -= dt
        if warp == 0:
            self.debt = 0.0
        if wall_dt > 0:
            self.achieved = 0.9 * self.achieved + 0.1 * (self.sim.world.t - start_t) * 60.0 / wall_dt

    def settings_rect(self):
        """The Settings button at the top right of the world."""
        return pygame.Rect(self.S - 96, 6, 88, 26)

    def draw_world_area(self):
        """The world, a small top bar with the time and the Settings button, and the graph below."""
        w = self.sim.world
        drawing.draw_world(self.canvas, w)
        bar = pygame.Surface((self.S, 38), pygame.SRCALPHA)
        bar.fill((20, 20, 20, 160))
        self.canvas.blit(bar, (0, 0))
        self.canvas.blit(self.bold.render(f"{w.bio_t / 60:5.1f} h of biology", True, TEXT), (10, 9))
        drawing.draw_scale_bar(self.canvas, drawing.View(w.settings.box, self.S), self.small, self.S - 14)
        self.screen.blit(self.canvas, (0, 0))
        rect = self.settings_rect()
        pygame.draw.rect(self.screen, (70, 70, 84), rect, border_radius=6)
        label = self.font.render("Settings", True, TEXT)
        self.screen.blit(label, label.get_rect(center=rect.center))
        drawing.draw_counts_graph(self.screen, (0, self.S, self.S, GRAPH_H), self.sim.stats, self.small)

    def draw_panel(self):
        """The right-hand panel."""
        pygame.draw.rect(self.screen, PANEL_BG, (self.S, 0, PANEL_W, self.S + GRAPH_H))
        self.screen.blit(self.bold.render("MyxoHunt: M. xanthus hunting E. coli", True, TEXT), (self.S + 10, 8))
        self.speed.draw(self.screen, self.font)
        for button in self.buttons:
            button.draw(self.screen, self.font)
        status = f"now ×{self.achieved:,.0f} real time" + (f"   {self.message}" if self.message else "")
        self.screen.blit(self.small.render(status, True, DIM), (self.S + 10, 148))
        self.panel.draw(self.screen, self.font, self.bold)

    def draw_settings(self):
        """The Settings panel over the world and the graph."""
        pygame.draw.rect(self.screen, OVERLAY_BG, (0, 0, self.S, self.S + GRAPH_H))
        self.screen.blit(self.bold.render("Settings", True, TEXT), (12, 10))
        self.screen.blit(self.small.render("wheel to scroll; Esc to close", True, DIM), (100, 13))
        self.close_button.draw(self.screen, self.font)
        self.settings_list.draw(self.screen, self.font, self.bold)

    def frame(self, wall_dt):
        """Advance the world and draw one frame."""
        self.advance(wall_dt)
        if self.show_settings:
            self.draw_settings()
        else:
            self.draw_world_area()
        self.draw_panel()
        pygame.display.flip()

    def run(self, max_frames=None):
        """The main loop: events, steps, drawing, at most 30 frames a second."""
        clock, n = pygame.time.Clock(), 0
        while max_frames is None or n < max_frames:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                self.handle(event)
            self.frame(clock.tick(30) / 1000.0)
            n += 1


def main():
    """Open the window and run until it's closed."""
    if "--test" in sys.argv:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        app = App(test=True)
        app.speed.value = len(SPEEDS) - 1
        app.run(max_frames=int(sys.argv[sys.argv.index("--test") + 1]))
        app.show_settings = "--settings" in sys.argv
        app.frame(0.0)
        app.screenshot()
        print(app.message)
        return
    App().run()
    pygame.quit()


if __name__ == "__main__":
    main()
