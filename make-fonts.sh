#!/bin/sh -ex
fonttools ttx -o Inconsolata.ttx ~/Library/Fonts/Inconsolata-dz.otf
sed 's|</ttFont>||g' Inconsolata.ttx > Inconsolata_tmp.ttx
for i in ttx/*.ttx; do
  BASE="$(basename $i .ttx)"
  cat Inconsolata_tmp.ttx $i > Inconsolata.ttx
  fonttools ttx -o Inconsolata.otf Inconsolata.ttx
  pyftsubset Inconsolata.otf --text="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-" --drop-tables+=FFTM --output-file=Inconsolata-${BASE}.woff2 --flavor=woff2 --prune-unicode-ranges --no-hinting --gids=0,1 --notdef-outline --layout-features='' --with-zopfli
  pyftsubset Inconsolata.otf --text="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-" --drop-tables+=FFTM --output-file=Inconsolata-${BASE}.woff --flavor=woff --prune-unicode-ranges --no-hinting --gids=0,1 --notdef-outline --layout-features='' --with-zopfli
  rm -f -- Inconsolata.otf
done
rm -f -- Inconsolata_tmp.ttx
rm -f -- Inconsolata.ttx
