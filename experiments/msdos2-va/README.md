# MS-DOS 2.0 for the PC-88VA (English distribution disk)

This directory builds a bootable PC-88VA 2HD disk with Microsoft MS-DOS 2.0
(the MIT-licensed release in `microsoft/MS-DOS`) and a PC-88VA BIOS part. It
is a separate experiment of the FreeDOS-88VA project, not a FreeDOS milestone
and not part of any milestone build. It is unofficial and not supported by
Microsoft or NEC.

Validation: emulator only (VAEG). Hardware is NOT RUN.

## What is built

| Part | Source |
|---|---|
| IO.SYS | `v2.0/pc88va/VAIO.ASM` (PC-88VA BIOS part, derived from `SKELIO.ASM`) linked with the Microsoft-supplied `v2.0/bin/SYSINIT.OBJ` and `SYSIMES.OBJ` |
| Boot sector, FORMAT, SYS | `pc88va/VABOOT.ASM`, `VAFORMAT.ASM`, `VASYS.ASM` (shared with the MS-DOS 4.0 disk) |
| MEMINFO | `pc88va/MEMINFO.ASM` (memory layout report; DOS 2.0 has no MEM) |
| MSDOS.SYS, COMMAND.COM, CHKDSK, DEBUG, DISKCOPY, EDLIN, EXE2BIN, FC, FIND, MORE, RECOVER, SORT | Microsoft-supplied `v2.0/bin` binaries |

The project sources are on the `release/msdos-va` branch of
[FreeDOS-88VA/MS-DOS](https://github.com/FreeDOS-88VA/MS-DOS/tree/release/msdos-va);
`lock.json` pins its commit, the emu2 commit and the SHA-256 of every
Microsoft-supplied input. MASM 5.10 and LINK 3.65 from `v4.0/src/TOOLS` run
under emu2 built from its pinned source.

The published 2.0 source tree cannot rebuild MSDOS.SYS, COMMAND.COM or the
utilities: `IO.ASM` included by `STDIO.ASM` is missing, the `context` macro
is undefined, some modules use 2.11-era symbols, CHKDSK and PRINT do not
assemble, and the utilities that do assemble differ from the release
binaries. With the owner's approval, the disk therefore uses the release
binaries for these parts, as the 2.0 README describes for OEMs. They contain
no IBM PC BIOS calls. SYS and FORMAT are replaced by the PC-88VA programs;
PRINT is not included because PRN output is discarded.

## PC-88VA BIOS part

CON uses the ROM text BIOS and the primitive keyboard queue (ASCII keys only);
CLOCK reads and sets the calendar clock; AUX and PRN discard output; drives
A: and B: are the 2HD floppy drives (1024-byte sectors, 8 per track, 80
cylinders, 2 heads) through the ROM floppy BIOS. Conventional memory is
measured at boot; backup-memory settings are not read. Device requests run on
a private stack and clear DF on return; SYSINIT keeps the boot stack. The boot
sector finds IO.SYS and MSDOS.SYS through the FAT.

## Build

Requires git, make, a C compiler and Python 3.12 on the host.

```sh
git submodule update --init components/msdos components/emu2
git -C components/msdos fetch origin release/msdos-va
python3 -B experiments/msdos2-va/build.py --output build/msdos2-va
```

The disk is `build/msdos2-va/msdos2-pc88va-2hd.d88`; `build-record.json`
lists the source and file digests. Two independent builds produce the same
D88 bytes. `readfile.py IMAGE NAME` copies a root-directory file out of a D88.

## Verification (VAEG)

With the distribution CONFIG.SYS (`FILES=20`, `BUFFERS=10`), CHKDSK reports
558,016 bytes free on the PC-88VA and PC-88VA2 with 640 KiB, and on the VA2
426,944, 295,872 and 164,800 bytes with 512, 384 and 256 KiB.

Exercised on the VA2: boot through the FAT, DATE from the calendar, MEMINFO,
CHKDSK (A: and B:), FORMAT B: /S /V and booting the result, DISKCOPY (the copy
is identical), RECOVER, DEBUG, EDLIN, FC, FIND, SORT, MORE, EXE2BIN, COPY and
DIR.

Not run: hardware, drive B: as the boot drive, less common options.
