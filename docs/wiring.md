# Wiring

The stock knob screen has a 2×5 header (labels on the PCB):

```
GND   B    ENT   DIN   NC
5V    A    BEEP  DOUT  NC
```

| Screen | Raspberry Pi | Physical pin | Note |
|---|---|---|---|
| 5V | 5 V | 2 | screen board is "5V ONLY" (it has its own 3.3 V regulator) |
| GND | GND | 6 | |
| DOUT (screen transmits) | GPIO15 / RXD0 | 10 | measure first: must be ≈ 3.3 V |
| DIN (screen receives) | GPIO14 / TXD0 | 8 | |
| ENT (knob button) | GPIO13 | 33 | internal pull-up is enough |
| A (encoder) | GPIO19 | 35 | |
| B (encoder) | GPIO26 | 37 | |
| BEEP, NC | – | – | not used |

* Header orientation on the Pi: USB ports towards you, header on the right → pin 1 is top-left
  (inner row = odd pins, outer edge = even pins).
* Connect **GND first, then 5 V**. Pin 1 (3.3 V) sits right next to pin 2 – do not slip.
* **Measure DOUT against GND with 5 V connected** before wiring it to the Pi: ≈ 3.3 V is fine,
  5 V would need a voltage divider.
* If the screen does not answer, the two data wires are swapped: on some boards `DIN`/`DOUT`
  are named from the mainboard's point of view. Swapping them is harmless.
* Encoder direction is fixed in software (`PETREL_ENCODER_PINS="26 19"` or `"19 26"`).
* Petrel's own defaults (encoder 21/16, button 20, buzzer 19) are different – the pins above
  follow the classic `DWIN_T5UIC1_LCD` wiring. With them the hardware PWM buzzer is not used.
* Raspberry Pi 5 with the official M.2 HAT+: the supplied 16 mm stacking header barely reaches
  through; use a taller push-fit stacking header and keep the 16 mm standoffs.
* Longer distance (e.g. 1.5 m): a 10-pin IDC ribbon cable works; tie unused wires to GND.
  External 4.7–10 kΩ pull-ups to 3.3 V on A/B/ENT help if the knob skips steps.
