#!/bin/bash
# Write a 1 MB DACAI file-system image ("3:/") to SPI flash offset 0x100000 via FEL and verify.
# usage: fel_write_fs.sh fs-image.bin backup.bin     (panel in FEL mode, Petrel stopped)
#   fs-image.bin  1 MB image made with dacai_fs.py (delete/replace) or cut from a backup
#   backup.bin    your full 2 MB backup from fel_backup.sh - used to prove that boot code and
#                 firmware (0x000000-0x0DFFFF) are untouched afterwards
# This script never writes below 0x100000. It refuses anything but a 2 MB flash with a
# FAT volume at 0x100000.
set -e
IMG="$1"; BACKUP="$2"
[ -f "$IMG" ] && [ -f "$BACKUP" ] || { echo "usage: $0 fs-image.bin backup.bin"; exit 1; }
[ "$(stat -c %s "$IMG")" = 1048576 ] || { echo "The image must be exactly 1 MB."; exit 1; }
[ "$(stat -c %s "$BACKUP")" = 2097152 ] || { echo "The backup must be exactly 2 MB."; exit 1; }
[ "$(dd if="$IMG" bs=1 skip=54 count=3 status=none)" = "FAT" ] || { echo "The image is not a FAT volume."; exit 1; }
[ "$(dd if="$BACKUP" bs=1 skip=$((0x100000 + 54)) count=3 status=none)" = "FAT" ] || {
  echo "The backup has no FAT volume at 0x100000 - unknown layout, stopping."; exit 1; }
sunxi-fel version | grep -q "F1C100s" || { echo "No F1C100s in FEL mode found."; exit 1; }
sunxi-fel spiflash-info | grep -q "size: 2097152" || { echo "Unexpected flash size, stopping."; exit 1; }
echo "Writing $IMG to 0x100000 ..."
sunxi-fel spiflash-write 0x100000 "$IMG"
TMP="$(mktemp -d)"
sunxi-fel spiflash-read 0x100000 1048576 "$TMP/fs.bin"
if cmp -s "$TMP/fs.bin" "$IMG"; then echo "VERIFIED: file system matches $IMG"; else echo "MISMATCH after writing!"; exit 2; fi
# Boot code + firmware end at 0xE0000; the panel Data Flash (0xE0000-0xE3FFF) changes at runtime.
sunxi-fel spiflash-read 0 917504 "$TMP/fw.bin"
if [ "$(head -c 917504 "$BACKUP" | sha256sum | cut -d' ' -f1)" = "$(sha256sum < "$TMP/fw.bin" | cut -d' ' -f1)" ]; then
  echo "Boot code and firmware unchanged."
else
  echo "WARNING: boot code/firmware differ from $BACKUP."
fi
rm -rf "$TMP"
echo "Done. Power the panel off, remove the FEL card, power it on."
