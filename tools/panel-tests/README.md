# Panel test scripts

Small scripts used to find out what the DACAI panel supports (results: `docs/dacai-protocol.md`).
Stop Petrel first (it owns the UART and switches the backlight off when it stops); every script
talks to `/dev/ttyAMA0` at 115200 and turns the backlight on with `0x30 FF` where it matters.

| Script | Tests |
|---|---|
| `feature_test.py anim\|area0\|area1` | native animation `0x28`, virtual areas `0x27` / `0x25`+`0x26` |
| `testcard.py card\|bright` | one screen with `0x02 0x03 0x05 0x08 0x09 0x14 0x21 0x2A`; backlight levels |
| `sram_jpeg_both.py` | SRAM JPEG: `0x24` (top, fails) vs. DACAI `0x70` (bottom, works) |
| `picture_slot_padded.py <id>` | picture upload over UART: 32 KB padded JPEG + `0x33`, then `0x22` |
| `area1_from_slot.py <id>` | cache an uploaded picture in area 1 and copy half of it |
| `show_slot.py <id>` | show picture `<id>` with `0x22` |
| `aux_test.py` | extended UART `0x38`/`0x39` (no effect on DACAI) |
| `dacai_native.py` | Dacai's own HMI handshake `EE 04 FF FC FF FF` (no answer) |
| `rect_extent_test.py up\|left\|down\|right\|copy` | which rows/columns `0x09` and `0x27` really touch (off-by-one on DACAI) |
| `petrel_scenes.py [--petrel DIR] SCENE…` | draws Petrel's documentation scenes (e.g. MMU, NFC gate views) on the panel through `DacaiDriver` |

`picture_slot_padded.py` writes to the panel's flash – use a free picture slot (Petrel uses 0 and 1).
