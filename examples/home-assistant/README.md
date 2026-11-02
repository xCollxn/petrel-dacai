# ★ Optional add-on: printer autostart with Home Assistant

**Not needed for the screen.** Skip this folder if you do not use Home Assistant.

## What it solves

If you switch your printer off at the mains after printing, Klipper reports
`Lost communication with MCU` and stays there after you switch the printer on again, until
someone sends `FIRMWARE_RESTART`. With this add-on Home Assistant does that for you:
switch the printer on → after ~20 s Klipper is ready → the screen lights up.

## You need

* Home Assistant
* the [Moonraker integration](https://github.com/marcolivierarsenault/moonraker-home-assistant)
  (HACS) – provides `sensor.<name>_printer_state` and `sensor.<name>_printer_message`
* a smart plug (or other sensor) that **measures the printer's power** in watts

## Setup

1. Copy `printer_autostart.yaml` to `/config/packages/` (packages must be enabled:
   `homeassistant: packages: !include_dir_named packages` in `configuration.yaml`).
2. Replace the placeholders:
   * `MOONRAKER_HOST` → IP or hostname of your Klipper Pi
   * `PRINTER_POWER_SENSOR` → your power sensor, e.g. `sensor.printer_plug_power`
   * `PRINTER` in `sensor.PRINTER_printer_state` / `_printer_message` → your Moonraker device name
3. Check the threshold: look at the power sensor with the printer off and idle. The example
   uses 4 W (idle printers typically draw 5–10 W, off ≈ 0 W). If something else is on the
   same plug, subtract its usage or raise the threshold.
4. Developer tools → YAML → reload *REST commands* and *Automations*.
5. Test: printer off, wait until Klipper shows the error, printer on.

## Safety

* The automation never switches the plug – it only reads the power value.
* It only fires while Klipper is **not ready** and the message is about the lost MCU
  connection – never on real errors such as heater faults, never during a print.
