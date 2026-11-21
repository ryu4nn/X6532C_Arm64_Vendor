#!/bin/bash
# Build the hybrid X6532C vendor EROFS image (same filesystem type as stock).
#
# uid/gid/mode come from the extracted tree, made authoritative through
# fakeroot; SELinux labels come from the literal path map built out of the
# stock image itself.  The image is lz4 compressed because the stock vendor
# partition is compressed too and the payload has to fit in 305 MB.
set -euo pipefail

BASE=/home/randyyy/x6532c-work
WORK=$BASE/hybridimg
ROOT=$WORK/root
MKFS=$BASE/erofs-utils/mkfs/mkfs.erofs
IMG=$WORK/vendor.img
BYTES=305053696          # stock logical partition size (reference only)
COMP=${COMP:-lz4}

rm -f "$IMG" "$WORK/vendor.img.raw"

fakeroot bash -c '
set -e
cd '"$WORK"'
while IFS=$'"'"'\t'"'"' read -r p u g m; do
    chown -h "$u:$g" "root/$p"
    if [ ! -L "root/$p" ]; then chmod "$m" "root/$p"; fi
done < meta.tsv
'"$MKFS"' -b 4096 -x2 -z'"$COMP"' \
    --file-contexts=labels_map.txt --mount-point=vendor \
    '"$IMG"' root
'

echo "--- ukuran sebelum padding ---"
RAW=$(stat -c %s "$IMG")
echo "$RAW bytes"
# Partition size is rounded up to a whole MiB; the image is padded so that a
# plain dd onto the mapped partition replaces every byte of it.
PART=$(( (RAW + 1048575) / 1048576 * 1048576 ))
echo "$PART" > "$WORK/vnd_size.txt"
truncate -s "$PART" "$IMG"
echo "--- ukuran akhir (partisi) ---"
stat -c '%s bytes' "$IMG"