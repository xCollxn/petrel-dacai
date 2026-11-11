# DACAI vs. DWIN T5UIC1 – what is different

Findings from a Creality DACAI 4.3" knob screen (sticker `…SZCX48270M043_4.3寸_旋钮彩屏 V525`,
272×480 portrait) attached to a Raspberry Pi UART at 115200 8N1. Frames use the usual T5UIC1
layout `AA <cmd> <payload> CC 33 C3 3C`.

## Works like DWIN

| Command | | Notes |
|---|---|---|
| `0x00` handshake | ✅ | answers `AA 00 4F 4B CC 33 C3 3C` |
| `0x05` rectangle (fill/outline) | ✅ | used for all drawing and for thumbnails |
| text drawing | ✅ | rendered with the TrueType font from `private/truefont` |
| `0x23` show icon | ✅ | icon libraries come from `private/icon/N.zico` |
| `0x22` show JPEG from flash, area copy from picture 1 | ✅ | pictures come from `private/image/N.jpg` |
| `0x30` backlight | ✅ | 0 = dark |
| `0x32` read SRAM / data flash | ✅ | framed answer as on DWIN |
| `0x28` / `0x29` native icon animation | ✅ | runs on the panel by itself, several channels at once, no `0x3D` refresh needed (tested: 2 channels, icons 181–185 and 166–173) |
| `0x25` cache JPEG to area 1 + `0x26` copy from area 1 | ✅ | cache does not change the screen; copy is opaque (black pixels copied) |
| `0x27` copy from area 0 (picture shown by `0x22`) | ⚠️ | works, but bit 7 is inverted – see below |

## Different

1. **Drawing needs `0x3D` (update).** Drawing commands only become visible after
   `AA 3D CC 33 C3 3C`. (Petrel sends it anyway; your own test scripts must too.)
2. **Unframed acknowledgements.** Writes answer with raw bytes, without `AA` header and tail:
   * data-flash write `0x31 A5 …` → `A5 4F 4B` (DWIN: `AA 31 A5 4F 4B CC 33 C3 3C`)
   * SRAM write `0x31 5A …` → `5A 4F 4B` (DWIN: no answer) – a handy non-destructive way to tell
     the two panels apart (`tools/dacai_probe.py`).
3. **No JPEG from SRAM.** `0x24` (show SRAM JPEG) does nothing, in every mode tested
   (0x00, 0x20, 0x80, 0xA0, without mode byte). SRAM writes themselves work.
   → Thumbnails: decode on the host and draw horizontal colour runs with `0x05`
   (128×128 ≈ 1000 rectangles ≈ 15 KB ≈ 1.5 s).
4. **Picture-flash uploads over UART are not reliable.** Uploading pictures/icon blocks the
   DWIN way (SRAM + `0x33`) is acknowledged, but the icons never show up and the boot picture
   ends up broken. Artwork has to come from the SD card.
5. **Artwork format.** `private/` instead of `DWIN_SET/`:
   ```
   private/config.txt          register settings, e.g. "R1=07; 115200"
   private/icon/2.zico, 9.zico icon libraries (ZICO, see below)
   private/image/0.jpg …       480x272 baseline JPEGs (stored rotated, shown portrait)
   private/truefont/font.ttf   TrueType font, truefont.ini: "[setting] font0=font.ttf"
   ```
6. **`0x27` bit 7 is inverted.** With mode `0x00` the region is copied opaque (like DWIN with
   `0x80`). With mode `0x80` black pixels are treated as transparent, so only the non-black parts
   of the picture are drawn over what is on screen. Petrel's boot screen restore
   (`copy_cache(0, …, background=True)` → `0x80`) therefore leaves old content behind; sending
   `0x00` on DACAI fixes it.
7. **Font.** The stock font is a SimSun subset: monospaced, advance exactly 0.5 em,
   ascent 220/256, descent 36/256. Any replacement must keep 0.5 em advances, otherwise UIs that
   assume fixed 8/10 px cells break (`tools/build_font.py`).

## Hardware and extended UART

* Controller on the Rev 1.5 board: **Allwinner F1C100s** (U4) with an 8-pin SPI flash (U3).
* The DWIN extended UART (`0x38` baud divisor, `0x39` transmit, `0x3A` receive) is **not
  available**: no answer on the host UART, and no activity on any spare pin while sending `0x39`
  for 20 s. The 10-pin header has no extra UART pins.
* Unpopulated headers: **J3** (3 holes next to the SD slot) = GND (square) + two floating pins
  (~0.9 V, unchanged by `0x38`/`0x39`); **J2** (2 holes next to the crystal) = GND (square) +
  3.3 V, probably a boot strap – do not short it.

## ZICO icon library

```
offset 0   "ZICO"
offset 4   u32le  directory length in bytes (count × 16)
offset 8   directory, 16 bytes per icon (little endian):
           u16 id | u16 1 | u16 width | u16 height | u32 offset | u32 length
then       payloads: zlib-compressed RGB565 little-endian, row by row
           (offset is relative to the end of the directory)
```

Icon IDs are free (Petrel uses library 2, IDs 0–188 here). Black `0x0000` is filtered as
transparent when an icon is drawn without background. `tools/build_zico.py` writes and verifies
the format.

## Unknown / not tested

* Whether `config.txt` can raise the baud rate (would make thumbnails faster).
* Exact behaviour of other DACAI firmware revisions.
