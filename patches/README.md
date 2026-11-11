# Patches for Petrel

Base: [sezgynus/Petrel](https://github.com/sezgynus/Petrel) commit
`764d40684ee8485a7d00ffb9df9fc0add77b79c1` (v7.0.0-54).

**0001–0003 are the DACAI support proposed upstream** (a `DacaiDriver` class selected in
`configure.sh`). With them, Petrel uploads the boot picture, shared artwork and icon sprite
sheets over the UART – **no microSD card is needed**. 0004–0007 are optional extras from this
project.

| File | Switch in `Petrel.env` | What it does |
|---|---|---|
| `0001-DWIN-driver-extension-points-…` | – | Small hooks in the DWIN driver for panel variants; no behaviour change on DWIN |
| `0002-Add-DacaiDriver-…` | `PETREL_DACAI=1`, `PETREL_DACAI_BAUD` | The DACAI driver: `0x70` thumbnails, `0x27` bit 7, pictures padded to 32 KB, **icons from JPEG sprite sheets over UART**, host-stepped animations, bare `A5 OK`, brightness 0–63, faster host link, `tools/dacai_artwork.py` |
| `0003-configure.sh-DACAI-panel-option-…` | – | Kconfig menu *Display panel*, `docs/dacai.md` + Turkish translation |
| `0004-Optional-PETREL_HIDE_QR-…` | `PETREL_HIDE_QR=1` | Hides the project QR code on the Info page |
| `0005-Optional-PETREL_DARK_WHEN_PRINTER_OFF-…` | `PETREL_DARK_WHEN_PRINTER_OFF=1` | Backlight off while the printer board is unreachable; the knob wakes it for 10 s |
| `0006-Maintenance-belt-and-lead-screw-…` | – | Maintenance: belt / lead-screw tasks, friendly names, X/Y/Z badges (icons 186–188 come only with the SD overlay) |
| `0007-Optional-PETREL_BOOT_ARTWORK-…` | `PETREL_BOOT_ARTWORK=/path/boot.jpg` | Own boot picture (480×272 baseline JPEG), uploaded over UART |
| `petrel-dacai-all.patch` | – | all of the above as one diff |

Apply as commits (keeps the tree clean for `install.sh`):

```bash
cd ~/Petrel
git checkout -b dacai 764d40684ee8485a7d00ffb9df9fc0add77b79c1
git -c user.name=me -c user.email=me@localhost am ~/petrel-dacai/patches/000*.patch
```

Only the upstream part: `git am ~/petrel-dacai/patches/000[1-3]*.patch`.

Newer Petrel versions: `git rebase origin/master` on the `dacai` branch.

Tests: 0001–0003 add 30 tests and keep Petrel's suite as green as plain upstream (3 failures
exist on plain upstream too). 0006 intentionally changes maintenance behaviour, so 5 of Petrel's
own maintenance tests fail with it applied.

## Older series

* [`legacy-764d406-sd/`](legacy-764d406-sd/) – the previous series for the same base: icons came
  from the microSD card (`PETREL_LCD_SD_ASSETS`), switches `PETREL_DACAI_PICTURE_UPLOAD` and
  `PETREL_RECT_THUMBNAILS`. Superseded by 0001–0003.
* [`legacy-9907edf/`](legacy-9907edf/) – for Petrel v7.0.0-37 (flat file layout).
