#!/bin/sh
# Download DejaVu fonts 2.37 (free license, see LICENSES/DejaVu.txt) into fonts/dejavu
set -e
cd "$(dirname "$0")/.."
URL=https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.tar.bz2
SHA=fa9ca4d13871dd122f61258a80d01751d603b4d3ee14095d65453b4e846e17d7
mkdir -p fonts/dejavu
tmp=$(mktemp -d)
curl -sL -o "$tmp/dejavu.tar.bz2" "$URL"
echo "$SHA  $tmp/dejavu.tar.bz2" | sha256sum -c -
tar xjf "$tmp/dejavu.tar.bz2" -C "$tmp"
cp "$tmp"/dejavu-fonts-ttf-2.37/ttf/DejaVuSans*.ttf fonts/dejavu/
rm -rf "$tmp"
echo "DejaVu fonts in fonts/dejavu"
