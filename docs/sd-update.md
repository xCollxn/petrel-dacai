# Updating the screen via microSD

> **Optional.** With Petrel's DACAI driver (`PETREL_DACAI=1`) the boot picture and all icons are
> uploaded over the UART; no SD card is needed. Use the SD overlay only for the bold font or the
> redrawn icons, or to return to stock.

DACAI screens read their artwork from a folder called **`private`** on a microSD card in the
slot on the back of the screen. (Genuine DWIN screens use `DWIN_SET` – never mix them up.)

## 1. Get the stock `private` folder

You need the complete stock folder once, because this project does not redistribute
Creality's files. Sources:

* the screen firmware for your printer from Creality's download page (look for a `private`
  folder inside the firmware archive), or
* the community copy in
  [mriscoc/Ender3V2S1 → display assets/stock/private](https://github.com/mriscoc/Ender3V2S1/tree/Ender3V2S1-Bugfix/display%20assets/stock/private).

Keep an untouched copy – it is also your way back to the original look.

A stock folder contains `config.txt`, `icon/2.zico`, `icon/9.zico`, `image/0.jpg … 2.jpg`
and `truefont/font.ttf` + `truefont.ini`.

## 2. Build the folder

```bash
python3 tools/make_sd_package.py --stock /path/to/stock/private --out ~/sd
# optional own boot image:
python3 tools/make_boot.py my_boot.jpg --title "My Printer" --dejavu-dir fonts/dejavu
python3 tools/make_sd_package.py --stock /path/to/stock/private --out ~/sd --boot my_boot.jpg
```

What gets replaced: `icon/2.zico` (Petrel icon library), `image/0.jpg` (boot image),
`image/1.jpg` (Petrel shared artwork), `truefont/font.ttf` (+ ini).

## 3. Flash

1. Format the card: **FAT32, allocation unit 4096 bytes**, MBR. ≤ 32 GB is safest.
2. Copy the whole **`private`** folder to the card root (`E:\private\icon\2.zico` …).
3. Stop Petrel.
4. Unplug the screen's power (pulling the cable at the screen is the safest way).
5. Insert the card into the screen, power it again, wait until the update has finished.
6. Power off, remove the card, power on.
7. The SD update removes the pictures Petrel uploaded. Upload them again, then start Petrel:
   `~/petrel-env/bin/python ~/Petrel/tools/dacai_artwork.py --serial-port /dev/ttyAMA0`.
   Petrel's sprite sheets take precedence over icons from the card; icons Petrel does not have
   (e.g. 186–188 of patch 0006) still come from the card.

## Screen firmware update (`firmware.zlib`)

The reference screen runs **Creality's official Ender 3 Max Neo display firmware**: `firmware.zlib`
(build May 18 2022, SHA-256 `38712bb5…3786`) from the Creality download
`Ender 3-Max Neo-Marlin2.0.8.3-HW-V4.2.2-SW-V1.4.1_C` (20 Oct 2022), folder `Display Firmware`.
The same file is in [mriscoc's `dacai_update.zip`](https://github.com/mriscoc/Ender3V2S1/tree/Ender3V2S1-Bugfix/display%20assets).
Thumbnails and the SD-free icons were only verified with it. To install it, put `firmware.zlib`
next to the `private` folder on the card and flash as above; the screen shows
"Upgrading firmware". Remove the card afterwards.

* **Do not** use the later package `SW-V1.4.7_G`: it contains `TJC_SET/tjc.tft` for Max Neo units
  with a **TJC** screen, not for DACAI.
* **Never** copy the `.bin` files of these packages to the printer mainboard – they are Marlin and
  would replace Klipper.

## Back to stock

Same procedure with your untouched stock `private` folder.
