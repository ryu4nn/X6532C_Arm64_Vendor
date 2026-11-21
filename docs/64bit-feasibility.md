# X6532C 64-bit feasibility audit (2026-11-21)

## Reference zip: Arm64_Vendor_V2.1.zip

Extracted `vendor.img` (EROFS, 817.5 MiB, flash target 857,227,264 B).

| Property | Value |
|---|---|
| ro.product.vendor.device | Infinix-X6532 (Smart 9, not the HD) |
| ro.board.platform | **mt6768** |
| GPU kernel modules | mali_kbase_mt6768.ko, mali_mgm_mt6768.ko |
| Kernel module vermagic | 5.10.209-android12-9-05394-g76c5c8124950-dirty |
| Modules | 206 |
| lib32 / lib64 | 771 / 736 |
| zygote | zygote64_32 |
| init | init.mt6768.rc |
| VNDK | 31 |
| EGL | libGLES_mali.so (64-bit, 38 MB) + meow shim |
| Build path | out_vnd/target/product/x6531_v631 (Hot 50i port) |

Incompatible with X6532C: different SoC (mt6765), GPU (PowerVR GE8320 vs Mali-G52),
kernel vermagic (5.10.237 vs 5.10.209), init/modem/ISP sets.

## X6532C stock vendor

- ro.board.platform=mt6765, ro.zygote=zygote32, VNDK 31, vendor build 2026-04-17.
- lib32 721, lib64 3 (audio effect, sensor).
- PowerVR userspace: libEGL_mtk.so, libGLESv2_mtk.so, libGLES_meow.so,
  libMEOW_*.so, libIMGegl.so, libglslcompiler.so, libgpud.so, libgpu_aux.so,
  libged.so.
- DDK version 1.15@6070602.
- Kernel module: `vendor/lib/modules/pvrsrvkm_mt6765.ko` =
  `Rogue_DDK_Android rogueddk 1.15@6070602`, vermagic 5.10.237-android12-9-g12e06e225ce7-dirty.
- KM string: "(FAIL) ... Incompatible driver DDK version (%u.%u) / client DDK version (%u.%u)"
  and `PVRSRV_ERROR_DDK_VERSION_MISMATCH`.

## 64-bit MT6765 donor scan

All public 64-bit MT6765 (PowerVR GE8320) vendor trees found:

| Dump | Build | DDK | zygote |
|---|---|---|---|
| Realme RMX2185 / Teracube 2e | 2020-2021 | 1.11@5425693 | 64 |
| vivo 2120, Moto borag/E22 | 2022 | 1.13@5776728 | 64 |
| onn. tablet (mt6765) | 2023 | 1.13@5776728 | 64_32 |
| Lenovo x6c6l | 2024-01 | 1.13@5776728 | 64_32 |
| Umidigi G9C (Note 90C) | 2024-12 | 1.13@5776728 | 64_32 |
| Rabbit R1 (k65v1) | 2025-05 | 1.13@5776728 | 64 |
| Samsung Galaxy A03 vendor | 2025-05 | 1.13@5776728 | 64_32 |
| Redmi 9A MIUI 14 | 2025-12 | 1.13 (32-bit userland) | 32 |

No public 64-bit MT6765 client with DDK 1.15@6070602 was found. MTK's 64-bit
MT6765 BSPs stop at 1.13; the X6532C's 2026 vendor carries the newer 1.15 DDK.

## Correction (2026-11-22): Teracube is NOT 1.15

Both Teracube Android 16 full images were pulled from downloads2.myteracube.com
and unpacked (super.img -> simg2img -> lpunpack vendor_a -> fsck.erofs):

| Dump | SoC | Kernel BSP | Userland | DDK in vendor lib64 |
|---|---|---|---|---|
| Teracube 2s / sapphire, 16.2.1 | mt6765 | m1.13ED5776728 | arm64 | **1.13@5776728** |
| Teracube 2e / emerald, 16.3.1 | mt6765 | (4.19) | arm64 | **1.13@5776728** |

`grep -la 6070602` over the whole sapphire vendor tree returns nothing. The
earlier "sapphire uses gpu_rgx/m1.15ED6070602" note was wrong: the actual tree
at `Teracube-Inc/kernel_teracube_mt6765-4.19:drivers/gpu/mediatek/gpu_rgx/`
contains `m1.13ED5776728`. The DDK depends on the **kernel BSP version**, not on
the Android version - Teracube kept its 4.19 BSP through Android 16.

Criterion therefore: MT6765 on a **kernel 5.10** BSP (MTK "android12-9" line)
=> GPU drop m1.15ED6070602. The X6532C itself is such a device.

## Confirmed 1.15 arm64 donor: Honor X5b / X6a

Honor X5b = GFY-LX2, Honor X6a = WDY-LX2. Helio G36 = **MT6765V/XBA**,
PowerVR **Rogue GE8320**, Android 14 / MagicOS 8, kernel
5.10.226-android12-9-00064-gea4a6f067d3f-ab12969919, ABIs
`arm64-v8a, armeabi, armeabi-v7a`, dynamic partitions, A/B.

Runtime reports from two independent Device Info DBs (deviceinfohw.ru and
specdeviceinfo.com, both reading `GPU_VERSION` off real units):

    GPU_VERSION  3.2 build 1.15@6070602
    PLATFORM     mt6765
    CPU          MT6765V/XBA

That is an exact match for the X6532C kernel module
(`Rogue_DDK_Android rogueddk 1.15@6070602`).

Firmware is downloadable free and without quotas from Honor's own CDN via the
public iknow servlet. Working example (GFY-LX2 8.0.0.540, 4.7 GB zip):

    curl -L -o x5b.zip \
      "https://iknow.service.hihonor.com/weknow/servlet/download/public?contextNo=W00060434"

The servlet 302-redirects to `iknow-dl.service.hihonor.com/.../downloadServlet/<token>.zip`
(HEAD on the CDN URL returns 403; a GET follows it fine). A catalogue of
16752 model/version -> contextNo links lives in the gist
`0x8008/3ef2413fbd09648b0c02a0d1cf585d22` (`honor.md`); local copy at
`donor_honor/honor_links.md`. Relevant rows:

    GFY-L32 8.0.0.540  contextNo=W00060434   (X5b, newest)
    GFY-L32 8.0.0.542  contextNo=W00063929
    GFY-L03 8.0.0.379  contextNo=W00065189
    WDY-L03 8.0.0.367  contextNo=W00065240   (X6a)
    WDY-L13 8.0.0.367  contextNo=W00065250

Package is a plain zip with `ReleaseDoc/` (release notes, SD card upgrade
instructions) plus the firmware payload; extract with `tools/splituapp` (for
UPDATE.APP) or `tools/update-extractor.py`.

## Kernel needed? No

`vendor/lib/modules/pvrsrvkm_mt6765.ko` on the X6532C is
`ELF 64-bit LSB relocatable, ARM aarch64`. The UM/KM version check compares DDK
version strings (1.15 vs 1.15), not word size. The same module already serves
32-bit clients via compat ioctls and will serve 64-bit clients unchanged.
So the 64-bit work is entirely userspace; no kernel rebuild, no donor kernel.

## Consequence

A drop-in 64-bit vendor for X6532C does not exist. Flashing the mt6768 zip
would fail (modules/vermagic/GPU). Using a 1.13 64-bit client with the 1.15
kernel module is rejected by the KM version check; patching the check bypasses
the guard but the UM/KM ABI differs between 1.13 and 1.15, so GPU
init/hangs/crashes are likely.

Path now: take the 64-bit GL/EGL stack out of the Honor X5b vendor (targeting
exactly DDK 1.15@6070602) and graft it onto the X6532C vendor, keeping every
32-bit MTK HAL in place. Baseline LineageOS 19.1 32-bit remains the stable
target until that hybrid boots.