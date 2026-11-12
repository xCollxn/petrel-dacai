#!/bin/bash
# Read the complete 2 MB SPI flash of a DACAI panel in FEL mode twice and compare.
# usage: fel_backup.sh [output-directory]        (needs sunxi-tools, panel in FEL mode)
# Keep the backup private: it contains the panel's firmware. Store a second copy elsewhere.
set -e
OUT="${1:-.}"
mkdir -p "$OUT"
sunxi-fel version | grep -q "F1C100s" || { echo "No F1C100s in FEL mode found."; exit 1; }
INFO="$(sunxi-fel spiflash-info)"
echo "$INFO"
SIZE="$(echo "$INFO" | sed -n 's/.*size: \([0-9]*\) bytes.*/\1/p')"
[ -n "$SIZE" ] || { echo "Could not read the flash size."; exit 1; }
STAMP="$(date +%Y%m%d-%H%M%S)"
for i in 1 2; do
  echo "Reading pass $i ($SIZE bytes) ..."
  sunxi-fel spiflash-read 0 "$SIZE" "$OUT/dacai-spi-$STAMP-$i.bin"
done
A="$(sha256sum < "$OUT/dacai-spi-$STAMP-1.bin" | cut -d' ' -f1)"
B="$(sha256sum < "$OUT/dacai-spi-$STAMP-2.bin" | cut -d' ' -f1)"
if [ "$A" != "$B" ]; then
  echo "The two reads DIFFER - do not use them. Check the USB wiring and try again."
  exit 2
fi
rm "$OUT/dacai-spi-$STAMP-2.bin"
mv "$OUT/dacai-spi-$STAMP-1.bin" "$OUT/dacai-spi-$STAMP.bin"
echo "OK: $OUT/dacai-spi-$STAMP.bin  sha256 $A"
