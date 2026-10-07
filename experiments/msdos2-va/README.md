# Experiment: MS-DOS 2.0 on the PC-88VA

This experiment boots Microsoft MS-DOS 2.0 (the MIT-licensed release in
`microsoft/MS-DOS`) on the PC-88VA to compare its conventional-memory use
with the FreeDOS port. It is not a milestone, not a distribution and not part
of any milestone build. Results are emulator-only; hardware is NOT RUN.

## What is built

| File | Source |
|---|---|
| Boot sector | `v2.0/pc88va/VABOOT.ASM` (project-authored) |
| IO.SYS | `v2.0/pc88va/VAIO.ASM` (derived from `v2.0/source/SKELIO.ASM`), linked with the Microsoft-supplied `v2.0/bin/SYSINIT.OBJ` and `SYSIMES.OBJ` |
| MSDOS.SYS, COMMAND.COM | Microsoft-supplied `v2.0/bin` binaries of the same release |
| MEMINFO.COM | `v2.0/pc88va/MEMINFO.ASM` (project-authored) |

The project sources live on the `experiment/msdos2-va` branch of
[FreeDOS-88VA/MS-DOS](https://github.com/FreeDOS-88VA/MS-DOS/tree/experiment/msdos2-va);
`lock.json` pins its commit, the emu2 commit and the SHA-256 of every
Microsoft-supplied input. MASM 5.10 and LINK 3.65 from `v4.0/src/TOOLS` run
under emu2 built from source.

The published 2.0 source tree cannot rebuild MSDOS.SYS or COMMAND.COM: the
DOS character I/O module `IO.ASM` included by `STDIO.ASM` is missing, the
`context` macro used by several modules is undefined, and some modules
reference 2.11-era symbols. The source `SYSINIT.ASM` is likewise a later
revision than the shipped `SYSINIT.OBJ`. The experiment therefore uses the
release binaries for the machine-independent parts, as the 2.0 README
describes for OEMs, and builds only the PC-88VA parts from source.

## PC-88VA BIOS part

- Console output uses the ROM text BIOS (INT 83h); CR, LF, BS and printable
  ASCII are passed, other control codes are dropped.
- Keyboard input reads the primitive KB queue (INT 82h, functions 0Ah and
  09h), which bypasses the ROM Japanese front-end processor; the standard
  functions 00h/01h called into an uninitialized front-end pointer.
- Drives A: and B: use the ROM floppy BIOS (INT 80h) with the same 2HD
  1024-byte format as the FreeDOS disks.
- Conventional memory is measured at boot in 64 KiB steps; backup-memory
  settings are not read.
- AUX and PRN discard output; CLOCK keeps the last date and time set.
- IO.SYS is loaded at 1000:0000, the same base as the FreeDOS kernel, and
  nothing is placed below it.

Three integration defects were found and fixed: the ROM 1.0 text BIOS can
return with DF set (DOS string instructions then ran backwards); the DOS 2.0
stack is too shallow for the ROM services (requests now run on a private
512-byte stack); and SYSINIT keeps using the stack it inherits while it moves
MSDOS.SYS over the IO.SYS initialization code, so that stack must lie outside
IO.SYS (the boot stack at 3000:1000 is kept).

## Build

Requires git, make, a C compiler and Python 3.12 on the host (no
milestone container or toolchain is used).

```sh
git -C components/msdos fetch origin experiment/msdos2-va
python3 -B experiments/msdos2-va/build.py --output build/exp-msdos2-va
python3 -B experiments/msdos2-va/readfile.py IMAGE.d88 MEMINFO.TXT
```

Two independent builds produce the same D88 bytes. The disk boots to
`A>` after AUTOEXEC.BAT runs `MEMINFO > MEMINFO.TXT` and `MEMINFO`.

## Result (VAEG, VA and VA2, 640 KiB, no backup memory)

Both models give the same layout:

| Start | Contents | Bytes |
|---|---|---:|
| 10000h | IO.SYS resident part, including the 512-byte request stack | 1,392 |
| 10570h | MSDOS.SYS code, data, buffers and file tables, up to the first MCB at 148C0h | 17,232 |
| 148D0h | System block (owner 0008h) | 1,168 |
| 14D70h | COMMAND.COM resident part | 2,752 |
| 15840h | COMMAND.COM environment | 160 |
| 15960h | First program (PSP 1596h), memory block to A0000h | 566,944 |

Each block is preceded by its 16-byte MCB.

For comparison, FreeDOS M20 (release candidate 5) on the VA2 with 640 KiB
reports 507,216 bytes for the largest executable program with the swapping
FreeCOM. The MS-DOS 2.0 configuration is much smaller in function: default
BUFFERS=2 and FILES=8, no CONFIG.SYS, no Japanese console, no ANSI escape
sequences, stub AUX/PRN and a clock that does not read the calendar.

Verified in VAEG: boot, AUTOEXEC.BAT, keyboard commands (`DIR`, `COPY`),
redirected file creation and readback on the VA and the VA2. Not run:
512, 384 and 256 KiB, drive B:, hardware.
