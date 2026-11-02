#!/usr/bin/env python3
"""Shared drawing helpers and the first ten filled Petrel list icons.

Icons are drawn at 8x size and downsampled. Anti-aliased edges are blended onto
Petrel's Graphite background (0x2125); almost transparent pixels become pure black,
which Petrel's icon drawing filters out as transparent.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

K = 8
BG = (33, 37, 41)          # graphite_theme.BACKGROUND_RGB (0x2125)
CYAN = (46, 196, 230)
BLUE = (58, 143, 217)
BLUE_LIGHT = (150, 205, 245)
TEAL = (57, 180, 147)
TEAL_DARK = (38, 140, 112)
AMBER = (242, 193, 78)
AMBER_DARK = (205, 150, 45)
ORANGE = (240, 128, 52)
RED = (232, 80, 72)
ICE = (127, 211, 255)
WHITE = (236, 241, 245)
STEEL = (125, 142, 160)
STEEL_LIGHT = (170, 185, 200)
DARK = BG


class Pen:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w * K, h * K), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def p(self, pts):
        return [(x * K, y * K) for x, y in pts]

    def poly(self, pts, fill):
        self.d.polygon(self.p(pts), fill=fill)

    def rect(self, x0, y0, x1, y1, fill, r=0):
        box = [x0 * K, y0 * K, x1 * K, y1 * K]
        if r:
            self.d.rounded_rectangle(box, radius=r * K, fill=fill)
        else:
            self.d.rectangle(box, fill=fill)

    def circle(self, cx, cy, r, fill=None, outline=None, width=0):
        self.d.ellipse([(cx - r) * K, (cy - r) * K, (cx + r) * K, (cy + r) * K],
                       fill=fill, outline=outline, width=int(width * K))

    def line(self, pts, fill, width):
        self.d.line(self.p(pts), fill=fill, width=int(width * K), joint="curve")
        for x, y in (pts[0], pts[-1]):     # round line caps
            self.circle(x, y, width / 2, fill=fill)

    def arc(self, cx, cy, r, start, end, fill, width):
        self.d.arc([(cx - r) * K, (cy - r) * K, (cx + r) * K, (cy + r) * K],
                   start, end, fill=fill, width=int(width * K))

    def finish(self):
        small = self.im.resize((self.w, self.h), Image.LANCZOS)
        out = Image.new("RGB", (self.w, self.h), (0, 0, 0))
        src, dst = small.load(), out.load()
        for y in range(self.h):
            for x in range(self.w):
                r, g, b, a = src[x, y]
                if a < 90:
                    continue                      # stays black = transparent
                f = a / 255
                dst[x, y] = tuple(round(c * f + bg * (1 - f)) for c, bg in zip((r, g, b), BG))
        return out


def icon_file():                       # 014 print file
    p = Pen(20, 20)
    p.poly([(3.5, 1.5), (12.5, 1.5), (17, 6), (17, 18.5), (3.5, 18.5)], BLUE)
    p.poly([(12.5, 1.5), (12.5, 6), (17, 6)], BLUE_LIGHT)
    cx, cy, r = 10.25, 12.3, 4.1
    T, UR, DR = (cx, cy - r), (cx + .87 * r, cy - .5 * r), (cx + .87 * r, cy + .5 * r)
    B, DL, UL, C = (cx, cy + r), (cx - .87 * r, cy + .5 * r), (cx - .87 * r, cy - .5 * r), (cx, cy)
    p.poly([T, UR, C, UL], WHITE)
    p.poly([UL, C, B, DL], BLUE_LIGHT)
    p.poly([C, UR, DR, B], (205, 228, 245))
    return p.finish()


def icon_folder():                     # 100 folder (20x18)
    p = Pen(20, 18)
    p.poly([(1.5, 2.5), (7.5, 2.5), (9.5, 4.5), (18.5, 4.5), (18.5, 15.5), (1.5, 15.5)], AMBER_DARK)
    p.rect(1.5, 6.5, 18.5, 15.5, AMBER, r=1.2)
    return p.finish()


def icon_move():                       # 017 move axes
    p = Pen(20, 20)
    p.line([(10, 3.5), (10, 16.5)], CYAN, 2.4)
    p.line([(3.5, 10), (16.5, 10)], CYAN, 2.4)
    for tip, a, b in (((10, 0.8), (6.6, 4.6), (13.4, 4.6)), ((10, 19.2), (6.6, 15.4), (13.4, 15.4)),
                      ((0.8, 10), (4.6, 6.6), (4.6, 13.4)), ((19.2, 10), (15.4, 6.6), (15.4, 13.4))):
        p.poly([tip, a, b], CYAN)
    p.circle(10, 10, 2.3, fill=WHITE)
    return p.finish()


def icon_motor_off():                  # 152 motors off
    p = Pen(20, 20)
    p.rect(2.5, 2.5, 17.5, 17.5, STEEL, r=2.6)
    for x, y in ((4.6, 4.6), (15.4, 4.6), (4.6, 15.4), (15.4, 15.4)):
        p.circle(x, y, 0.9, fill=STEEL_LIGHT)
    p.circle(10, 10, 4.2, fill=(70, 82, 96))
    p.circle(10, 10, 1.6, fill=WHITE)
    p.line([(3, 17), (17, 3)], DARK, 4.4)
    p.line([(3, 17), (17, 3)], RED, 2.4)
    return p.finish()


def icon_home():                       # 018 Home
    p = Pen(20, 20)
    p.rect(13.3, 2.5, 15.6, 7, TEAL_DARK)
    p.rect(3.6, 8.4, 16.4, 18.5, TEAL, r=0.8)
    p.poly([(10, 1.2), (19.3, 9.6), (0.7, 9.6)], TEAL_DARK)
    p.rect(8.2, 12, 11.8, 18.5, DARK, r=0.6)
    return p.finish()


def icon_z_offset():                   # 012 Z offset (18x18, also status bar)
    p = Pen(18, 18)
    p.rect(1.5, 1.2, 16.5, 3.2, STEEL_LIGHT, r=0.8)
    p.rect(1.5, 14.8, 16.5, 16.8, STEEL_LIGHT, r=0.8)
    p.line([(9, 6.5), (9, 11.5)], AMBER, 2.2)
    p.poly([(9, 4.2), (5.8, 7.6), (12.2, 7.6)], AMBER)
    p.poly([(9, 13.8), (5.8, 10.4), (12.2, 10.4)], AMBER)
    return p.finish()


def flame(p, cx, base, h, w, fill):
    pts = []
    for i in range(41):                # drop shape: round bottom, pointed top
        t = i / 40 * 2 * math.pi
        x = math.sin(t) * w / 2
        y = -math.cos(t)
        y = y * (h * 0.62 if y > 0 else h * 0.38)
        x *= (1 - max(0, y / (h * 0.62)) ** 1.6) if y > 0 else 1
        pts.append((cx + x, base - h * 0.38 - y))
    p.poly(pts, fill)


def icon_preheat():                    # 162 preheat
    p = Pen(20, 20)
    flame(p, 10, 19, 18, 12.5, ORANGE)
    flame(p, 10, 18.6, 9.5, 6.4, AMBER)
    return p.finish()


def icon_cooldown():                   # 020 cooldown
    p = Pen(20, 20)
    for k in range(3):
        a = math.radians(90 + 60 * k)
        dx, dy = math.cos(a) * 8.3, math.sin(a) * 8.3
        p.line([(10 - dx, 10 - dy), (10 + dx, 10 + dy)], ICE, 2.0)
    for k in range(6):
        a = math.radians(90 + 60 * k)
        bx, by = 10 + math.cos(a) * 5.4, 10 + math.sin(a) * 5.4
        for s in (-1, 1):
            b = a + s * math.radians(50)
            p.line([(bx, by), (bx + math.cos(b) * 2.6, by + math.sin(b) * 2.6)], ICE, 1.6)
    p.circle(10, 10, 1.8, fill=WHITE)
    return p.finish()


def icon_probe():                      # 157 probe calibration (paper test)
    p = Pen(20, 20)
    p.rect(5.5, 1.2, 14.5, 6.6, STEEL_LIGHT, r=1.2)
    p.poly([(6.8, 6.6), (13.2, 6.6), (10, 11)], ORANGE)
    p.rect(2.5, 12.4, 17.5, 13.8, WHITE, r=0.4)
    p.rect(1, 15.3, 19, 18.4, TEAL, r=1)
    return p.finish()


def icon_screw():                      # 159 bed screws
    p = Pen(20, 20)
    p.arc(10, 10, 8.4, 200, 340, TEAL, 1.9)
    p.poly([(17.9, 7.3), (19.6, 3.6), (15.3, 4.6)], TEAL)
    p.circle(10, 11.5, 5.8, fill=AMBER)
    p.line([(7, 11.5), (13, 11.5)], DARK, 1.7)
    p.line([(10, 8.5), (10, 14.5)], DARK, 1.7)
    return p.finish()


ICONS = {14: icon_file, 100: icon_folder, 17: icon_move, 152: icon_motor_off, 18: icon_home,
         12: icon_z_offset, 162: icon_preheat, 20: icon_cooldown, 157: icon_probe, 159: icon_screw}
