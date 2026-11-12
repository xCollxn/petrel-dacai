# Guide for AI assistants (Claude, ChatGPT, Copilot, …)

You are helping a user put Petrel on the stock Creality knob screen of a Klipper printer.
This file tells you what to do, in which order, what to verify and what must never happen.
Humans: [README.md](README.md) is for you; this file is fine to read too.

## Ground rules

1. **Identify the panel before anything else.** Run `tools/dacai_probe.py`. Only continue
   with this project for *DACAI panel*. For a genuine DWIN T5UIC1 use plain Petrel.
2. **Never put `DWIN_SET` files on a DACAI card**, never flash panel "kernel" firmware you
   did not get for this exact screen. Artwork changes only via the `private` folder.
3. **Never let unpatched Petrel talk to a DACAI panel.** Its first start uploads a DWIN icon
   library over UART, which DACAI stores as broken pictures. Apply the patches (as commits) and
   set `PETREL_DACAI=1` before `install.sh`.
4. **One UART owner.** Stop Petrel before running any probe/test script.
5. **The printer is real hardware.** Do not home, move, heat or extrude without the user's
   explicit OK in that moment; homing usually needs an empty bed (BLTouch probes the middle).
   Never send `FIRMWARE_RESTART` while a print is running.
6. **Never switch power outlets/smart plugs** to "test" something – they may power other
   devices (routers!). Reading power values is fine.
7. Ask the user to look at the screen whenever you need visual confirmation – you cannot see it.
   Describe exactly what they should see.
8. Keep a backup of anything you change (`printer.cfg`, `moonraker.conf`, HA files).

## Scope: required vs. ★ optional

The screen needs only the Pi and the wires – with patches 0001–0004 Petrel uploads its artwork
and icons over the UART, no SD card. Everything marked ★ (Home Assistant autostart, own boot
image, own icons/font via the SD overlay) is optional. **Ask the user whether they have
Home Assistant and a power-measuring plug before suggesting the autostart add-on**; never make
it a requirement. Without it, `FIRMWARE_RESTART` from Mainsail/Fluidd after power-on is fine.

## Procedure with checkpoints

| Step | Action | Checkpoint |
|---|---|---|
| 1 | Wiring per `docs/wiring.md`. Have the user measure DOUT→GND ≈ 3.3 V with 5 V connected before DOUT goes to the Pi. | value ≤ 3.3 V |
| 2 | Enable UART (Pi 5: `dtparam=uart0=on` in `/boot/firmware/config.txt`, reboot – needs sudo, the user may have to type the password). | `/dev/ttyAMA0` exists, `pinctrl get 14,15` shows TXD0/RXD0 |
| 3 | `python3 tools/dacai_probe.py --draw-test` with the display service stopped | handshake `aa 00 4f 4b …`, *DACAI panel*, user sees 4 squares |
| 4 | Clone Petrel, `git checkout -b dacai 764d406…`, `git am patches/000*.patch` | `git status --short` empty, 8 commits on top |
| 5 | Copy `examples/Petrel.env` to `~/.config/Petrel/Petrel.env`, replace `USER` | file exists *before* install, contains `PETREL_DACAI=1` |
| 6 | `cd ~/Petrel && bash install.sh` (user runs it, needs sudo) | log shows `Sprite sheets: upload complete` (first start, ~15 s) and `LCD UART connected`; user sees Petrel icons |
| 7 | ★ Only for own icons/font: build the SD folder (`tools/make_sd_package.py`), user flashes it (`docs/sd-update.md`), then re-upload artwork with `tools/dacai_artwork.py` in Petrel | user sees the custom font |
| 8 | Knob direction, buttons, temperatures vs. Mainsail | user confirms |

Stopping/starting Petrel without sudo (Moonraker manages it after install):
`curl -X POST "http://localhost:7125/machine/services/stop?service=Petrel"` (`start`, `restart`).

## Symptoms → cause

| Symptom | Cause / fix |
|---|---|
| No handshake answer | UART wires swapped (DIN/DOUT labels can be from the mainboard's view), UART not enabled, wrong port, other program owns the port |
| `LCD UART unavailable; reconnect scheduled` in a loop | `PETREL_DACAI=1` missing (bare `A5 4F 4B` flash ACK) or patches not applied |
| Icons missing / wrong after a panel SD update | the SD update removed the uploaded pictures → stop Petrel, `~/petrel-env/bin/python ~/Petrel/tools/dacai_artwork.py --serial-port …`, start Petrel |
| Boot logo corrupted | unpatched Petrel ran once → apply patches, set `PETREL_DACAI=1`, run `tools/dacai_artwork.py` |
| No thumbnail in the file preview | `PETREL_DACAI=1` missing; also check the G-code has thumbnails (`/server/files/metadata`) |
| Maintenance X/Y/Z badges missing | icons 186–188 of patch 0007 exist only in the SD overlay |
| Your own test drawing does not appear | send `AA 3D CC 33 C3 3C` (update) after drawing |
| Knob runs backwards | swap the numbers in `PETREL_ENCODER_PINS` |
| `Buzzer GPIO conflicts with encoder/button` | expected with this wiring, harmless |
| Klipper `Lost communication with MCU` after power-on | normal; `FIRMWARE_RESTART` (or the HA example automation) |
| Python `ModuleNotFoundError: requests` inside Petrel's venv | do not add dependencies; the patches use only stdlib + Pillow |
| `install.sh: Permission denied` / repo must be clean | call `bash install.sh`; commit patches with `git am` instead of leaving a dirty tree |

## Practical notes for agents

* Quoting: when sending Python through `ssh host '…'`, single quotes inside break the command.
  Prefer copying a script file to the host and running it (`ssh host 'python3 -' < script.py`).
* The Pi 5 venv `~/petrel-env` has Pillow; `fonttools` is only needed for `build_font.py`
  (use a separate venv).
* Icons: with patches 0001–0004 Petrel packs `~/Petrel/assets/icons/NNN.jpg` onto sprite
  sheets itself (pictures 16+). Own icons: replace files there (same size, baseline 4:2:0
  JPEG, black = transparent) and restart Petrel – only changed sheets are uploaded. The SD
  route (`tools/make_icons.py`, `tools/build_zico.py`) is only a fallback for icons Petrel
  cannot find on its sheets.
* Boot image: `tools/make_boot.py` – keep y 280–350 calm, Petrel draws its progress bar there.
* Font changes must keep 0.5 em advances (`tools/build_font.py`).
* Moonraker API is open on the LAN in a default setup; Mainsail preheat presets live in the
  database (`namespace=mainsail`, `key=presets.presets`) and Petrel reads them.
* Report results honestly to the user; if a test needed their eyes, say so.

## Protocol facts you can rely on

See [docs/dacai-protocol.md](docs/dacai-protocol.md): unframed ACKs (`A5 4F 4B`, `5A 4F 4B`),
no `0x24` (use `0x70`), `0x27` bit 7 inverted, `0x33` pictures padded to 32 KB, picture IDs above 15,
no wait needed after `0x25`, update needed via `0x3D`, ZICO format, `private/` layout, font metrics.
