# ★ Advanced: FEL access to the DACAI screen

> **⚠️ Optional, for people who can solder – at your own risk.** Nothing here is needed to run
> Petrel on a DACAI screen. FEL gives you raw access to the screen's flash memory: you can
> back it up and rescue a broken screen, but a wrong write can also leave it dark until you
> restore your backup. **Make the backup first.** Never publish your backup – it contains
> Creality's firmware.

## What you get

| | |
|---|---|
| 🛟 **Backup and rescue** | A byte-exact copy of the screen's 2 MB flash; a screen with corrupted firmware or file system can be restored |
| 🎨 **Native icons and animations** | Your own icon library (`icon/2.zico`) on the screen, with the screen's own `0x28` animations (patch 0009, `PETREL_DACAI_PANEL_ICONS=1`) |
| 🧹 **Clean up** | Remove leftover pictures and files from the 1 MB file system that UART commands cannot delete |

All of this works over the screen's **USB pins** and a microSD "FEL key". Only J3 needs three
solder joints; the pads marked J2 are **not** needed.

## What you need

* soldering iron, an old USB cable with a **USB-A** plug you can cut
* a microSD card (any size, FAT32) – it becomes the "FEL key"
* the Pi running Petrel (or any Linux PC) with `sunxi-tools`
* a multimeter is handy for checking wire colours

## 1. Solder USB to J3

Power the screen off (unplug it at the screen). J3 is the unpopulated 3-pin header next to the
microSD slot ([board photo](img/dacai-board-annotated.jpg), [chip pins](img/dacai-f1c100s-uart-pins.jpg)).

| Wire (usual colours) | Signal | J3 pad |
|---|---|---|
| black | GND | **square** pad |
| green | USB D+ | **middle** pad (F1C100s pin 69) |
| white | USB D− | **outer** round pad (F1C100s pin 68) |
| red | +5 V | **do not connect** – cut and insulate it |

If your cable uses other colours, find the pins with a continuity tester (USB-A from the front,
contacts up: 1 = +5 V, 2 = D−, 3 = D+, 4 = GND). Optionally solder a 3-pin header into J3 instead.
Add strain relief (cable tie or a drop of hot glue) so the cable cannot pull on the pads. Plug
the USB-A end into the Pi and leave it connected: in normal operation the screen's USB port is
silent and nothing happens.

## 2. Install the tools on the Pi

```bash
sudo apt install sunxi-tools
sudo usermod -aG sunxi-fel "$USER"      # then log out and in again
```

The tools of this project are in `tools/fel/` (Python 3 with Pillow – Petrel's
`~/petrel-env/bin/python` has it).

## 3. Make the FEL key (microSD)

The F1C100s checks the microSD card **before** its own flash. A card with the small
`fel-sdboot` program at 8 KB makes it jump straight into FEL mode – no J2 bridge, no tweezers.

1. Delete all files from the card (no `private` folder or `firmware.zlib` on it). Normal FAT32
   formatting starts the partition at 1 MB or later, which leaves room at 8 KB.
2. Put the card into the **Pi's** microSD slot (or a USB card reader) and find its device name:
   ```bash
   lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINT
   ```
   > **⚠️ Writing to the wrong device destroys that disk.** The Pi's system disk is usually
   > `nvme0n1` or `mmcblk0` with a mounted `/`. The card has the size of *your card* and is not mounted.
3. Write the program (replace `/dev/mmcblk0` with **your card**):
   ```bash
   sudo dd if=/usr/share/sunxi-tools/fel-sdboot.sunxi of=/dev/mmcblk0 bs=1024 seek=8 conv=fsync
   ```
   The card stays a normal FAT32 card. Label it "FEL".

   > **It stays a FEL card after formatting.** Formatting only rewrites the partition; the
   > program at 8 KB survives. Using the card for a microSD update then keeps the screen black
   > (it is in FEL mode, `lsusb` shows `1f3a:efe8`) and the update never starts. Use another
   > card, or clear the area before the partition:
   > `sudo dd if=/dev/zero of=/dev/mmcblk0 bs=1024 seek=8 count=1016 conv=fsync`
   > (again: **your card**, and only if its partition starts at 1 MB – check with `sudo fdisk -l`).

## 4. Enter and leave FEL mode

1. Stop Petrel: `curl -X POST "http://localhost:7125/machine/services/stop?service=Petrel"`
2. Unplug the screen, insert the FEL key, power it again → **the screen stays black.**
3. Check:
   ```bash
   lsusb | grep 1f3a:efe8            # "Allwinner ... in FEL/flashing mode"
   sunxi-fel version                  # soc=00001663(F1C100s)
   sunxi-fel spiflash-info            # size: 2097152 bytes
   ```
4. To leave: power off, **remove the card**, power on, start Petrel.

## 5. Back up first

```bash
bash ~/petrel-dacai/tools/fel/fel_backup.sh ~/dacai-backup
```

The script reads the whole flash twice and keeps it only if both reads are identical (about 10 s
each). Copy the file to a second place (PC, NAS). This is your way back to exactly today's state.

## Flash layout (2 MB SPI NOR)

| Offset | Content |
|---|---|
| `0x000000` | Boot code (`eGON.BT0`) and the screen firmware (compressed) |
| `0x0E0000`–`0x0E3FFF` | Data Flash of the T5UIC1 protocol (`0x31`/`0x32` address 0 = flash `0xE0000`). Petrel's records live here, e.g. `PETBOOT1` at `0xE0120`, `PETPAGE1` at `0xE0150`, `PETSPR01` at `0xE0600` |
| `0x100000`–`0x1FFFFF` | File system `3:/`: FAT12, 1 MB, 512-byte clusters – `config.txt`, `icon/*.zico`, `image/*.jpg`, `truefont/*` |

The screen's microSD update replaces `icon/`, `image/` and `truefont/` in this file system.
Petrel's picture uploads (`0x33`) add `image/<id>.jpg` files here.

## 6. Edit the file system

All editing happens offline on a copy; only the finished 1 MB image is written.

```bash
cd ~/petrel-dacai/tools/fel
P=~/petrel-env/bin/python
B=~/dacai-backup/dacai-spi-YYYYMMDD-HHMMSS.bin        # your backup

$P dacai_fs.py list    "$B"                                     # what is on the screen
$P dacai_fs.py extract "$B" /ICON/2.zico 2.zico                # copy a file out
$P dacai_fs.py delete  "$B" fs-new.bin /IMAGE/22.JPG /MAIN.LUA # remove files
$P dacai_fs.py replace "$B" fs-new.bin /ICON/2.zico my.zico    # swap a file's content
$P dacai_fs.py repair  "$B" fs-new.bin                          # free space no file owns
```

`delete`, `replace` and `repair` write a 1 MB image and check that every other file is
byte-identical. To combine several steps, use the previous output image as the next input.
`list` ends with `file system consistent` or with a warning and what to do about it. Then, with
the screen in FEL mode:

```bash
bash fel_write_fs.sh fs-new.bin "$B"
```

The script writes **only** the file system (offset `0x100000`), reads it back and compares, and
confirms that boot code and firmware still match your backup (about 20 s).

### The firmware's own FAT copy

The screen firmware can keep a copy of the boot sector and the FAT in the last 16 sectors of
the file system (8 KB that the FAT shows as free), followed by a header `00 01 FF FE` +
CRC-16/MODBUS. If that header is valid and the copy differs from the FAT, the firmware **restores
the old FAT at the next start** – an offline edit is undone, and the space it freed comes back as
used by no file. On the reference screen this filled the file system until Petrel's picture
uploads were acknowledged but no longer stored (icons stayed empty).

`dacai_fs.py` therefore updates that copy on every write (`list` shows its state). When the
screen was nearly full, the firmware may also have stored a picture in those sectors and then
written its copy over it: `repair` then refuses and asks you to `delete` that picture first
(Petrel uploads it again). After writing an image back, a fresh backup + `list` should report
`file system consistent`.

## 7. Native icons and animations (patch 0009)

Petrel normally draws icons from sprite sheets it uploads itself. With your own icon library on
the screen, Petrel can use the screen's icon files instead – your own artwork and the screen's
own animations:

1. Build a library with all of Petrel's icon IDs – copy `~/Petrel/assets/icons/*.jpg` into a
   folder, put your redrawn icons over them (same IDs and sizes), then
   `python3 ~/petrel-dacai/tools/build_zico.py folder/ my.zico` – and check it:
   ```bash
   $P zico_tool.py compare my.zico ~/Petrel/assets/icons   # "MISSING: none", "different size: none"
   ```
2. Animations are drawn opaque. Give the fan frames the dashboard colour instead of black:
   ```bash
   $P zico_tool.py backing my.zico my-fan.zico 0x18C4 166-173
   ```
3. Put it on the screen with `dacai_fs.py replace … /ICON/2.zico my-fan.zico` and
   `fel_write_fs.sh` – or, without FEL, via the microSD overlay ([sd-update.md](sd-update.md)).
   Optionally delete the then unused sprite sheets `/IMAGE/16.JPG` … `/IMAGE/21.JPG`.
4. Add `PETREL_DACAI_PANEL_ICONS=1` to `Petrel.env` and restart Petrel. The log shows
   `Panel icon files in use; sprite checkpoint cleared`.

**After every Petrel update** run `zico_tool.py compare` again: new or changed icons are not on
the screen until you rebuild and write the library. To go back to sprite sheets, remove the
setting – Petrel uploads all sheets again on the next start.

## 8. Restore

File system only (icons, pictures, font as at backup time):

```bash
dd if="$B" of=fs-backup.bin bs=1024 skip=1024 count=1024
bash fel_write_fs.sh fs-backup.bin "$B"
```

**Last resort – the whole flash including firmware** (only if the screen no longer starts):

```bash
sunxi-fel spiflash-write 0 "$B"
sunxi-fel spiflash-read 0 2097152 check.bin && cmp check.bin "$B" && echo "restored"
```

The FEL key always works, because the chip enters FEL before it reads its own flash.

## Notes

* J2 (2 pads next to the crystal) is **not** a FEL or reset bridge: its round pad has a 15 kΩ
  pull-up to 3.3 V and connects neither to the SPI flash nor to the SoC reset pin. Leave it alone.
* `main.lua` in the file system is not executed in the DWIN-emulation mode (tested).
* Tested on the reference screen (Ender 3 Max Neo, board Rev 1.5, Creality display firmware
  `SW-V1.4.1_C`). Other screens may use other flash sizes – the scripts stop if the layout differs.
