#!/usr/bin/env python3
"""Draw Petrel's documentation scenes on the real DACAI panel through DacaiDriver.

    petrel_scenes.py [--petrel DIR] --list
    petrel_scenes.py [--petrel DIR] SCENE [SCENE ...]

Uses Petrel's own scene renderer (tools/render_docs_screenshots.py with its test
fixtures), but sends the packets to /dev/ttyAMA0 instead of only the emulator, so
screens that need hardware you may not have (MMU, NFC reader) can be checked on
the panel. The emulator image of the same packets is saved as /tmp/panel-SCENE.png
for comparison. Stop Petrel first. Needs a Petrel checkout with DacaiDriver and
its uploaded sprite sheets (icons are drawn from pictures 16+).

Scenes with diagonal lines (see 0x03 in docs/dacai-protocol.md): nfc-gate-choose,
nfc-gate-complete, nfc-gate-error, mmu-cutting-tip, mmu-cutting-filament.
"""
import argparse
from pathlib import Path
import sys
import time
from unittest.mock import patch

import serial

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument('--petrel', default=str(Path.home() / 'Petrel'))
parser.add_argument('--port', default='/dev/ttyAMA0')
parser.add_argument('--list', action='store_true')
parser.add_argument('scenes', nargs='*')
args = parser.parse_args()
root = Path(args.petrel)
sys.path[:0] = [str(root), str(root / 'tests'), str(root / 'tools')]
sys.argv = sys.argv[:1]  # the renderer must not see our arguments

import render_docs_screenshots as R  # noqa: E402
from test_t5uic1_driver import driver as fake_driver  # noqa: E402
from petrel.artwork import sprites  # noqa: E402
from petrel.emulator.framebuffer import Framebuffer  # noqa: E402
from petrel.hardware.dwin.dacai import DacaiDriver  # noqa: E402

PORT = serial.Serial(args.port, 115200, timeout=0.3)


def panel_driver():
    lcd = fake_driver()
    lcd.__class__ = DacaiDriver
    lcd.serial = lcd.MYSERIAL1 = PORT
    lcd.host_baud = 115200
    lcd._sprites = sprites.load().index
    lcd._sprite_animations = {}
    lcd._sprite_mask = 0xFFFF
    return lcd


class DacaiFramebuffer(Framebuffer):
    def reset(self, protocol='dacai'):
        super().reset('dacai')


R.driver = panel_driver
R.Framebuffer = DacaiFramebuffer
scenes = {name: draw for name, _group, _en, _tr, draw in R.SCENES}
scenes['mmu-cutting-tip'] = lambda: R.mmu(changes=dict(action='Cutting Tip', filament='Loaded', filament_pos=10))
scenes['mmu-cutting-filament'] = lambda: R.mmu(changes=dict(action='Cutting Filament', filament='Loaded',
                                                            filament_pos=10))

if args.list or not args.scenes:
    print(' '.join(sorted(scenes)))
    sys.exit()

PORT.write(b'\xAA\x00\xCC\x33\xC3\x3C'); PORT.flush(); time.sleep(0.2); PORT.reset_input_buffer()
PORT.write(b'\xAA\x30\x3F\xCC\x33\xC3\x3C'); PORT.flush()  # backlight on
with patch.object(time, 'strftime', return_value='12:34'), \
        patch('petrel.features.mmu.filament_view.time.monotonic', return_value=3.6):
    for name in args.scenes:
        image = scenes[name]()
        image.save(f'/tmp/panel-{name}.png')
        print('shown', name, '- emulator image /tmp/panel-' + name + '.png')
        if name != args.scenes[-1]:
            time.sleep(4)
