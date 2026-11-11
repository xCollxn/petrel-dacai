# Patches for Petrel

Base: [sezgynus/Petrel](https://github.com/sezgynus/Petrel) commit
`764d40684ee8485a7d00ffb9df9fc0add77b79c1` (v7.0.0-54, after Petrel's move to the `petrel/` package).
For the older v7.0.0-37 (`9907edf`, flat file layout) use [`legacy-9907edf/`](legacy-9907edf/).

| File | Switch | Touches |
|---|---|---|
| `0001-DACAI-accept-bare-A5-OK-…` | always | `petrel/hardware/dwin/protocol.py` |
| `0002-DACAI-PETREL_LCD_SD_ASSETS-…` | `PETREL_LCD_SD_ASSETS=1` | `petrel/hardware/dwin/driver.py` |
| `0003-DACAI-draw-thumbnails-from-rectangles-…` | `PETREL_RECT_THUMBNAILS=1` | `petrel/hardware/dwin/driver.py` |
| `0004-Optional-PETREL_HIDE_QR-…` | `PETREL_HIDE_QR=1` | `petrel/features/info/qr.py`, `petrel/features/info/view.py` |
| `0005-Optional-PETREL_DARK_WHEN_PRINTER_OFF-…` | `PETREL_DARK_WHEN_PRINTER_OFF=1` | `petrel/features/display_settings/view.py` |
| `0006-Maintenance-belt-and-lead-screw-…` | always | `petrel/features/maintenance/records/care.py`, `…/ui/experience.py`, `…/ui/icons.py` |
| `0007-DACAI-0x70-SRAM-JPEG-0x27-bit-7-picture-upload-…` | `PETREL_DACAI=1`, `PETREL_DACAI_PICTURE_UPLOAD=1`, `PETREL_BOOT_ARTWORK` | `petrel/hardware/dwin/driver.py`, `petrel/artwork/boot.py`, `petrel/artwork/shared.py` |
| `0008-DACAI-brightness-range-0.63-and-faster-host-UART-…` | `PETREL_DACAI=1`, `PETREL_DACAI_BAUD` | `petrel/hardware/dwin/driver.py`, `petrel/hardware/dwin/startup.py` |
| `petrel-dacai-all.patch` | – | all of the above as one diff |

Without their switch, 0002–0005, 0007 and 0008 leave Petrel's behaviour unchanged, so they are safe on DWIN
screens too. 0006 uses icon IDs 186–188, which exist only in this project's SD overlay.

Apply as commits (keeps the tree clean for `install.sh`):

```bash
cd ~/Petrel
git checkout -b dacai 764d40684ee8485a7d00ffb9df9fc0add77b79c1
git -c user.name=me -c user.email=me@localhost am /path/to/patches/000*.patch
```

Or as a plain diff: `git apply /path/to/petrel-dacai-all.patch` (tree becomes dirty).

Newer Petrel versions: `git rebase origin/master` on the `dacai` branch; most hunks are small
and self-contained.

0006 is a home-workshop customisation (belt / lead-screw maintenance tasks). It intentionally
changes maintenance behaviour, so 5 of Petrel's own maintenance tests fail with it applied; all
other patches keep Petrel's test suite green (3 further failures exist on plain upstream too).
