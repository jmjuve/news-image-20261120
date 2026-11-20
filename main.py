#!/usr/bin/env python3
"""news-image-20261120 — "Sum up 20 November's world news in one image".

Front-page poster, 1024x1024, pure stdlib (no PIL, no external fonts,
no network). Hand-built 5x7 bitmap capitals font, deterministic PNG
(zlib level 9, no ancillary chunks, no timestamps).

Stories (all verified 20 Nov 2026, see PLAN.md):
  HERO  Russia's overnight ballistic-missile attack on Kyiv — Dnipro
        bridges damaged, Putin's retaliation for the Kerch Bridge strikes.
  MINI  Asian markets tumble (Taiwan -5%+, Nikkei -4.8%).
  MINI  Cyclone Akvan landfall near Gopalpur, India.
  MINI  Kamala Harris meets Emmanuel Macron in Paris.
No 19 Nov story appears anywhere in the image.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

CREAM = (246, 239, 221)
INK = (26, 26, 26)
RED = (193, 39, 45)
NAVY_TOP = (16, 28, 51)
NAVY_HOR = (34, 56, 92)
RIVER = (27, 58, 92)
RIVER_LT = (46, 90, 134)
SKYLINE = (11, 18, 32)
WINDOW = (255, 217, 122)
FIRE_OUT = (200, 40, 30)
FIRE_MID = (244, 140, 6)
FIRE_CORE = (255, 214, 10)
FIRE_HOT = (255, 240, 180)
SMOKE = (107, 114, 128)
SMOKE_LT = (154, 160, 166)
STEEL = (62, 76, 99)
STEEL_DK = (44, 58, 79)
PANEL = (253, 248, 236)
RULE = (201, 191, 168)
SEA = (220, 232, 240)
LAND = (227, 201, 143)
STORM = (29, 53, 87)

# ---------------------------------------------------------------- font ----
# 5x7 bitmap capitals. Each glyph is 7 rows of 5 characters ('#' = ink).
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", "..#..", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    "'": ["..#..", "..#..", "..#..", ".....", ".....", ".....", "....."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ",": [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    "%": ["#...#", "#..#.", "...#.", "..#..", ".#...", ".#..#", "#...#"],
    "/": ["....#", "....#", "...#.", "..#..", "..#..", ".#...", "#...."],
    ":": [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    "(": ["...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"],
    ")": ["##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."],
    "+": [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
}


# -------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            s = (yy * self.w + x0) * 3
            self.px[s:s + len(row)] = row

    def disc(self, cx, cy, r, c):
        if r <= 0:
            return
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = t // 2
        while True:
            self.rect(x0 - r, y0 - r, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polyline(self, pts, c, t=1):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            self.line(x0, y0, x1, y1, c, t)

    def text(self, s, cx, y, scale, color):
        """Draw centred text; cx is the centre x, y the top."""
        adv = 6 * scale
        w = len(s) * adv - scale
        x = cx - w // 2
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for r, row in enumerate(g):
                for cc, bit in enumerate(row):
                    if bit == "#":
                        self.rect(x + cc * scale, y + r * scale,
                                  scale, scale, color)
            x += adv


# -------------------------------------------------------------- pieces ----
def explosion(cv, cx, cy, r):
    for k in range(8):
        a = k * math.pi / 4 + 0.3
        cv.line(cx, cy, cx + int((r + 12) * math.cos(a)),
                cy + int((r + 12) * math.sin(a)), FIRE_MID, 3)
    cv.disc(cx, cy, r, FIRE_OUT)
    cv.disc(cx, cy, int(r * 0.68), FIRE_MID)
    cv.disc(cx, cy, int(r * 0.42), FIRE_CORE)
    cv.disc(cx, cy, int(r * 0.18), FIRE_HOT)


def smoke(cv, cx, cy, r):
    for dx, dy, rr in [(-r, 0, r), (0, -int(r * 0.7), int(r * 0.9)),
                       (int(r * 0.8), -int(r * 0.4), int(r * 0.8))]:
        cv.disc(cx + dx, cy + dy, rr, SMOKE)
        cv.disc(cx + dx - 3, cy + dy - 3, int(rr * 0.6), SMOKE_LT)


def missile(cv, x0, y0, x1, y1):
    cv.line(x0, y0, x1, y1, FIRE_MID, 7)
    cv.line(x0, y0, x1, y1, (255, 233, 168), 3)
    cv.disc(x1, y1, 10, FIRE_MID)
    cv.disc(x1, y1, 5, FIRE_HOT)


def draw_sky(cv):
    # Night gradient in 8 bands, darker at the top.
    bands = 8
    top_y, bot_y = 96, 375
    for i in range(bands):
        f = i / (bands - 1)
        c = tuple(int(NAVY_TOP[k] + (NAVY_HOR[k] - NAVY_TOP[k]) * f)
                  for k in range(3))
        y0 = top_y + (bot_y - top_y) * i // bands
        y1 = top_y + (bot_y - top_y) * (i + 1) // bands
        cv.rect(0, y0, W, y1 - y0, c)
    # Stars, fixed deterministic scatter.
    for i in range(90):
        x = (i * 137 + 53) % W
        y = 100 + (i * 89 + 31) % 220
        cv.rect(x, y, 2 if i % 5 == 0 else 1, 2 if i % 5 == 0 else 1,
                (216, 222, 233))
    # Searchlight beams from the riverbank.
    for bx, tx in [(120, 60), (120, 120), (120, 180)]:
        cv.line(bx, 375, tx, 140, (185, 200, 221), 2)
    for bx, tx in [(900, 860), (900, 920)]:
        cv.line(bx, 375, tx, 150, (185, 200, 221), 2)
    # Caption inside the night scene, left-aligned clear of missile trails.
    cv.text("KYIV, UKRAINE - OVERNIGHT", 173, 108, 2, (232, 236, 242))


def draw_skyline(cv):
    bldgs = [(20, 70, 90), (100, 50, 130), (160, 80, 70), (250, 60, 150),
             (320, 90, 100), (420, 55, 120), (485, 70, 80), (565, 60, 140),
             (635, 85, 95), (730, 55, 125), (795, 75, 75), (880, 60, 110),
             (950, 60, 85)]
    for bx, bw, bh in bldgs:
        cv.rect(bx, 375 - bh, bw, bh, SKYLINE)
        for wy in range(375 - bh + 8, 368, 14):
            for wx in range(bx + 8, bx + bw - 6, 14):
                if (bx + wy + wx) % 3 == 0:
                    cv.rect(wx, wy, 5, 7, WINDOW)


def draw_river(cv):
    cv.rect(0, 375, W, 516 - 375, RIVER)
    for i, y in enumerate([390, 408, 428, 452, 476, 500]):
        x = 20 + (i * 173) % 300
        cv.line(x, y, x + 180 + (i * 97) % 260, y, RIVER_LT, 2)
    # Orange reflections under the burning bridges.
    for x, y, ln in [(470, 500, 60), (300, 460, 44), (760, 430, 40)]:
        cv.line(x, y, x, y + ln, FIRE_MID, 3)


def draw_bridges(cv):
    # Far bridge: thin deck + one arch, high in the frame.
    cv.line(40, 402, 984, 402, (85, 98, 122), 4)
    arc = []
    for i in range(21):
        t = i / 20
        arc.append((40 + int(944 * t), 402 - int(26 * math.sin(t * math.pi))))
    cv.polyline(arc, (85, 98, 122), 3)
    for x in range(120, 960, 80):
        cv.line(x, 402, x, 392, (85, 98, 122), 2)
    # Mid bridge: deck, two pylons, stay cables.
    cv.line(30, 445, 994, 445, STEEL, 6)
    for px in (300, 700):
        cv.rect(px - 4, 398, 8, 47, STEEL_DK)
        for tx in (px - 150, px - 75, px + 75, px + 150):
            cv.line(px, 400, tx, 445, STEEL, 2)
    # Near bridge: DAMAGED — deck in two pieces with a gap, one span
    # tilted down into the river, fire at the break.
    cv.rect(60, 488, 380, 8, (44, 58, 79))
    cv.rect(580, 488, 390, 8, (44, 58, 79))
    cv.line(440, 492, 520, 520, (44, 58, 79), 8)
    for sx in (150, 350, 650, 850):
        cv.rect(sx - 4, 496, 8, 20, (44, 58, 79))
    # Explosions and smoke on the bridges.
    explosion(cv, 510, 478, 26)
    smoke(cv, 500, 438, 16)
    explosion(cv, 300, 432, 18)
    explosion(cv, 760, 392, 15)
    explosion(cv, 180, 362, 16)


def draw_hero(cv):
    draw_sky(cv)
    draw_skyline(cv)
    draw_river(cv)
    draw_bridges(cv)
    missile(cv, 260, 112, 330, 350)
    missile(cv, 600, 100, 690, 340)
    missile(cv, 860, 140, 790, 380)


def draw_masthead(cv):
    cv.text("FRIDAY 20 NOVEMBER 2026", W // 2, 24, 6, INK)
    cv.rect(60, 40, 12, 12, RED)
    cv.rect(W - 72, 40, 12, 12, RED)
    cv.rect(20, 76, W - 40, 4, RED)


def draw_headline(cv):
    cv.text("KYIV'S BRIDGES HIT", W // 2, 526, 9, INK)
    cv.rect(20, 596, W - 40, 3, RED)
    cv.text("OVERNIGHT MISSILE ATTACK DAMAGES DNIPRO CROSSINGS",
            W // 2, 606, 3, INK)
    cv.text("PUTIN'S RETALIATION FOR THE KERCH BRIDGE STRIKES",
            W // 2, 628, 3, (90, 40, 40))


def draw_chart(cv, x0, y0, w, h):
    cv.rect(x0, y0, w, h, PANEL)
    cv.rect(x0, y0, w, 2, INK)
    cv.rect(x0, y0 + h - 2, w, 2, INK)
    cv.rect(x0, y0, 2, h, INK)
    cv.rect(x0 + w - 2, y0, 2, h, INK)
    for gy in (y0 + h // 3, y0 + 2 * h // 3):
        cv.line(x0 + 6, gy, x0 + w - 6, gy, RULE, 1)
    pts = [(x0 + 14, y0 + 22), (x0 + 70, y0 + 30), (x0 + 120, y0 + 26),
           (x0 + 170, y0 + 52), (x0 + 215, y0 + 48), (x0 + 260, y0 + 92),
           (x0 + 300, y0 + 108)]
    cv.polyline(pts, RED, 4)
    ex, ey = pts[-1]
    cv.line(ex, ey, ex - 16, ey - 4, RED, 4)
    cv.line(ex, ey, ex - 6, ey - 16, RED, 4)
    cv.text("ASIA", x0 + w // 2, y0 + h - 26, 2, (90, 40, 40))


def draw_cyclone(cv, x0, y0, w, h):
    cv.rect(x0, y0, w, h, SEA)
    cv.rect(x0, y0, w, 2, INK)
    cv.rect(x0, y0 + h - 2, w, 2, INK)
    cv.rect(x0, y0, 2, h, INK)
    cv.rect(x0 + w - 2, y0, 2, h, INK)
    # Land (India's east coast) along the left edge.
    for yy in range(y0, y0 + h):
        xr = x0 + 90 - (yy - y0) // 3
        if xr > x0:
            cv.rect(x0, yy, xr - x0, 1, LAND)
    # Spiral storm over the coast.
    cx, cy = x0 + w // 2 + 20, y0 + h // 2
    pts = []
    steps = 160
    for i in range(steps + 1):
        a = i / steps * 4 * math.pi
        r = 52 * i / steps
        pts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
    cv.polyline(pts, STORM, 3)
    cv.disc(cx, cy, 7, STORM)
    # Rain streaks.
    for i in range(8):
        rx = x0 + 30 + i * 32
        cv.line(rx, y0 + 12, rx - 8, y0 + 34, STORM, 2)
    cv.text("GOPALPUR", x0 + w // 2, y0 + h - 26, 2, STORM)


def draw_paris(cv, x0, y0, w, h):
    cv.rect(x0, y0, w, h, PANEL)
    cv.rect(x0, y0, w, 2, INK)
    cv.rect(x0, y0 + h - 2, w, 2, INK)
    cv.rect(x0, y0, 2, h, INK)
    cv.rect(x0 + w - 2, y0, 2, h, INK)
    cx = x0 + w // 2
    base = y0 + h - 12
    top = y0 + 14
    # Eiffel Tower silhouette.
    cv.line(cx, top, cx - 34, base, INK, 4)
    cv.line(cx, top, cx + 34, base, INK, 4)
    cv.line(cx, top - 8, cx, top + 4, INK, 3)
    for fy, fw in [(0.30, 34), (0.55, 48), (0.80, 62)]:
        yy = top + int((base - top) * fy)
        cv.line(cx - fw // 2, yy, cx + fw // 2, yy, INK, 3)
    # US flag, left pole.
    fx, fy = x0 + 22, y0 + 18
    cv.line(fx, fy, fx, fy + 62, INK, 2)
    for i in range(7):
        cv.rect(fx + 2, fy + i * 4, 44, 4,
                RED if i % 2 == 0 else CREAM)
    cv.rect(fx + 2, fy, 18, 16, (30, 60, 120))
    for wy in range(fy + 3, fy + 14, 5):
        for wx in range(fx + 5, fx + 17, 5):
            cv.rect(wx, wy, 2, 2, CREAM)
    # French flag, right pole (ink border, then three bands inside).
    gx = x0 + w - 68
    cv.line(gx + 46, fy, gx + 46, fy + 62, INK, 2)
    cv.rect(gx, fy, 45, 28, INK)
    cv.rect(gx + 1, fy + 1, 14, 26, (30, 60, 160))
    cv.rect(gx + 16, fy + 1, 14, 26, CREAM)
    cv.rect(gx + 31, fy + 1, 13, 26, RED)


def draw_minis(cv):
    cv.rect(0, 652, W, 3, INK)
    cols = [(0, 341), (342, 682), (683, 1024)]
    for i, (c0, c1) in enumerate(cols):
        if i:
            cv.rect(c0 - 1, 660, 2, 336, RULE)
    # Column 1 — markets.
    c0, _ = cols[0]
    cv.text("ASIA", c0 + 170, 664, 2, RED)
    draw_chart(cv, c0 + 10, 692, 321, 140)
    cv.text("MARKETS", c0 + 170, 846, 5, INK)
    cv.text("TUMBLE", c0 + 170, 884, 5, RED)
    cv.text("TAIWAN DOWN 5%", c0 + 170, 922, 3, INK)
    cv.text("NIKKEI -4.8%", c0 + 170, 944, 3, INK)
    # Column 2 — cyclone.
    c0, _ = cols[1]
    cv.text("INDIA", c0 + 170, 664, 2, RED)
    draw_cyclone(cv, c0 + 10, 692, 321, 140)
    cv.text("CYCLONE AKVAN", c0 + 170, 846, 4, INK)
    cv.text("HITS INDIA", c0 + 170, 880, 4, INK)
    cv.text("LANDFALL NEAR", c0 + 170, 922, 3, INK)
    cv.text("GOPALPUR", c0 + 170, 944, 3, INK)
    # Column 3 — Paris.
    c0, _ = cols[2]
    cv.text("PARIS", c0 + 170, 664, 2, RED)
    draw_paris(cv, c0 + 10, 692, 321, 140)
    cv.text("HARRIS MEETS", c0 + 170, 846, 4, INK)
    cv.text("MACRON", c0 + 170, 880, 4, RED)
    cv.text("COURTESY MEETING", c0 + 170, 922, 3, INK)
    cv.text("IN PARIS", c0 + 170, 944, 3, INK)


def draw_footer(cv):
    cv.rect(20, 972, W - 40, 2, INK)
    cv.text("THE DAY'S WORLD NEWS - IN ONE IMAGE", W // 2, 982, 2, INK)


# -------------------------------------------------------------- png out ----
def write_png(path, cv):
    raw = b"".join(
        b"\x00" + bytes(cv.px[y * W * 3:(y + 1) * W * 3])
        for y in range(H))
    comp = zlib.compress(raw, 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    cv = Canvas(W, H, CREAM)
    draw_masthead(cv)
    draw_hero(cv)
    draw_headline(cv)
    draw_minis(cv)
    draw_footer(cv)
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if outdir:
        out = os.path.join(outdir, "entry.png")
    else:
        out = os.path.join(here, "out", "entry.png")
    n = write_png(out, cv)
    print("wrote %s (%d bytes)" % (out, n))


if __name__ == "__main__":
    main()
