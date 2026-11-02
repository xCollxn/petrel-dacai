#!/usr/bin/env python3
"""Assemble the microSD ``private`` folder for a DACAI panel.

The panel firmware expects a complete ``private`` folder (config.txt, icon/, image/,
truefont/). Creality's stock files are NOT redistributed here, so start from the
stock folder of your own screen firmware and lay this project's files over it.

Usage:
    make_sd_package.py --stock /path/to/stock/private --out /path/to/sdcard
        [--overlay sd-overlay/private] [--boot my_boot.jpg]

Result: <out>/private/... -> copy the *private* folder to the root of a FAT32 card
(4096-byte allocation unit), insert it into the panel's slot, power the panel on and
wait until the update has finished. See docs/sd-update.md.
"""
import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REQUIRED = ("config.txt", "icon", "image", "truefont")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stock", required=True, help="stock DACAI 'private' folder")
    ap.add_argument("--out", required=True, help="output folder (gets a 'private' subfolder)")
    ap.add_argument("--overlay", default=str(HERE / "sd-overlay" / "private"))
    ap.add_argument("--boot", help="optional own boot JPEG (480x272, see make_boot.py)")
    a = ap.parse_args()

    stock, overlay = Path(a.stock), Path(a.overlay)
    missing = [n for n in REQUIRED if not (stock / n).exists()]
    if missing:
        sys.exit(f"{stock} does not look like a DACAI 'private' folder (missing: {', '.join(missing)}).\n"
                 "If your screen firmware has a DWIN_SET folder instead, you have a DWIN panel: "
                 "use plain Petrel, not this project.")
    target = Path(a.out) / "private"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(stock, target)
    for f in overlay.rglob("*"):
        if f.is_file():
            dest = target / f.relative_to(overlay)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
            print("overlay:", dest.relative_to(target.parent))
    if a.boot:
        shutil.copy2(a.boot, target / "image" / "0.jpg")
        print("boot image:", a.boot)
    print("\nDone ->", target)


if __name__ == "__main__":
    main()
