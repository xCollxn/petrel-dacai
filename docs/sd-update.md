# Updating the screen via microSD

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
6. Power off, remove the card, power on, start Petrel.

## Back to stock

Same procedure with your untouched stock `private` folder.
