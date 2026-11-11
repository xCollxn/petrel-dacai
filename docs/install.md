# Installation – step by step

Tested on Raspberry Pi 5 (Debian 13), Klipper v0.13.0, Moonraker v0.11.0, Mainsail 2.19,
Petrel `764d406` (v7.0.0-54). Commands assume the Klipper user's home directory (`~`) and this repository
cloned to `~/petrel-dacai`.

## 1. Wiring and UART

See [wiring.md](wiring.md). Afterwards enable the primary UART:

* **Pi 5:** add `dtparam=uart0=on` to `/boot/firmware/config.txt`, reboot. The screen is then on
  `/dev/ttyAMA0` (GPIO14/15). The Pi 5 debug console uses `ttyAMA10` and does not interfere.
* **Pi 3/4:** disable the serial login console in `raspi-config` and use `dtoverlay=disable-bt`;
  the port is `/dev/ttyAMA0`.
* Your user must be in the `dialout` and `gpio` groups.

## 2. Is it really a DACAI panel?

```bash
python3 ~/petrel-dacai/tools/dacai_probe.py --draw-test
```

* `handshake: aa 00 4f 4b cc 33 c3 3c` → the screen answers.
* `DACAI panel` → continue here.
* `behaves like a genuine DWIN T5UIC1` → use plain Petrel, you do not need this project.
* With `--draw-test` four coloured squares should appear in the middle of the screen.

No answer at all? Swap the two UART wires (the screen's `DIN`/`DOUT` labels are sometimes
written from the mainboard's point of view) and check 5 V/GND.

## 3. Petrel with patches

```bash
git clone https://github.com/sezgynus/Petrel.git ~/Petrel
cd ~/Petrel
git checkout -b dacai 764d40684ee8485a7d00ffb9df9fc0add77b79c1
git -c user.name=me -c user.email=me@localhost am ~/petrel-dacai/patches/000*.patch
git log --oneline | head -7          # six "DACAI / Optional / Maintenance" commits on top
git status --short                   # must be empty (the installer requires a clean tree)
```

## 4. Settings before installing

```bash
mkdir -p ~/.config/Petrel && chmod 700 ~/.config/Petrel
cp ~/petrel-dacai/examples/Petrel.env ~/.config/Petrel/Petrel.env
nano ~/.config/Petrel/Petrel.env     # check port and encoder pins
```

Because the file exists, `install.sh` keeps it and skips the interactive menu. The example
disables Petrel's optional Klipper extras, so your `printer.cfg` is not touched.

## 5. Install

```bash
cd ~/Petrel && bash install.sh       # install.sh is not executable in the repo, call it via bash
```

It installs packages (sudo), creates `Petrel.service`, adds `[include Petrel.conf]` to
`moonraker.conf` and restarts Moonraker. Petrel starts right away – with the patches, so the
screen is safe.

## 6. SD card

Follow [sd-update.md](sd-update.md). Stop Petrel during the update:

```bash
sudo systemctl stop Petrel           # or without sudo: curl -X POST "http://localhost:7125/machine/services/stop?service=Petrel"
```

## 7. Check

```bash
sudo systemctl start Petrel
journalctl -u Petrel -f              # expect "LCD UART connected"
```

* Wrong knob direction → swap the two numbers in `PETREL_ENCODER_PINS` and restart Petrel.
* A warning about the buzzer GPIO is expected when GPIO19 is used for the encoder.
* `Cannot refresh Mainsail presets: 404` just means you have no Mainsail preheat presets yet.

**That's it – steps 1–7 are all you need.**

## Two settings outside Petrel that are easy to miss

* **Thumbnails need thumbnails in the G-code.** Enable them in your slicer, e.g. OrcaSlicer /
  PrusaSlicer: *Printer settings → G-code thumbnails* `32x32/PNG, 300x300/PNG`; Cura: the
  *Moonraker / Create Thumbnail* post-processing script. Moonraker extracts them automatically;
  older files without thumbnails just show the file icon.
* **Preheat buttons come from Mainsail.** Petrel shows Mainsail's preheat presets
  (*Mainsail → Settings → Presets*, e.g. "PLA 215/55", "PETG 235/70"). Without presets Petrel
  uses built-in defaults (PLA 200/60, ABS 210/100). Fluidd users can set the two values on the
  screen under *Control → Temperature*.

## Recommended: maintenance reminders (no extra hardware)

On the screen: *Maintenance → Care schedule → Add reminder*. Choose *Sampled printing hours*
(counts real printing time only, not screen-on time) or *Extruded filament (metres)*.
Starting points for PLA/PETG: X/Y *Belt & roller check* 100 h, Z *Lead screw clean & lube*
200 h, hotend *Nozzle maintenance* 1000 m (≈ 3 kg; much less for abrasive filament).

## ★ Optional add-ons (skip if you do not have the hardware)

* ★ **Home Assistant autostart** – needs Home Assistant, the Moonraker integration and a
  power-measuring smart plug: [examples/home-assistant](../examples/home-assistant/).
  Without it: send `FIRMWARE_RESTART` in Mainsail/Fluidd after switching the printer on.
* ★ **Own boot image** – `tools/make_boot.py --title "My Printer" --info "220 × 220 × 250 mm" out.jpg`
  (needs the DejaVu fonts: `tools/fetch_dejavu.sh`), then rebuild the SD folder with `--boot out.jpg`.
