#!/usr/bin/env python3
"""Build a DACAI-compatible ``private/truefont/font.ttf`` from DejaVu Sans Mono.

The stock DACAI font is a SimSun subset: monospaced, every glyph exactly 0.5 em
wide, ascent 220/256, descent 36/256. Petrel lays text out on that fixed grid, so the
replacement keeps the same metrics: outlines are scaled (x 0.8305, y 0.80, +100 up),
every advance is 1024/2048, hinting is removed, and the character set is
U+0020-U+007E plus U+00A0-U+00FF.

Requires: pip install fonttools
Usage: build_font.py <DejaVuSansMono[-Bold].ttf> <out font.ttf> ["Family Name"]
"""
import sys

from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

if len(sys.argv) < 3:
    sys.exit(__doc__)
src, dest = sys.argv[1], sys.argv[2]
name = sys.argv[3] if len(sys.argv) > 3 else "DACAI DejaVu Mono"
SX, SY, DY = 0.8305, 0.80, 100
UPM, ADV, ASC, DESC = 2048, 1024, 1760, 288

font = TTFont(src)
opts = Options()
opts.hinting = False
opts.layout_features = []
opts.name_IDs = ["*"]
opts.notdef_outline = True
sub = Subsetter(opts)
sub.populate(unicodes=list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)))
sub.subset(font)

glyf, gs, hmtx = font["glyf"], font.getGlyphSet(), font["hmtx"]
for gname in font.getGlyphOrder():
    pen = TTGlyphPen(gs)
    gs[gname].draw(TransformPen(pen, (SX, 0, 0, SY, 0, DY)))
    g = pen.glyph()
    glyf[gname] = g
    g.recalcBounds(glyf)
    hmtx[gname] = (ADV, g.xMin if g.numberOfContours else 0)

for tag in ("fpgm", "prep", "cvt ", "hdmx", "LTSH", "VDMX", "kern", "GPOS", "GSUB", "GDEF", "FFTM"):
    if tag in font:
        del font[tag]
font["head"].unitsPerEm = UPM
font["head"].flags &= ~(1 << 4)
hh = font["hhea"]
hh.ascent, hh.descent, hh.lineGap, hh.advanceWidthMax = ASC, -DESC, 0, ADV
os2 = font["OS/2"]
os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = ASC, -DESC, 0
os2.usWinAscent, os2.usWinDescent, os2.xAvgCharWidth = ASC, DESC, ADV
font["post"].isFixedPitch = 1
for rec in font["name"].names:
    if rec.nameID in (1, 3, 4, 6, 16):
        rec.string = name if rec.nameID != 6 else name.replace(" ", "")
font["maxp"].maxZones = 1
font.save(dest)
check = TTFont(dest)
print(dest, "glyphs:", len(check.getBestCmap()),
      "advances:", {check["hmtx"][g][0] for g in check.getGlyphOrder()})
