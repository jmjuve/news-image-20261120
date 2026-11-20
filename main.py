#!/usr/bin/env python3
"""news-image-20261120: sum up Friday 20 November 2026 in one image.

Draws a newspaper front page (1024x1024 PNG) with pure Python 3 stdlib
only -- no PIL, no network, no external assets -- so it runs identically
in the make.fun sandbox (stdlib only) and on any local Python 3.

Layout (PLAN.md art direction, drawn live by this program):
  masthead "FRIDAY 20 NOVEMBER 2026", red rule,
  hero: Kyiv at night under attack -- the Dnipro river with its
  bridges, missile trails and explosions over the skyline, a bridge
  span damaged,
  headline "KYIV'S BRIDGES HIT",
  subline "Overnight missile attack damages Dnipro crossings --
  Putin's retaliation for the Kerch Bridge strikes",
  bottom strip, three equal mini-stories: Asian markets tumble,
  Cyclone Akvan hits India, Harris meets Macron in Paris.

Facts in the image (verified 2+ sources, see PLAN.md):
  - no bridge number is stated (sources disagree: 2 vs 3 damaged);
  - no evacuation number for the cyclone (single-sourced);
  - market moves as percentages only (Taiwan down 5%+, Nikkei -4.8%).

Deterministic: fixed palette, fixed geometry, no time, no randomness,
PNG written with zlib level 9 and no ancillary chunks, so two runs
produce byte-identical output.
"""

import binascii
import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
CREAM = (246, 238, 214)   # newsprint background
INK = (20, 20, 20)        # type and line work
RED = (193, 39, 45)       # the one red accent: the lead story only
NIGHT = (14, 22, 44)      # Kyiv night sky
NIGHT_TOWER = (28, 34, 58)  # skyline silhouette against the night
RIVER = (26, 64, 112)     # the Dnipro at night
RIVER_LIGHT = (90, 140, 190)
SEA = (78, 127, 166)
SEA_DARK = (38, 80, 130)
SAND = (222, 205, 160)
GREY = (96, 96, 96)
SMOKE = (150, 150, 150)
STEEL = (58, 58, 58)
WHITE = (255, 255, 255)
FIRE = (240, 120, 30)     # explosion and fire glow
FIRE_YELLOW = (250, 200, 60)
WOOD = (140, 95, 55)
WOOD_DARK = (96, 62, 34)
NAVY = (30, 44, 78)
GOLD = (250, 220, 90)
FLAG_BLUE = (30, 60, 140)
SKY_PALE = (199, 220, 234)

# ------------------------------------------------------- stroke font
# Hand-built single-stroke capitals on a 10 x 12 grid (y down, baseline
# y=12; descenders to y=14). Each glyph is a list of strokes; each stroke
# is a list of (x, y) points joined by straight segments. Rendered thick,
# it reads as a clean bold sans at any scale.
FONT = {
    "A": [[(1, 12), (5, 0), (9, 12)], [(3, 8), (7, 8)]],
    "B": [[(1, 0), (1, 12)],
          [(1, 0), (6, 0), (8, 2), (8, 4), (6, 6), (1, 6)],
          [(1, 6), (6, 6), (8, 8), (8, 10), (6, 12), (1, 12)]],
    "C": [[(8, 2), (6, 0), (3, 0), (1, 2), (1, 10), (3, 12), (6, 12), (8, 10)]],
    "D": [[(1, 0), (1, 12)], [(1, 0), (6, 0), (8, 2), (8, 10), (6, 12), (1, 12)]],
    "E": [[(8, 0), (1, 0), (1, 12), (8, 12)], [(1, 6), (6, 6)]],
    "F": [[(8, 0), (1, 0), (1, 12)], [(1, 6), (6, 6)]],
    "G": [[(8, 2), (6, 0), (3, 0), (1, 2), (1, 10), (3, 12), (6, 12),
           (8, 10), (8, 7), (5, 7)]],
    "H": [[(1, 0), (1, 12)], [(9, 0), (9, 12)], [(1, 6), (9, 6)]],
    "I": [[(5, 0), (5, 12)], [(2, 0), (8, 0)], [(2, 12), (8, 12)]],
    "J": [[(8, 0), (8, 9), (6, 12), (2, 12), (1, 10)]],
    "K": [[(1, 0), (1, 12)], [(9, 0), (1, 6)], [(4, 5), (9, 12)]],
    "L": [[(1, 0), (1, 12), (8, 12)]],
    "M": [[(1, 12), (1, 0), (5, 7), (9, 0), (9, 12)]],
    "N": [[(1, 12), (1, 0), (9, 12), (9, 0)]],
    "O": [[(3, 0), (7, 0), (9, 2), (9, 10), (7, 12), (3, 12), (1, 10),
           (1, 2), (3, 0)]],
    "P": [[(1, 12), (1, 0), (7, 0), (9, 2), (9, 5), (7, 7), (1, 7)]],
    "Q": [[(3, 0), (7, 0), (9, 2), (9, 10), (7, 12), (3, 12), (1, 10),
           (1, 2), (3, 0)], [(6, 9), (9, 13)]],
    "R": [[(1, 12), (1, 0), (7, 0), (9, 2), (9, 5), (7, 7), (1, 7)],
          [(6, 7), (9, 12)]],
    "S": [[(8, 2), (6, 0), (3, 0), (1, 2), (1, 5), (3, 7), (7, 7), (9, 9),
           (9, 10), (7, 12), (3, 12), (1, 10)]],
    "T": [[(1, 0), (9, 0)], [(5, 0), (5, 12)]],
    "U": [[(1, 0), (1, 9), (3, 12), (7, 12), (9, 9), (9, 0)]],
    "V": [[(1, 0), (5, 12), (9, 0)]],
    "W": [[(1, 0), (3, 12), (5, 6), (7, 12), (9, 0)]],
    "X": [[(1, 0), (9, 12)], [(9, 0), (1, 12)]],
    "Y": [[(1, 0), (5, 6), (9, 0)], [(5, 6), (5, 12)]],
    "Z": [[(1, 0), (9, 0), (1, 12), (9, 12)]],
    "0": [[(3, 0), (7, 0), (9, 2), (9, 10), (7, 12), (3, 12), (1, 10),
           (1, 2), (3, 0)]],
    "1": [[(3, 2), (5, 0), (5, 12)], [(2, 12), (8, 12)]],
    "2": [[(1, 2), (3, 0), (7, 0), (9, 2), (9, 5), (1, 12), (9, 12)]],
    "3": [[(2, 0), (7, 0), (9, 2), (9, 5), (7, 7)],
          [(7, 7), (9, 9), (9, 11), (7, 12), (2, 12)]],
    "4": [[(6, 0), (6, 12)], [(0, 8), (8, 8)], [(6, 0), (0, 8)]],
    "5": [[(8, 0), (1, 0), (1, 6), (7, 6), (9, 8), (9, 10), (7, 12), (1, 12)]],
    "6": [[(8, 1), (6, 0), (3, 0), (1, 2), (1, 10), (3, 12), (6, 12),
           (8, 10), (8, 8), (6, 6), (1, 6)]],
    "7": [[(1, 0), (9, 0), (5, 12)]],
    "8": [[(3, 0), (7, 0), (9, 2), (9, 5), (7, 7), (3, 7), (1, 5), (1, 2),
           (3, 0)],
          [(3, 7), (7, 7), (9, 9), (9, 11), (7, 12), (3, 12), (1, 10),
           (1, 9), (3, 7)]],
    "9": [[(1, 6), (1, 2), (3, 0), (7, 0), (9, 2), (9, 6), (7, 8), (3, 8),
           (1, 6)],
          [(9, 6), (9, 12)]],
    "%": [[(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)],
          [(7, 9), (9, 9), (9, 11), (7, 11), (7, 9)],
          [(8, 1), (2, 11)]],
    " ": [],
    ",": [[(5, 10), (5, 12), (3, 14)]],
    ".": [[(4, 11), (6, 11), (6, 13), (4, 13), (4, 11)]],
    "'": [[(5, 0), (4, 4)]],
    "-": [[(1, 6), (9, 6)]],
    "\u2014": [[(0, 6), (10, 6)]],
    ":": [[(4, 3), (6, 3), (6, 5), (4, 5), (4, 3)],
          [(4, 9), (6, 9), (6, 11), (4, 11), (4, 9)]],
    ";": [[(4, 3), (6, 3), (6, 5), (4, 5), (4, 3)],
          [(5, 8), (5, 11), (3, 13)]],
    "/": [[(8, 12), (2, 0)]],
    "!": [[(5, 0), (5, 8)], [(4, 10), (6, 10), (6, 12), (4, 12), (4, 10)]],
    "?": [[(2, 2), (4, 0), (7, 0), (9, 2), (9, 4), (7, 6), (5, 6), (5, 8)],
          [(4, 10), (6, 10), (6, 12), (4, 12), (4, 10)]],
    "(": [[(7, 0), (4, 3), (4, 9), (7, 12)]],
    ")": [[(3, 0), (6, 3), (6, 9), (3, 12)]],
    "\u2022": [[(4, 5), (6, 5), (6, 7), (4, 7), (4, 5)]],
}

ADVANCE = 11.0  # glyph cell width in font units, including the gap


def text_width(text, scale):
    """Pixel width of `text` at the given scale."""
    return len(text) * ADVANCE * scale


# ---------------------------------------------------------------- canvas
class Canvas:
    """A plain RGB raster; every draw op clips to the frame."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x0, y0, x1, y1, color):
        x0 = max(0, int(x0)); y0 = max(0, int(y0))
        x1 = min(self.w, int(x1)); y1 = min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def fill_circle(self, cx, cy, r, color):
        r = int(r)
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)

    def disc(self, cx, cy, r, color):
        self.fill_circle(cx, cy, r, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line stamped with a disc of radius thick//2."""
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        r = max(0, thick // 2)
        dx = abs(x1 - x0); dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.disc(x0, y0, r, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    def polyline(self, points, color, thick=1):
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            self.line(ax, ay, bx, by, color, thick)

    def polygon(self, points, color):
        """Scanline fill of a simple polygon (even-odd rule)."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        y0, y1 = int(math.ceil(min(ys))), int(math.floor(max(ys)))
        n = len(points)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                ax, ay = points[i]
                bx, by = points[(i + 1) % n]
                if (ay <= y < by) or (by <= y < ay):
                    t = (y - ay) / (by - ay)
                    xs.append(ax + t * (bx - ax))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(math.ceil(xs[j])), y,
                               int(math.floor(xs[j + 1])) + 1, y + 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for dy in range(-int(ry), int(ry) + 1):
            t = 1.0 - (dy * dy) / float(ry * ry)
            dx = int(rx * math.sqrt(max(0.0, t)))
            self.fill_rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)

    def ring(self, cx, cy, r, color, thick=2):
        for a in range(0, 360, 2):
            t = math.radians(a)
            self.disc(int(cx + r * math.cos(t)), int(cy + r * math.sin(t)),
                      max(0, thick // 2), color)

    # ------------------------------------------------------------ text
    def text(self, x, y, scale, color, s, thick=None):
        """Draw `s` (already upper-case) with top-left at (x, y)."""
        if thick is None:
            thick = max(1, int(round(scale * 0.85)))
        cx = float(x)
        for ch in s:
            for stroke in FONT.get(ch, FONT.get("?", [])):
                pts = [(cx + px * scale, y + py * scale) for (px, py) in stroke]
                self.polyline(pts, color, thick)
            cx += ADVANCE * scale

    def text_centered(self, cx, y, scale, color, s, thick=None):
        self.text(cx - text_width(s, scale) / 2.0, y, scale, color, s, thick)


# ---------------------------------------------------------------- PNG
def png_bytes(canvas):
    """Encode the canvas as a deterministic PNG (no ancillary chunks)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        out = struct.pack(">I", len(payload)) + tag + payload
        out += struct.pack(">I", binascii.crc32(tag + payload) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", data) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- scenes
def draw_flag_us(c, fx, fy):
    """US flag, 56 x 36, top-left (fx, fy): stripes + blue canton."""
    for i in range(5):
        c.fill_rect(fx, fy + i * 7, fx + 56, fy + i * 7 + 4,
                    RED if i % 2 == 0 else WHITE)
    c.fill_rect(fx, fy, fx + 24, fy + 18, FLAG_BLUE)
    for sx in (6, 14, 22):
        for sy in (5, 12):
            c.fill_circle(fx + sx, fy + sy, 1, WHITE)


def draw_flag_fr(c, fx, fy):
    """France flag, 56 x 36, top-left (fx, fy): blue / white / red."""
    c.fill_rect(fx, fy, fx + 19, fy + 36, FLAG_BLUE)
    c.fill_rect(fx + 19, fy, fx + 37, fy + 36, WHITE)
    c.fill_rect(fx + 37, fy, fx + 56, fy + 36, RED)


def draw_masthead(c):
    c.text_centered(W / 2, 26, 2.6, INK, "FRIDAY 20 NOVEMBER 2026")
    c.fill_rect(24, 96, 1000, 102, RED)
    c.fill_rect(24, 106, 1000, 108, INK)
    c.text(24, 122, 1.5, RED, "LEAD STORY")
    c.text(1000 - text_width("KYIV", 1.5), 122, 1.5, INK, "KYIV")


def burst(c, bx, by, r, core, mid, outer):
    """An explosion: ray star + layered discs, brightest at the core."""
    for ang in range(0, 360, 30):
        t = math.radians(ang)
        c.line(bx, by, bx + r * math.cos(t), by + r * math.sin(t), outer, 4)
    c.fill_circle(bx, by, r, outer)
    c.fill_circle(bx, by, int(r * 0.65), mid)
    c.fill_circle(bx, by, int(r * 0.35), core)


def draw_hero(c):
    x0, y0, x1, y1 = 24, 150, 1000, 400
    # night sky, then the Dnipro river band along the bottom
    c.fill_rect(x0, y0, x1, 330, NIGHT)
    c.fill_rect(x0, 330, x1, y1, RIVER)
    # stars, fixed positions
    for (sx, sy, sr) in ((80, 170, 2), (150, 205, 1), (230, 168, 2),
                         (330, 190, 1), (430, 164, 2), (520, 200, 1),
                         (610, 172, 2), (700, 196, 1), (790, 166, 2),
                         (880, 200, 1), (950, 172, 2), (60, 240, 1),
                         (960, 240, 1), (380, 220, 1), (660, 230, 1)):
        c.fill_circle(sx, sy, sr, WHITE)
    # pale moon, upper right
    c.fill_circle(905, 185, 20, (232, 228, 200))
    c.fill_circle(898, 180, 16, (240, 236, 214))
    # Kyiv skyline silhouette along the horizon (base y=330)
    towers = [(36, 44, 84), (92, 36, 58), (140, 50, 108), (202, 32, 66),
              (246, 42, 92), (760, 40, 70), (812, 52, 118), (876, 34, 62),
              (922, 46, 96), (970, 26, 54)]
    for (bx, bw, bh) in towers:
        c.fill_rect(bx, 330 - bh, bx + bw, 330, NIGHT_TOWER)
        for wy in range(330 - bh + 10, 324, 18):
            for wx in range(bx + 7, bx + bw - 7, 14):
                c.fill_rect(wx, wy, wx + 4, wy + 5, GOLD)
    # church dome with a cross, left of centre
    c.fill_circle(560, 262, 18, GOLD)
    c.polygon([(542, 264), (578, 264), (560, 244)], GOLD)
    c.line(560, 244, 560, 228, GOLD, 3)
    c.line(552, 234, 568, 234, GOLD, 3)
    c.fill_rect(548, 264, 572, 330, NIGHT_TOWER)
    # tall spire (Motherland Monument), right of centre
    c.polygon([(668, 330), (676, 330), (672, 210)], NIGHT_TOWER)
    c.line(672, 210, 672, 196, GOLD, 3)
    # fires burning at the foot of two towers
    for (fx, fy) in ((160, 326), (836, 326)):
        c.fill_circle(fx, fy, 16, FIRE)
        c.fill_circle(fx, fy - 4, 10, FIRE_YELLOW)
        c.fill_circle(fx - 12, fy - 18, 9, SMOKE)
        c.fill_circle(fx + 6, fy - 28, 12, SMOKE)
        c.fill_circle(fx - 2, fy - 40, 9, SMOKE)
    # missile trails arcing down from the top of the sky
    c.polyline([(120, 152), (180, 190), (250, 228), (310, 258)],
               FIRE_YELLOW, 3)
    c.polyline([(620, 152), (640, 190), (668, 222), (700, 248)],
               FIRE_YELLOW, 3)
    c.polyline([(860, 152), (830, 186), (800, 214), (772, 238)],
               WHITE, 3)
    # explosions over the skyline
    burst(c, 312, 252, 22, WHITE, FIRE_YELLOW, FIRE)
    burst(c, 702, 242, 18, WHITE, FIRE_YELLOW, FIRE)
    burst(c, 770, 232, 12, WHITE, FIRE_YELLOW, FIRE)
    # river shimmer lines
    for wy in (344, 362, 382):
        for wx in range(x0 + 20, x0 + 940, 90):
            c.line(wx, wy, wx + 44, wy, RIVER_LIGHT, 2)
    # the two Dnipro bridges across the river, decks at y=346 and y=374
    # near bridge: deck, pylons, cables
    c.fill_rect(x0, 344, x1, 350, STEEL)
    c.fill_rect(x0, 350, x1, 352, INK)
    for px in (150, 480, 850):
        c.fill_rect(px, 316, px + 10, 344, STEEL)
        c.line(px + 5, 316, px - 52, 344, WHITE, 2)
        c.line(px + 5, 316, px + 62, 344, WHITE, 2)
    # far bridge: lower deck, its middle span torn away by the strike
    c.fill_rect(x0, 372, x0 + 380, 378, STEEL)
    c.fill_rect(x0 + 620, 372, x1, 378, STEEL)
    c.fill_rect(x0, 378, x0 + 380, 380, INK)
    c.fill_rect(x0 + 620, 378, x1, 380, INK)
    for px in (120, 880):
        c.fill_rect(px, 352, px + 10, 372, STEEL)
    # the broken span, hanging down into the river
    c.polygon([(x0 + 380, 372), (x0 + 440, 384), (x0 + 486, 396),
               (x0 + 470, 400), (x0 + 424, 388), (x0 + 380, 378)], STEEL)
    c.polygon([(x0 + 620, 372), (x0 + 566, 386), (x0 + 540, 398),
               (x0 + 556, 400), (x0 + 584, 388), (x0 + 620, 378)], STEEL)
    # splash and debris where the span hit the water
    c.fill_circle(512, 394, 8, WHITE)
    c.fill_circle(530, 392, 5, WHITE)
    c.fill_rect(492, 396, 520, 400, STEEL)
    # smoke over the broken span
    c.fill_circle(470, 356, 14, SMOKE)
    c.fill_circle(500, 344, 18, GREY)
    c.fill_circle(528, 356, 12, SMOKE)
    # fire glow on the broken span
    c.fill_circle(500, 372, 10, FIRE)
    c.fill_circle(500, 372, 5, FIRE_YELLOW)
    c.text(1000 - text_width("DNIPRO RIVER", 1.0), 384, 1.0, WHITE,
           "DNIPRO RIVER")
    # headline + subline under the picture
    c.text_centered(W / 2, 418, 4.2, RED, "KYIV'S BRIDGES HIT")
    c.text_centered(W / 2, 486, 1.9, INK, "OVERNIGHT MISSILE ATTACK DAMAGES")
    c.text_centered(W / 2, 516, 1.9, INK,
                    "DNIPRO CROSSINGS \u2014 PUTIN'S RETALIATION")
    c.text_centered(W / 2, 546, 1.9, INK, "FOR THE KERCH BRIDGE STRIKES")


def draw_markets(c, x0, w):
    """Mini-story 1: Asian markets tumble -- a falling red chart."""
    y0, y1 = 700, 850
    c.fill_rect(x0, y0, x0 + w, y1, WHITE)
    # gridlines
    for gy in (724, 754, 784, 814):
        c.line(x0 + 12, gy, x0 + w - 12, gy, (220, 220, 220), 1)
    # axes
    c.line(x0 + 12, y0 + 16, x0 + 12, y1 - 34, INK, 2)
    c.line(x0 + 12, y1 - 34, x0 + w - 12, y1 - 34, INK, 2)
    # the fall: a steep red line with two small dead-cat bounces
    pts = [(x0 + 20, 716), (x0 + 70, 726), (x0 + 110, 748),
           (x0 + 150, 742), (x0 + 190, 768), (x0 + 230, 762),
           (x0 + 272, 800), (x0 + 300, 812)]
    c.polyline(pts, RED, 5)
    # markers on the line
    for (px, py) in pts:
        c.fill_circle(px, py, 4, RED)
    # big down arrow at the end of the fall
    ax, ay = x0 + 292, 806
    c.line(ax, ay - 26, ax, ay + 6, RED, 5)
    c.polygon([(ax - 10, ay - 2), (ax + 10, ay - 2), (ax, ay + 14)], RED)
    # the numbers, in red under the chart
    c.text_centered(x0 + w / 2, y1 - 20, 1.0, RED, "TAIWAN -5%  NIKKEI -4.8%")


def draw_cyclone(c, x0, w):
    """Mini-story 2: Cyclone Akvan -- a spiral storm over India's coast."""
    y0, y1 = 700, 850
    c.fill_rect(x0, y0, x0 + w, y1, SEA)
    # India's east coast: sand land on the left, sea on the right
    c.polygon([(x0, y0), (x0 + 92, y0), (x0 + 70, y0 + 60),
               (x0 + 96, y0 + 110), (x0 + 60, y1), (x0, y1)], SAND)
    # the storm spiral, centred over the coast near Gopalpur
    cx, cy = x0 + 190, 770
    for r, col in ((58, WHITE), (44, (210, 228, 240)), (30, WHITE),
                   (16, (210, 228, 240))):
        c.ring(cx, cy, r, col, 6)
    c.fill_circle(cx, cy, 10, WHITE)
    c.fill_circle(cx, cy, 5, SEA_DARK)
    # spiral arms sweeping out over the sea
    c.polyline([(cx + 58, cy - 6), (cx + 88, cy - 22), (cx + 108, cy - 44)],
               WHITE, 5)
    c.polyline([(cx - 58, cy + 6), (cx - 88, cy + 24), (cx - 104, cy + 48)],
               WHITE, 5)
    # rain streaks over the land
    for (rx, ry) in ((x0 + 24, 716), (x0 + 44, 736), (x0 + 30, 760),
                     (x0 + 52, 780), (x0 + 26, 806), (x0 + 48, 826)):
        c.line(rx, ry, rx - 6, ry + 12, WHITE, 2)
    c.text_centered(x0 + w / 2, y1 - 20, 1.0, WHITE, "GOPALPUR, INDIA")


def draw_paris(c, x0, w):
    """Mini-story 3: Harris meets Macron -- two flags over the Eiffel Tower."""
    y0, y1 = 700, 850
    c.fill_rect(x0, y0, x0 + w, y1, (232, 226, 208))
    # the two flags, side by side above the tower
    draw_flag_us(c, x0 + 52, 706)
    draw_flag_fr(c, x0 + w - 108, 706)
    # the Eiffel Tower, ink silhouette
    cx = x0 + w / 2
    # legs: two curved sides meeting at the top
    c.polygon([(cx - 74, 850), (cx - 52, 780), (cx - 30, 742),
               (cx - 14, 706), (cx - 8, 706), (cx - 20, 742),
               (cx - 38, 780), (cx - 52, 850)], INK)
    c.polygon([(cx + 74, 850), (cx + 52, 780), (cx + 30, 742),
               (cx + 14, 706), (cx + 8, 706), (cx + 20, 742),
               (cx + 38, 780), (cx + 52, 850)], INK)
    # the three platforms
    c.fill_rect(cx - 58, 796, cx + 58, 802, INK)
    c.fill_rect(cx - 36, 752, cx + 36, 758, INK)
    c.fill_rect(cx - 16, 716, cx + 16, 721, INK)
    # spire
    c.line(cx, 706, cx, 694, INK, 4)
    c.fill_circle(cx, 692, 3, INK)
    # arch between the legs
    c.polygon([(cx - 52, 850), (cx - 44, 812), (cx + 44, 812),
               (cx + 52, 850), (cx + 30, 850), (cx + 28, 828),
               (cx - 28, 828), (cx - 30, 850)], (232, 226, 208))
    c.text_centered(x0 + w / 2, y1 - 20, 1.0, INK, "PARIS")


def draw_bottom_strip(c):
    cols = [(24, 312), (356, 312), (688, 312)]
    tags = ["THE MARKETS", "THE STORM", "PARIS"]
    heads = [("MARKETS", "TUMBLE"),
             ("CYCLONE AKVAN", "HITS INDIA"),
             ("HARRIS MEETS", "MACRON")]
    painters = [draw_markets, draw_cyclone, draw_paris]
    for i, ((x0, w), tag, (h1, h2), paint) in enumerate(
            zip(cols, tags, heads, painters)):
        if i:
            c.fill_rect(x0 - 10, 660, x0 - 8, 990, INK)
        c.text_centered(x0 + w / 2, 668, 1.5, INK, tag)
        paint(c, x0, w)
        c.text_centered(x0 + w / 2, 868, 1.8, INK, h1)
        c.text_centered(x0 + w / 2, 900, 1.8, INK, h2)
    c.fill_rect(24, 640, 1000, 643, INK)
    c.text_centered(W / 2, 992, 1.2, INK, "20 NOVEMBER 2026 \u2014 THE WORLD IN ONE PAGE")


def draw_page():
    c = Canvas(W, H, CREAM)
    # outer frame
    c.fill_rect(0, 0, W, 8, INK)
    c.fill_rect(0, H - 8, W, H, INK)
    c.fill_rect(0, 0, 8, H, INK)
    c.fill_rect(W - 8, 0, W, H, INK)
    draw_masthead(c)
    draw_hero(c)
    draw_bottom_strip(c)
    return c


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    data = png_bytes(draw_page())
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
