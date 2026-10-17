"""
ui_widgets.py — tiny home-made widgets for the live window, with no extra library (build manual
§5): a slider, a switch, a choice you click to cycle through, and a button. Every widget has a
`rect` that the window may move (the settings panel scrolls).
"""
import pygame

TEXT = (232, 232, 232)
MUTED = (160, 160, 168)
DIM = (120, 120, 128)
TRACK = (85, 85, 92)
KNOB = (110, 190, 255)
FACE = (58, 58, 68)
FACE_HOT = (88, 88, 108)
ON = (90, 190, 110)
STAR = (255, 205, 80)


class Slider:
    """A horizontal slider from lo to hi that snaps to `step`; `fmt` shows the value."""

    def __init__(self, label, lo, hi, value, step, rect, fmt="{:g}", note=""):
        self.label, self.lo, self.hi, self.step, self.fmt, self.note = label, lo, hi, step, fmt, note
        self.value = value
        self.rect = pygame.Rect(rect)
        self.dragging = False

    def value_at(self, x):
        """The snapped value under screen position x."""
        frac = min(max((x - self.rect.x) / self.rect.w, 0.0), 1.0)
        v = round((self.lo + frac * (self.hi - self.lo)) / self.step) * self.step
        return int(round(v)) if float(self.step).is_integer() else round(v, 6)

    def handle(self, event):
        """Follow clicks and drags on the slider; True when the value changed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = self.rect.inflate(16, 20).collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            return False
        if self.dragging and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            new = self.value_at(event.pos[0])
            changed, self.value = new != self.value, new
            return changed
        return False

    def draw(self, surf, font):
        """The label and value above the track, the knob at the value, a note on the right."""
        shown = self.fmt(self.value) if callable(self.fmt) else self.fmt.format(self.value)
        surf.blit(font.render(f"{self.label}: {shown}", True, TEXT), (self.rect.x, self.rect.y - 26))
        if self.note:
            note = font.render(self.note, True, DIM)
            surf.blit(note, (self.rect.right - note.get_width(), self.rect.y - 26))
        pygame.draw.rect(surf, TRACK, self.rect, border_radius=3)
        frac = (min(max(self.value, self.lo), self.hi) - self.lo) / (self.hi - self.lo)
        pygame.draw.circle(surf, KNOB, (self.rect.x + frac * self.rect.w, self.rect.centery), 7)


class Toggle:
    """An on/off switch with a label."""

    def __init__(self, label, value, rect, note=""):
        self.label, self.value, self.note = label, value, note
        self.rect = pygame.Rect(rect)

    def handle(self, event):
        """Flip on a click; True when it changed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.value = not self.value
            return True
        return False

    def draw(self, surf, font):
        """A small switch and the label."""
        box = pygame.Rect(self.rect.x, self.rect.y + 3, 34, 16)
        pygame.draw.rect(surf, ON if self.value else TRACK, box, border_radius=8)
        knob_x = box.right - 8 if self.value else box.x + 8
        pygame.draw.circle(surf, TEXT, (knob_x, box.centery), 6)
        surf.blit(font.render(self.label, True, TEXT if self.value else MUTED), (box.right + 8, self.rect.y + 2))
        if self.note:
            surf.blit(font.render(self.note, True, DIM), (box.right + 8, self.rect.y + 20))


class Choice:
    """A box that cycles through fixed options when clicked; option `best` is marked ★."""

    def __init__(self, label, options, index, rect, best=None):
        self.label, self.options, self.index, self.best = label, list(options), index, best
        self.rect = pygame.Rect(rect)

    @property
    def value(self):
        """The option shown now."""
        return self.options[self.index]

    def handle(self, event):
        """Next option on a click; True when it changed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.index = (self.index + 1) % len(self.options)
            return True
        return False

    def draw(self, surf, font):
        """The label above, the current option in a box (a star if it is the recommended one)."""
        hot = self.rect.collidepoint(pygame.mouse.get_pos())
        if self.label:
            surf.blit(font.render(self.label, True, MUTED), (self.rect.x, self.rect.y - 18))
        pygame.draw.rect(surf, FACE_HOT if hot else FACE, self.rect, border_radius=5)
        best = self.best is not None and self.index == self.best
        x = self.rect.x + 8
        if best:
            draw_star(surf, (x + 6, self.rect.centery), 6, STAR)
            x += 18
        text = font.render(str(self.value), True, STAR if best else TEXT)
        surf.blit(text, (x, self.rect.centery - text.get_height() // 2))


def draw_star(surf, centre, r, colour):
    """A five-pointed star (drawn, since the default font has no star sign)."""
    import math
    pts = [(centre[0] + (r if k % 2 == 0 else r * 0.45) * math.sin(math.pi * k / 5),
            centre[1] - (r if k % 2 == 0 else r * 0.45) * math.cos(math.pi * k / 5)) for k in range(10)]
    pygame.draw.polygon(surf, colour, pts)


class Button:
    """A button that calls `action()` when clicked."""

    def __init__(self, label, action, rect):
        self.label, self.action = label, action
        self.rect = pygame.Rect(rect)

    def handle(self, event):
        """Call the action on a click; True if clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.action()
            return True
        return False

    def draw(self, surf, font):
        """A rounded box with the label in the middle."""
        hot = self.rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surf, FACE_HOT if hot else FACE, self.rect, border_radius=6)
        text = font.render(self.label, True, TEXT)
        surf.blit(text, text.get_rect(center=self.rect.center))
