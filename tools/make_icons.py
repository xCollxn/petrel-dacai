#!/usr/bin/env python3
"""Render all filled colour icons (74 redrawn Petrel symbols + 3 new maintenance icons).

Usage: make_icons.py <out_dir> [--dejavu-dir DIR]
Writes NNN.png files. Merge them over Petrel's assets/icons/NNN.jpg and build the
library with build_zico.py (see make_sd_package.py).
X/Y/Z/E badges need DejaVuSans-Bold.ttf (see fetch_dejavu.sh).
"""
import math
import os
import sys
from pathlib import Path

from PIL import ImageFont

from icons_core import (AMBER, AMBER_DARK, BLUE, BLUE_LIGHT, CYAN, DARK, ICONS, K, ORANGE, Pen,
                        RED, STEEL, STEEL_LIGHT, TEAL, TEAL_DARK, WHITE)

PURPLE = (167, 139, 250)
PURPLE_DARK = (124, 98, 214)
GREEN = (72, 199, 116)
PINK = (240, 98, 146)
GRAY = (98, 110, 124)
LETTER_FONT = os.path.join(os.environ.get("DEJAVU_DIR", "fonts/dejavu"), "DejaVuSans-Bold.ttf")


def letter(p, ch, cx, cy, size, fill):
    f = ImageFont.truetype(LETTER_FONT, int(size * K))
    p.d.text((cx * K, cy * K), ch, font=f, fill=fill, anchor="mm")


def fan_blades(p, cx, cy, r, angle, fill, hub=WHITE):
    for k in range(4):
        a = math.radians(angle + 90 * k)
        pts = [(cx, cy)]
        for i in range(1, 16):                     # curved blade
            t = i / 15
            ang = a - 0.55 + 1.1 * t
            rr = r * (0.35 + 0.65 * math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.5)
            pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        p.poly(pts, fill)
    p.circle(cx, cy, r * 0.24, fill=hub)


def speaker(p, fill, ox=0):
    p.rect(2 + ox, 7, 6 + ox, 13, fill, r=0.6)
    p.poly([(5.5 + ox, 7), (11 + ox, 2.5), (11 + ox, 17.5), (5.5 + ox, 13)], fill)


def i_hotend():                         # 009 hotend (18x18)
    p = Pen(18, 18)
    p.rect(3.5, 1, 14.5, 6.5, STEEL_LIGHT, r=1)
    p.rect(5.5, 6.5, 12.5, 9.5, ORANGE)
    p.poly([(5.5, 9.5), (12.5, 9.5), (9, 15)], ORANGE)
    p.circle(9, 16.3, 1.2, fill=AMBER)
    return p.finish()


def i_bed():                            # 010 heated bed (18x18)
    p = Pen(18, 18)
    for x in (4.5, 9, 13.5):
        p.line([(x, 2), (x - 1.2, 4.5), (x, 7), (x - 1.2, 9.5)], ORANGE, 1.5)
    p.rect(1, 11.5, 17, 15, AMBER, r=1)
    p.rect(3, 15, 4.6, 17, AMBER_DARK)
    p.rect(13.4, 15, 15, 17, AMBER_DARK)
    return p.finish()


def i_speed():                          # 011 speed (18x18)
    p = Pen(18, 18)
    for y, x0, col in ((4.5, 1.5, (110, 170, 200)), (9, 3.5, CYAN), (13.5, 1.5, (110, 170, 200))):
        p.line([(x0, y), (x0 + 7, y)], col, 1.8)
    p.poly([(10.5, 3), (17, 9), (10.5, 15)], CYAN)
    return p.finish()


def i_clock(size=24):                   # 015 print time (24x24)
    p = Pen(size, size)
    c, r = size / 2, size / 2 - 1.5
    p.circle(c, c, r, fill=BLUE)
    p.circle(c, c, r - 2.2, fill=(30, 60, 100))
    for k in range(12):
        a = math.radians(30 * k)
        p.circle(c + math.cos(a) * (r - 3.6), c + math.sin(a) * (r - 3.6), 0.55, fill=BLUE_LIGHT)
    p.line([(c, c), (c, c - r + 5)], WHITE, 1.8)
    p.line([(c, c), (c + r - 6.5, c + 1.5)], AMBER, 1.8)
    p.circle(c, c, 1.4, fill=WHITE)
    return p.finish()


def i_chevron():                        # 016 more
    p = Pen(20, 20)
    p.line([(7.5, 4), (13.5, 10), (7.5, 16)], WHITE, 2.6)
    return p.finish()


def i_set_home():                       # 019 reference point
    p = Pen(20, 20)
    p.circle(10, 10, 8, fill=TEAL)
    p.circle(10, 10, 5.6, fill=DARK)
    p.circle(10, 10, 3.2, fill=TEAL)
    for a, b in (((10, 0.5), (10, 4)), ((10, 16), (10, 19.5)), ((0.5, 10), (4, 10)), ((16, 10), (19.5, 10))):
        p.line([a, b], WHITE, 1.6)
    return p.finish()


def i_axis(ch, color):                  # 021-024 X/Y/Z/E
    def draw():
        p = Pen(20, 20)
        p.rect(1.5, 1.5, 18.5, 18.5, color, r=3.5)
        letter(p, ch, 10, 10.6, 13, WHITE)
        return p.finish()
    return draw


def i_emergency():                      # 025 emergency-stop tag
    p = Pen(20, 20)
    pts = [(10 + 9 * math.cos(math.radians(22.5 + 45 * k)), 10 + 9 * math.sin(math.radians(22.5 + 45 * k)))
           for k in range(8)]
    p.poly(pts, RED)
    p.rect(8.8, 4.5, 11.2, 11.5, WHITE, r=1)
    p.circle(10, 14.6, 1.4, fill=WHITE)
    return p.finish()


def i_thermo():                         # 026 temperature
    p = Pen(20, 20)
    p.rect(7.3, 1.2, 12.7, 13, STEEL_LIGHT, r=2.7)
    p.circle(10, 15, 4.6, fill=STEEL_LIGHT)
    p.rect(8.9, 5, 11.1, 14, RED, r=1)
    p.circle(10, 15, 3.1, fill=RED)
    for y in (4, 6.5, 9):
        p.line([(13.8, y), (15.8, y)], STEEL_LIGHT, 1.1)
    return p.finish()


def i_save():                           # 027 save
    p = Pen(20, 20)
    p.poly([(2, 2), (15, 2), (18, 5), (18, 18), (2, 18)], BLUE)
    p.rect(5, 2, 13.5, 7.5, BLUE_LIGHT, r=0.6)
    p.rect(10.5, 3, 12.5, 6.5, BLUE)
    p.rect(5, 11, 15, 18, WHITE, r=0.8)
    p.line([(7, 13.6), (13, 13.6)], BLUE_LIGHT, 1.1)
    return p.finish()


def i_download():                       # 028 read / stock configuration
    p = Pen(20, 20)
    p.rect(2, 13, 18, 18.5, TEAL_DARK, r=1.6)
    p.line([(10, 1.5), (10, 9)], TEAL, 2.6)
    p.poly([(10, 14), (4.8, 8.2), (15.2, 8.2)], TEAL)
    p.circle(15, 15.8, 1, fill=WHITE)
    return p.finish()


def i_info():                           # 029 Info
    p = Pen(20, 20)
    p.circle(10, 10, 9, fill=BLUE)
    p.circle(10, 5.6, 1.6, fill=WHITE)
    p.rect(8.6, 8.4, 11.4, 15.5, WHITE, r=1)
    return p.finish()


def i_fan(angle=0):                     # 030 fan + 166-173 animation
    def draw():
        p = Pen(20, 20)
        p.circle(10, 10, 9.4, fill=(36, 66, 86))
        fan_blades(p, 10, 10, 8.3, angle, CYAN)
        return p.finish()
    return draw


def i_spool():                          # 033 spool
    p = Pen(20, 20)
    p.circle(10, 10, 9, fill=AMBER_DARK)
    p.circle(10, 10, 6.6, fill=PINK)
    for r in (5.2, 3.9):
        p.circle(10, 10, r, outline=(255, 150, 185), width=0.6)
    p.circle(10, 10, 2.6, fill=AMBER)
    p.circle(10, 10, 1.2, fill=DARK)
    return p.finish()


def i_tag_add():                        # 034 assign tag
    p = Pen(20, 20)
    p.poly([(2, 3.5), (10, 3.5), (18.5, 12), (12, 18.5), (2, 9.5)], AMBER)
    p.circle(6, 7.4, 1.5, fill=DARK)
    p.line([(11, 9), (11, 15)], WHITE, 1.8)
    p.line([(8, 12), (14, 12)], WHITE, 1.8)
    return p.finish()


def i_trash():                          # 035 remove
    p = Pen(20, 20)
    p.rect(7.5, 1.2, 12.5, 3.6, RED, r=0.8)
    p.rect(2.5, 3.2, 17.5, 5.6, RED, r=1)
    p.poly([(4, 6.5), (16, 6.5), (15, 18.5), (5, 18.5)], RED)
    for x in (7.5, 10, 12.5):
        p.line([(x, 9), (x, 16)], (255, 190, 185), 1.1)
    return p.finish()


def i_arrow_right():                    # 036 next
    p = Pen(20, 20)
    p.circle(10, 10, 9, fill=TEAL)
    p.line([(5, 10), (12, 10)], WHITE, 2.2)
    p.poly([(15.5, 10), (10.5, 5.5), (10.5, 14.5)], WHITE)
    return p.finish()


def i_retry():                          # 037 retry
    p = Pen(20, 20)
    p.arc(10, 10.5, 7, 220, 500, TEAL, 2.6)
    p.poly([(1.2, 6.5), (6.8, 2.2), (7.6, 8.8)], TEAL)
    return p.finish()


def i_software():                       # 054 Software
    p = Pen(20, 20)
    p.rect(1.5, 2.5, 18.5, 17.5, PURPLE_DARK, r=2.5)
    p.line([(7.5, 6.5), (4.5, 10), (7.5, 13.5)], WHITE, 1.7)
    p.line([(12.5, 6.5), (15.5, 10), (12.5, 13.5)], WHITE, 1.7)
    p.line([(11, 5.5), (9, 14.5)], (210, 200, 255), 1.4)
    return p.finish()


def i_power():                          # 055 power
    p = Pen(20, 20)
    p.arc(10, 10.8, 7.2, 300, 600, RED, 2.6)
    p.line([(10, 1.5), (10, 9.5)], RED, 2.6)
    return p.finish()


def i_swap():                           # 096 interface
    p = Pen(20, 20)
    p.line([(2.5, 6.5), (13, 6.5)], CYAN, 2.2)
    p.poly([(18, 6.5), (13, 2.3), (13, 10.7)], CYAN)
    p.line([(7, 13.5), (17.5, 13.5)], BLUE_LIGHT, 2.2)
    p.poly([(2, 13.5), (7, 9.3), (7, 17.7)], BLUE_LIGHT)
    return p.finish()


def i_plug():                           # 097 serial port
    p = Pen(20, 20)
    p.rect(6.3, 1, 8.3, 6, STEEL_LIGHT)
    p.rect(11.7, 1, 13.7, 6, STEEL_LIGHT)
    p.rect(3.5, 5.5, 16.5, 11.5, AMBER, r=1.5)
    p.poly([(5.5, 11.5), (14.5, 11.5), (12, 15), (8, 15)], AMBER_DARK)
    p.rect(8.9, 14.5, 11.1, 19, STEEL_LIGHT)
    return p.finish()


def i_chip():                           # 101 MCU
    p = Pen(20, 20)
    for k in range(3):
        o = 6.5 + 3.5 * k
        for a, b in (((o, 0.8), (o, 4)), ((o, 16), (o, 19.2)), ((0.8, o), (4, o)), ((16, o), (19.2, o))):
            p.line([a, b], STEEL_LIGHT, 1.3)
    p.rect(3.5, 3.5, 16.5, 16.5, TEAL, r=2)
    p.rect(7, 7, 13, 13, TEAL_DARK, r=1)
    p.circle(6, 6, 0.9, fill=WHITE)
    return p.finish()


def i_machine():                        # 102 machine
    p = Pen(20, 20)
    p.rect(1.5, 1.5, 18.5, 18.5, STEEL, r=2)
    p.rect(3.8, 3.8, 16.2, 14.6, DARK, r=0.8)
    p.rect(4, 4.5, 16, 6, STEEL_LIGHT)
    p.rect(8, 4, 12, 7.5, ORANGE, r=0.5)
    p.poly([(8.8, 7.5), (11.2, 7.5), (10, 9.4)], ORANGE)
    p.rect(6.5, 11.2, 13.5, 14.6, TEAL)
    p.rect(3, 15.8, 17, 17, STEEL_LIGHT)
    return p.finish()


def i_host():                           # 103 host (monitor)
    p = Pen(20, 20)
    p.rect(1, 2, 19, 14.5, STEEL_LIGHT, r=1.6)
    p.rect(2.8, 3.8, 17.2, 12.7, BLUE, r=0.6)
    p.poly([(3.5, 12), (8, 7), (11, 10), (13.5, 8), (17, 12)], BLUE_LIGHT)
    p.rect(8.5, 14.5, 11.5, 17, STEEL)
    p.rect(5, 17, 15, 18.8, STEEL_LIGHT, r=0.8)
    return p.finish()


def i_check_circle():                   # 104 check
    p = Pen(20, 20)
    p.circle(10, 10, 9, fill=GREEN)
    p.line([(5.5, 10.3), (8.6, 13.4), (14.6, 6.8)], WHITE, 2.2)
    return p.finish()


def i_pulse():                          # 105 diagnostics
    p = Pen(20, 20)
    p.rect(1, 2.5, 19, 17.5, (70, 44, 62), r=2.5)
    p.line([(2.5, 10.5), (6, 10.5), (8, 5), (11, 15.5), (13, 8.5), (14.6, 10.5), (17.5, 10.5)], PINK, 1.8)
    return p.finish()


def bulb(p, glass, base=STEEL_LIGHT, rays=False):
    if rays:
        for a in (200, 240, 270, 300, 340):
            r = math.radians(a)
            p.line([(10 + math.cos(r) * 7.8, 8 + math.sin(r) * 7.8),
                    (10 + math.cos(r) * 9.6, 8 + math.sin(r) * 9.6)], AMBER, 1.2)
    p.circle(10, 8, 6.0, fill=glass)
    p.poly([(6.6, 11.3), (13.4, 11.3), (12.5, 14), (7.5, 14)], glass)
    p.rect(7.3, 14, 12.7, 16.2, base, r=0.6)
    p.rect(8.3, 16.6, 11.7, 18.6, base, r=0.6)


def i_idea():                           # 106 recommendations
    p = Pen(20, 20)
    bulb(p, AMBER)
    p.line([(8.6, 9.5), (10, 7), (11.4, 9.5)], (255, 245, 200), 1.1)
    return p.finish()


def i_calendar():                       # 107 care schedule
    p = Pen(20, 20)
    p.rect(1.5, 3, 18.5, 18.5, WHITE, r=2.2)
    p.rect(1.5, 3, 18.5, 7.5, RED, r=2.2)
    p.rect(1.5, 5.5, 18.5, 7.5, RED)
    for x in (6, 14):
        p.rect(x - 0.9, 1, x + 0.9, 5, STEEL)
    for r_ in range(2):
        for c in range(3):
            p.rect(4.5 + c * 4, 9.8 + r_ * 4, 6.8 + c * 4, 12 + r_ * 4,
                   BLUE if (r_, c) != (1, 2) else RED, r=0.4)
    return p.finish()


def i_wifi(level):                      # 108-110 Wi-Fi
    def draw():
        p = Pen(20, 20)
        for k, r in enumerate((5.0, 9.5, 14.0)):
            p.arc(10, 17.5, r, 225, 315, CYAN if k < level else GRAY, 2.4)
        p.circle(10, 17, 1.9, fill=CYAN)
        return p.finish()
    return draw


def i_checkbox(checked):                # 140/141
    def draw():
        p = Pen(20, 20)
        if checked:
            p.rect(2, 2, 18, 18, TEAL, r=3.5)
            p.line([(5.6, 10.2), (8.7, 13.3), (14.5, 6.8)], WHITE, 2.2)
        else:
            p.rect(2, 2, 18, 18, STEEL, r=3.5)
            p.rect(3.8, 3.8, 16.2, 16.2, DARK, r=2.2)
        return p.finish()
    return draw


def i_light():                          # 143 light
    p = Pen(20, 20)
    bulb(p, AMBER, rays=True)
    return p.finish()


def sun(p, cx, cy, r, ray, fill):
    for k in range(8):
        a = math.radians(45 * k)
        p.line([(cx + math.cos(a) * (r + 1.6), cy + math.sin(a) * (r + 1.6)),
                (cx + math.cos(a) * (r + 1.6 + ray), cy + math.sin(a) * (r + 1.6 + ray))], fill, 1.6)
    p.circle(cx, cy, r, fill=fill)


def i_brightness():                     # 144 brightness
    p = Pen(20, 20)
    sun(p, 10, 10, 4.4, 2.6, AMBER)
    return p.finish()


def i_dim():                            # 145 dim brightness
    p = Pen(20, 20)
    sun(p, 10, 10, 3.6, 1.6, (176, 150, 90))
    return p.finish()


def i_moon():                           # 146 idle dim
    p = Pen(20, 20)
    p.circle(9.5, 10.5, 7.8, fill=PURPLE)
    p.d.ellipse([(13.8 - 6.4) * K, (6.2 - 6.4) * K, (13.8 + 6.4) * K, (6.2 + 6.4) * K], fill=(0, 0, 0, 0))
    for x, y, r in ((16, 13, 1.1), (17.8, 9.2, 0.7)):
        p.circle(x, y, r, fill=(220, 210, 255))
    return p.finish()


def i_buzzer():                         # 147 buzzer
    p = Pen(20, 20)
    speaker(p, PURPLE, ox=1)
    p.arc(11.5, 10, 4.2, 300, 420, PURPLE, 1.7)
    return p.finish()


def i_volume():                         # 148 volume
    p = Pen(20, 20)
    speaker(p, PURPLE)
    p.arc(10.5, 10, 3.8, 300, 420, PURPLE, 1.6)
    p.arc(10.5, 10, 7.2, 305, 415, PURPLE, 1.6)
    return p.finish()


def i_click():                          # 149 click tone
    p = Pen(20, 20)
    p.circle(10, 11.5, 6.4, fill=PURPLE_DARK)
    p.circle(10, 11.5, 3.4, fill=PURPLE)
    for a in (230, 270, 310):
        r = math.radians(a)
        p.line([(10 + math.cos(r) * 7.4, 10.5 + math.sin(r) * 7.4),
                (10 + math.cos(r) * 9.4, 10.5 + math.sin(r) * 9.4)], (210, 200, 255), 1.5)
    return p.finish()


def i_encoder():                        # 150 encoder tone
    p = Pen(20, 20)
    p.circle(10, 10, 6.5, fill=PURPLE_DARK)
    for k in range(12):
        a = math.radians(30 * k)
        p.circle(10 + math.cos(a) * 6.5, 10 + math.sin(a) * 6.5, 1.0, fill=PURPLE_DARK)
    p.circle(10, 10, 4.2, fill=PURPLE)
    p.line([(10, 10), (10, 6.6)], WHITE, 1.5)
    p.arc(10, 10, 9.2, 200, 250, (210, 200, 255), 1.3)
    p.arc(10, 10, 9.2, 290, 340, (210, 200, 255), 1.3)
    return p.finish()


def i_motion():                         # 151 motion
    p = Pen(20, 20)
    p.line([(2.5, 2), (2.5, 17.5), (18, 17.5)], STEEL_LIGHT, 1.6)
    p.line([(4.5, 15), (8, 12.5), (11, 13.5), (15.5, 6)], CYAN, 2.0)
    p.poly([(18.4, 1.8), (13.4, 3.8), (17.4, 7.4)], CYAN)
    return p.finish()


def i_velocity():                       # 153 velocity (gauge)
    p = Pen(20, 20)
    p.arc(10, 12, 8, 180, 360, STEEL, 3.2)
    p.arc(10, 12, 8, 180, 285, CYAN, 3.2)
    p.line([(10, 12), (14.6, 6.8)], WHITE, 1.8)
    p.circle(10, 12, 2, fill=WHITE)
    p.rect(3, 15.5, 17, 17.2, STEEL, r=0.8)
    return p.finish()


def i_accel():                          # 154 acceleration
    p = Pen(20, 20)
    pts = [(2 + 14 * t, 18 - 14.5 * t ** 2.2) for t in [i / 16 for i in range(15)]]
    p.line(pts, ORANGE, 2.2)
    p.poly([(17.8, 1.2), (13, 3.6), (17.2, 7.2)], ORANGE)
    p.line([(2, 18.4), (18, 18.4)], STEEL_LIGHT, 1.2)
    return p.finish()


def i_corner():                         # 155 corner speed
    p = Pen(20, 20)
    p.line([(3.5, 18), (3.5, 9), (5.2, 5.2), (9, 3.5), (13.5, 3.5)], TEAL, 2.4)
    p.poly([(18.8, 3.5), (13.5, -0.6), (13.5, 7.6)], TEAL)
    p.circle(5, 5, 1.3, fill=AMBER)
    return p.finish()


def i_ratio():                          # 156 Cruise Ratio
    p = Pen(20, 20)
    box = [(10 - 8.6) * K, (10 - 8.6) * K, (10 + 8.6) * K, (10 + 8.6) * K]
    p.circle(10, 10, 8.6, fill=STEEL)
    p.d.pieslice(box, -90, 130, fill=CYAN)
    p.circle(10, 10, 4, fill=DARK)
    return p.finish()


def grid(p, color, x0=2, y0=3, x1=18, y1=17):
    p.rect(x0, y0, x1, y1, color, r=1.2)
    dx, dy = (x1 - x0) / 3, (y1 - y0) / 3
    for i in range(3):
        for j in range(3):
            p.rect(x0 + 1.2 + i * dx, y0 + 1.2 + j * dy, x0 + (i + 1) * dx - 0.4, y0 + (j + 1) * dy - 0.4,
                   DARK, r=0.3)


def i_mesh_profile():                   # 158 mesh profile
    p = Pen(20, 20)
    grid(p, TEAL, 1.5, 3, 15.5, 17)
    p.poly([(13, 1), (19, 1), (19, 12), (16, 9.5), (13, 12)], AMBER)
    return p.finish()


def i_level():                          # 160 calculate level
    p = Pen(20, 20)
    p.rect(1, 6, 19, 14, AMBER, r=2.5)
    p.rect(5.5, 7.8, 14.5, 12.2, (190, 235, 120), r=2)
    p.circle(10, 10, 1.6, fill=WHITE)
    p.line([(7.8, 7.8), (7.8, 12.2)], AMBER_DARK, 0.9)
    p.line([(12.2, 7.8), (12.2, 12.2)], AMBER_DARK, 0.9)
    return p.finish()


def i_sound_off():                      # 161 sound off
    p = Pen(20, 20)
    speaker(p, GRAY)
    p.line([(13, 7), (18, 13)], RED, 2)
    p.line([(18, 7), (13, 13)], RED, 2)
    return p.finish()


def i_flow():                           # 163 flow (drop)
    p = Pen(20, 20)
    pts = []
    for i in range(41):
        t = i / 40 * 2 * math.pi
        x, y = math.sin(t), -math.cos(t)
        if y > 0:
            x *= (1 - y) ** 0.9
            y *= 1.55
        pts.append((10 + x * 6.4, 12.4 - y * 6.4))
    p.poly(pts, BLUE)
    p.arc(10, 12.4, 3.6, 100, 170, BLUE_LIGHT, 1.4)
    return p.finish()


def i_active_mesh():                    # 164 active mesh
    p = Pen(20, 20)
    grid(p, TEAL, 1, 3, 15, 17)
    p.circle(15, 14.5, 4.6, fill=GREEN)
    p.line([(12.8, 14.6), (14.4, 16.2), (17.2, 13)], WHITE, 1.5)
    return p.finish()


def i_mesh_cal():                       # 165 mesh calibrate
    p = Pen(20, 20)
    grid(p, TEAL, 1, 7, 19, 19)
    p.rect(7, 0.6, 13, 3.2, STEEL_LIGHT, r=0.6)
    p.poly([(7.8, 3.2), (12.2, 3.2), (10, 6.6)], ORANGE)
    return p.finish()


ALL = dict(ICONS)
ALL.update({
    9: i_hotend, 10: i_bed, 11: i_speed, 15: i_clock, 16: i_chevron, 19: i_set_home,
    21: i_axis("X", RED), 22: i_axis("Y", GREEN), 23: i_axis("Z", BLUE), 24: i_axis("E", ORANGE),
    25: i_emergency, 26: i_thermo, 27: i_save, 28: i_download, 29: i_info, 30: i_fan(0),
    33: i_spool, 34: i_tag_add, 35: i_trash, 36: i_arrow_right, 37: i_retry, 54: i_software,
    55: i_power, 96: i_swap, 97: i_plug, 101: i_chip, 102: i_machine, 103: i_host,
    104: i_check_circle, 105: i_pulse, 106: i_idea, 107: i_calendar,
    108: i_wifi(1), 109: i_wifi(2), 110: i_wifi(3), 140: i_checkbox(False), 141: i_checkbox(True),
    143: i_light, 144: i_brightness, 145: i_dim, 146: i_moon, 147: i_buzzer, 148: i_volume,
    149: i_click, 150: i_encoder, 151: i_motion, 153: i_velocity, 154: i_accel, 155: i_corner,
    156: i_ratio, 158: i_mesh_profile, 160: i_level, 161: i_sound_off, 163: i_flow,
    164: i_active_mesh, 165: i_mesh_cal,
})
for n, icon_id in enumerate(range(166, 174)):          # fan animation: 8 steps over 90 degrees
    ALL[icon_id] = i_fan(n * 90 / 8)

# --- Runde 3: Wartung (neue IDs 186-188) ------------------------------------
def i_belt():                           # 186 belt + pulleys
    p = Pen(20, 20)
    p.circle(4.6, 10, 3.6, fill=STEEL_LIGHT)
    p.circle(15.4, 10, 3.6, fill=STEEL_LIGHT)
    p.circle(4.6, 10, 1.3, fill=DARK)
    p.circle(15.4, 10, 1.3, fill=DARK)
    p.line([(4.6, 5.6), (15.4, 5.6)], CYAN, 1.9)
    p.line([(4.6, 14.4), (15.4, 14.4)], CYAN, 1.9)
    p.arc(4.6, 10, 4.4, 90, 270, CYAN, 1.9)
    p.arc(15.4, 10, 4.4, 270, 450, CYAN, 1.9)
    for x in (7.5, 10, 12.5):
        p.line([(x, 4.4), (x, 6.8)], WHITE, 0.9)
    return p.finish()


def i_lead_screw():                     # 187 lead screw
    p = Pen(20, 20)
    p.rect(8.6, 1, 11.4, 19, STEEL_LIGHT, r=1)
    for k in range(7):
        y = 2.5 + k * 2.4
        p.line([(7.2, y + 1.1), (12.8, y - 0.2)], STEEL, 1.1)
    p.rect(5, 9, 15, 12.6, AMBER, r=1.2)
    p.circle(16.6, 4.2, 2.4, fill=(120, 200, 255))
    p.poly([(14.6, 4.6), (18.6, 4.6), (16.6, 1.0)], (120, 200, 255))
    return p.finish()


def i_filament_sensor():                # 188 filament sensor
    p = Pen(20, 20)
    p.rect(3, 6, 17, 16, STEEL, r=2)
    p.line([(0.6, 11), (19.4, 11)], PINK, 2.2)
    p.circle(13.5, 8.6, 1.5, fill=GREEN)
    p.rect(5, 2.5, 9, 6, STEEL_LIGHT, r=0.6)
    return p.finish()


ALL.update({186: i_belt, 187: i_lead_screw, 188: i_filament_sensor})

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Render Petrel DACAI colour icons")
    ap.add_argument("out_dir")
    ap.add_argument("--dejavu-dir", help="folder with DejaVuSans-Bold.ttf")
    a = ap.parse_args()
    if a.dejavu_dir:
        LETTER_FONT = os.path.join(a.dejavu_dir, "DejaVuSans-Bold.ttf")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for icon_id, fn in sorted(ALL.items()):
        fn().save(out / f"{icon_id:03d}.png")
    print(len(ALL), "icons written to", out)
