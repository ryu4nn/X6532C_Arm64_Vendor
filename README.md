# Arm64 Vendor for the Infinix Smart 9 HD (X6532C)

A hybrid `vendor` partition for the Infinix Smart 9 HD **X6532C** that keeps the
device's own 32-bit MediaTek HALs and grafts a **64-bit PowerVR user-mode
driver** on top of them, so an arm64 Android userspace can reach the GE8320.

The stock vendor partition is 32-bit only: of 724 shared objects it ships, 721
are `armeabi-v7a` and just 3 are `arm64-v8a` (accelerometer/audio effect
helpers). With the stock image `ro.zygote=zygote32` and an empty `abilist64`,
no `arm64-v8a` application can run, and a 64-bit ROM has no EGL driver to load.

## Device specifications

| | |
|---|---|
| Device | Infinix Smart 9 HD |
| Model | X6532C |
| SoC | MediaTek MT6765 (Helio G50), 4× Cortex-A53 + 4× Cortex-A53 |
| GPU | Imagination PowerVR GE8320 |
| Stock OS | Android 14 Go, XOS 14 |
| Kernel | 5.10.237-android12-9, `aarch64` |
| Stock vendor | erofs, lz4-compressed, 291 MiB, VNDK **31** (SDK 31) |
| Stock userspace | `armeabi-v7a` only, `ro.zygote=zygote32` |
| Partitions | dynamic (super), A/B, virtual A/B |

## What the image contains

| Source | Arch | Role |
|---|---|---|
| Stock X6532C `vendor.img` | arm | every file of the original partition, unchanged |
| Honor X5b (GFY-LX2) `vendor.img` | arm64 | 41 PowerVR user-mode objects under `lib64/` |

Both sides carry the **same GPU driver generation**, `Rogue_DDK_Android
rogueddk 1.15@6070602`, and the same VNDK level (31), so the kernel module's
`PVRSRV_ERROR_DDK_VERSION_MISMATCH` check passes and the UM/KM ioctl ABI agrees.

Nothing in the stock partition is removed, rewritten or relabelled. The 41
additions are the only difference.

<details>
<summary>Added objects (41 files + 3 symlinks)</summary>

```
lib64/egl/libEGL_mtk.so              lib64/libion_mtk.so
lib64/egl/libGLES_meow.so            lib64/libion_ulit.so
lib64/egl/libGLESv1_CM_mtk.so        lib64/libladder.so
lib64/egl/libGLESv2_mtk.so           lib64/libNoFpsActor.so
lib64/egl/libMEOW_data.so            lib64/libPVRMtkutils.so
lib64/egl/libMEOW_gift.so            lib64/libPVROCL.so
lib64/egl/libMEOW_qt.so              lib64/libPVRScopeServices.so
lib64/egl/libMEOW_trace.so           lib64/libsrv_um.so
lib64/hw/gralloc.rogue.so            lib64/libufwriter.so
lib64/hw/vulkan.mt6765.so            lib64/libusc.so
lib64/mt6765/libdpframework.so       lib64/vendor.mediatek.hardware.mms@1.0.so
lib64/mt6765/libmtk_drvb.so          lib64/vendor.mediatek.hardware.mms@1.1.so
lib64/mt6765/libpq_prot.so           lib64/vendor.mediatek.hardware.mms@1.2.so
lib64/libDefaultFpsActor.so          lib64/vendor.mediatek.hardware.mms@1.3.so
lib64/libdrm.so                      lib64/vendor.mediatek.hardware.mms@1.4.so
lib64/libFrameRecord.so              lib64/vendor.mediatek.hardware.mms@1.5.so
lib64/libged.so                      lib64/vendor.mediatek.hardware.pq@2.0.so
lib64/libglslcompiler.so
lib64/libgpu_aux.so
lib64/libgpud.so
lib64/libgralloc_extra.so
lib64/libgralloc_metadata.so
lib64/libgralloctypes_mtk.so
lib64/libIMGegl.so
```

`lib64/libdpframework.so`, `lib64/libmtk_drvb.so` and `lib64/libpq_prot.so` are
symlinks to `mt6765/`, matching the stock `lib/` layout.
</details>

## Why the vendor partition and not the ROM

The EGL driver is discovered through `ro.hardware.egl` inside the *sphal*
linker namespace, whose permitted paths are `/vendor/${LIB}` and `/odm/${LIB}`
only. `libEGL` additionally probes a hard-coded list of directories that starts
at `/odm/lib64/egl` and `/vendor/lib64/egl`. There is no ODM partition on this
device, so `/vendor/lib64/egl` is the only place a 64-bit driver can live.

The 64-bit objects therefore have to travel as a vendor image, which is also why
they are shipped as a separate flashable archive instead of a ROM build product:
the ROM never writes the `vendor` partition.

## Provenance of the 64-bit half

| | |
|---|---|
| Donor | Honor X5b (GFY-LX2, `k65v1_64_bsp_k510`) |
| Firmware | `GFY-L32 8.0.0.540`, official Honor CDN |
| Donor vendor | VNDK 31, `ro.zygote=zygote64_32`, `abilist64=arm64-v8a` |
| Donor kernel | 5.10.226-android12-9, same MTK BSP generation |
| DDK | `1.15@6070602` — identical to stock X6532C |

DDK versions are pinned by the kernel BSP line, not by the Android release, so
a newer Android build on an older BSP is not a valid donor. The Teracube
sapphire/emerald Android 16 vendors, for example, are `1.13@5776728` and cannot
be used here; see `docs/64bit-feasibility.md` for the audit.

## Installation

Two routes, both requiring an unlocked bootloader and verification already
disabled for the slot (which any custom ROM on this device requires anyway).

### Recovery archive (recommended)

```
ryu4nn-X6532C-Arm64-Vendor-<version>.zip
```

The archive grows `vendor$SLOT` from 291 MiB to 307 MiB through the recovery's
own `lptools` (the stock partition is too small for the added objects), maps it
and streams the image onto it. Requires OrangeFox/TWRP built with
`TW_INCLUDE_LPTOOLS` and `TW_INCLUDE_FASTBOOTD`, which is what
`android_device_infinix_X6532C_ofrp` produces.

### fastbootd

```
fastboot delete-logical-partition vendor_a
fastboot create-logical-partition vendor_a 321912832
fastboot flash vendor_a vendor.img
```

Use `vendor_b` for slot `_b`. The image is `321912832` bytes.

Flash this **after** the ROM, or after any ROM update that recreates the
super partition.

## Build

Fully reproducible from the two stock vendor images; see `docs/BUILD.md`.

```
tools/build_vendor.py       assemble the tree, derive metadata + labels
tools/mkimg_erofs.sh        build the lz4 erofs image
tools/verify.py             compare the result against the stock image
```

`patches/erofs-utils-1.9.4-simple-file-contexts.patch` teaches `mkfs.erofs` to
apply SELinux labels from a literal path→context map. It exists because the
build host has no root (so `security.selinux` xattrs cannot be written to the
source tree) and no libselinux (so upstream `--file-contexts` is unavailable).

## Verification

The image is checked against the stock partition, entry by entry:

| Check | Result |
|---|---|
| SELinux labels | 2325/2325 identical |
| uid/gid/mode | 2136/2325 identical |
| File contents (sha1) | 2034/2034 identical |
| Stock entries present | 2325/2325 |
| `fsck.erofs` | clean |

The 189 differences are symlink modes: `mkfs.erofs` stores `0777` for symlinks
while the stock image stores `0755`. Linux ignores permission bits on symlinks,
so this has no runtime effect.

## Known risks

- **MTK gralloc handle layout.** The 64-bit `libgralloc_extra.so` must agree
  with the 32-bit `android.hardware.graphics.allocator@4.0-service-mediatek` on
  the private fields it appends to `native_handle`. Donor and stock builds are
  17008 and 17056 bytes respectively — same interface generation, but not
  byte-identical.
- **`ro.hardware.egl`.** The stock value is `mtk`; the donor's is `meow`. Both
  names resolve to the same `libEGL_mtk.so` + `libGLES_meow.so` pair present in
  this image, and the property is left untouched.
- **64-bit OpenCL** (`libPVROCL.so`) is included but unverified; the 32-bit one
  used by the stock HALs is untouched.
- **Verification.** The image is unsigned. If the slot still enforces AVB,
  `vendor` will not mount.

## Credits

- Vendor base: Infinix X6532C firmware `260417V1675`.
- 64-bit PowerVR userspace: Honor X5b `GFY-L32 8.0.0.540` (official CDN).
- Flashable-archive layout modelled on *Chongkessob's* `Arm64_Vendor_V2.1.zip`;
  the bundled static `xz` binary comes from that archive.