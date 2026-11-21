# Building the hybrid vendor image

Everything below runs unprivileged on a Linux host. The only inputs are the two
stock `vendor.img` files.

## 0. Inputs

| Path | Meaning |
|---|---|
| `stock/super.img` | X6532C SP Flash Tool package, sparse |
| `stock/vendor_a.img` | `lpunpack -p vendor_a` output, erofs, 305053696 bytes |
| `donor/vendor.img` | Honor X5b `image/vendor.img`, sparse erofs |

```sh
simg2img super.img super.raw
lpunpack -p vendor_a super.raw .
```

## 1. Read the stock partition

The stock tree is never mounted by the kernel; erofs is read in userspace.

```sh
fsck.erofs --extract=vendorstock --preserve-perms --xattrs vendor_a.img
python3 tools/dumpmeta.py vendor_a.img vendorstock fsmeta.tsv
```

`dumpmeta.py` asks `dump.erofs --path` for every entry and records the
authoritative `uid`, `gid` and `mode`. This matters because the vendor tree is
not uniformly `0:0` — 420 entries belong to `gid 2000` and a handful are `0600`,
`0444` or `0751`.

`fsck.erofs` cannot restore `security.selinux` without root, so labels are read
separately from a FUSE mount:

```sh
tools/bin/erofsfuse vendor_a.img /mnt/vendor
python3 tools/dumplabels.py /mnt/vendor labels.tsv
```

The same scan is what proves the partition carries **no**
`security.capability` xattrs, so no file capabilities have to be reproduced.

## 2. Assemble the tree

```sh
python3 tools/build_vendor.py
```

`build_vendor.py` copies the stock tree, grafts the 41 arm64 objects from
`hybrid/`, and resolves each new path against its 32-bit twin:

| New path | Identity inherited from |
|---|---|
| `lib64/egl/*` | `lib/egl/*` |
| `lib64/hw/gralloc.rogue.so` | `lib/hw/gralloc.rogue.so` |
| `lib64/mt6765/*` | `lib/mt6765/*` |
| `lib64/*.so` | `lib/*.so` |

`lib64/hw/vulkan.mt6765.so` has no 32-bit twin and takes
`u:object_r:same_process_hal_file:s0` from the vendor file contexts rule for
`/vendor/lib(64)?/hw/vulkan\.mt[0-9]+\.so`. Outputs:

- `meta.tsv` — path, uid, gid, mode for all 2325 entries
- `labels_map.txt` — literal `/vendor/<path> <context>`, for `mkfs.erofs`
- `file_contexts` — the same map in escaped regex form, for `e2fsdroid`

## 3. Build the image

```sh
COMP=lz4hc tools/mkimg_erofs.sh
```

`mkimg_erofs.sh` runs the metadata loop and `mkfs.erofs` under `fakeroot`, so
`lstat` reports the ownership recorded in `meta.tsv` without any privileges.
Labels come in through the patched `--file-contexts`, with `--mount-point=vendor`
so lookups use `/vendor/...` paths.

Compression is `lz4hc` because the stock partition is lz4-compressed and the
resulting image has to stay in the same size class; `lzma` and `zstd` are not
available to a 5.10 kernel.

The image is padded up to a whole MiB to become the new partition size
(321912832 bytes). The stock partition (305053696) is too small: the 41 added
objects add 60 MB of data, which is 38 MB after compression.

## 4. Verify

```sh
fsck.erofs vendor.img
tools/bin/erofsfuse vendor.img /mnt/new
python3 tools/verify.py /mnt/new
```

`verify.py` walks the built image and compares, for every entry, the SELinux
label against `labels_map.txt`, the `uid`/`gid`/`mode` against `meta.tsv`, and
the contents against `vendorstock` or `hybrid`. Any deviation is printed and the
exit status is non-zero.

## 5. Package

`update-binary` grows `vendor$SLOT` through the recovery's `lptools`
(`resize`, falling back to `remove` + `create`), maps it, and streams
`vendor.img.xz` onto `/dev/block/mapper/vendor$SLOT`.

```
META-INF/com/google/android/update-binary
META-INF/com/google/android/updater-script   (empty)
META-INF/xz                                  static 32-bit ARM xz
vendor.img.xz
```

`VND_SIZE` in `update-binary` must be kept in sync with `vnd_size.txt`.

## Host toolchain

| Tool | Source |
|---|---|
| `erofs-utils` 1.9.4 + patch | `patches/` |
| `fsck.erofs`, `dump.erofs` | same tree |
| `erofsfuse` | same tree, `./configure --enable-fuse` |
| `fakeroot` | distribution package |
| `lpunpack`, `lpdump`, `simg2img` | `android-sdk` / AOSP partition tools |