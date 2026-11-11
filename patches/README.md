# Patches for Petrel

Base: [sezgynus/Petrel](https://github.com/sezgynus/Petrel) commit
`9907edfac4a6e50b4c71f25613d522ffec4a49ba` (v7.0.0-37).

| File | Switch | Touches |
|---|---|---|
| `0001-DACAI-accept-bare-A5-OK-…` | always | `dwin_protocol.py` |
| `0002-DACAI-PETREL_LCD_SD_ASSETS-…` | `PETREL_LCD_SD_ASSETS=1` | `t5uic1_driver.py` |
| `0003-DACAI-draw-thumbnails-from-rectangles-…` | `PETREL_RECT_THUMBNAILS=1` | `t5uic1_driver.py` |
| `0004-Optional-PETREL_HIDE_QR-…` | `PETREL_HIDE_QR=1` | `info_qr.py`, `petrel_ui.py` |
| `0005-Optional-PETREL_DARK_WHEN_PRINTER_OFF-…` | `PETREL_DARK_WHEN_PRINTER_OFF=1` | `petrel_ui.py` |
| `0006-Maintenance-belt-and-lead-screw-…` | always | `maintenance_care.py`, `maintenance_experience.py`, `maintenance_icons.py` |
| `0007-DACAI-0x70-SRAM-JPEG-0x27-bit-7-picture-upload-…` | `PETREL_DACAI=1`, `PETREL_DACAI_PICTURE_UPLOAD=1`, `PETREL_BOOT_ARTWORK` | `t5uic1_driver.py`, `boot_artwork.py`, `shared_artwork.py` |
| `petrel-dacai-all.patch` | – | all of the above as one diff |

Without their switch, 0002–0005 and 0007 leave Petrel's behaviour unchanged, so they are safe on DWIN
screens too. 0006 uses icon IDs 186–188, which exist only in this project's SD overlay.

Apply as commits (keeps the tree clean for `install.sh`):

```bash
cd ~/Petrel
git checkout -b dacai 9907edfac4a6e50b4c71f25613d522ffec4a49ba
git -c user.name=me -c user.email=me@localhost am /path/to/patches/000*.patch
```

Or as a plain diff: `git apply /path/to/petrel-dacai-all.patch` (tree becomes dirty).

Newer Petrel versions: `git rebase origin/master` on the `dacai` branch; most hunks are small
and self-contained.
