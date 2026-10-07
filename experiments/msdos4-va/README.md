# Experiment: MS-DOS 4.0 on the PC-88VA

This experiment boots Microsoft MS-DOS 4.0 (the MIT-licensed release in
`microsoft/MS-DOS`) on the PC-88VA to compare its conventional-memory use
with the FreeDOS port. It is not a milestone, not a distribution and not part
of any milestone build. Results are emulator-only; hardware is NOT RUN.

## What is built

Everything is assembled from source with the original MS-DOS 4.0 tools
(BUILDIDX, BUILDMSG, NOSRVBLD, MASM 5.10, LINK 3.65, EXE2BIN) running under
emu2 built from its pinned source:

| File | Source |
|---|---|
| MSDOS.SYS | `v4.0/src/DOS` and `v4.0/src/INC`, unchanged, linked as in `MSDOS.LNK` |
| IO.SYS | `v4.0/pc88va/VAIO.ASM` (project-authored BIOS part) + `v4.0/src/BIOS` SYSINIT1, SYSCONF, SYSINIT2, SYSIMES |
| COMMAND.COM | `v4.0/src/CMD/COMMAND` with `PC88VA` defined (CLS uses the VA text BIOS instead of IBM INT 10h) |
| Boot sector, MEMINFO.COM | `v2.0/pc88va/VABOOT.ASM` and `MEMINFO.ASM`, shared with the MS-DOS 2.0 experiment |

The sources are on the `experiment/msdos4-va` branch of
[FreeDOS-88VA/MS-DOS](https://github.com/FreeDOS-88VA/MS-DOS/tree/experiment/msdos4-va);
`lock.json` pins its commit, the emu2 commit and the SHA-256 of every tool.
The IBM PC BIOS part of IO.SYS (MSBIO1 ... MSINIT) and its loader MSLOAD are
not used: the boot sector loads IO.SYS and MSDOS.SYS as in the 2.0
experiment. The build overlays the INC, DOS and BIOS directories per
assembly unit in the original include order and gives the tools CRLF text;
NOSRVBLD does not accept LF-only message skeletons.

## PC-88VA changes

`v4.0/pc88va/VAIO.ASM` is the 2.0 experiment BIOS (INT 83h console, primitive
INT 82h keyboard queue, INT 80h 2HD floppy drives A: and B:, boot-time memory
measurement, private request stack, DF cleared on return, boot stack kept
during initialization) with what the 4.0 SYSINIT needs from the BIOS part:
its public variables (hardware-stack, MULTITRACK, 3.5-inch drive and
keyboard-function flags, all unused here), an extended BPB and the `CLOCK$`
name. DOS 4.0 points INT 2Ah-3Fh at its own handlers; `RE_INIT` gives INT 33h
back to the ROM mouse BIOS.

With `PC88VA` defined, `SYSINIT1.ASM` skips three IBM PC dependencies whose
interrupt numbers and ports mean something else on the PC-88VA: the INT 15h
(AH=C0h) and INT 11h configuration probes, the INT 15h (AH=88h) extended
memory query and the shared-interrupt rearm writes to ports 2F2h-2F7h and
6F2h-6F7h. The default model byte 0FFh is kept, so no hardware stacks are
installed unless `STACKS=` is given. MSDOS.SYS is unchanged.

## Build

Requires git, make, a C compiler and Python 3.12 on the host.

```sh
git -C components/msdos fetch origin experiment/msdos4-va
python3 -B experiments/msdos4-va/build.py --output build/exp-msdos4-va
python3 -B experiments/msdos4-va/readfile.py IMAGE.d88 MEMINFO.TXT
```

Two disks are produced: `default` without CONFIG.SYS and `matched` with the
FreeDOS M20 settings `FILES=16`, `BUFFERS=6` (the effective FreeDOS value),
`STACKS=0,0` and `LASTDRIVE=E`. Two independent builds produce the same D88
bytes. Both disks boot to `A>` after AUTOEXEC.BAT runs
`MEMINFO > MEMINFO.TXT` and `MEMINFO`.

## Result (VAEG, VA and VA2, 640 KiB, no backup memory)

Both models give the same layout for each disk:

| Start | Contents | default | matched |
|---|---|---:|---:|
| 10000h | IO.SYS resident BIOS part, including the 512-byte request stack | 1,504 | 1,504 |
| 105E0h | MSDOS.SYS code and data, up to the first MCB at 193E0h | 36,352 | 36,352 |
| 193F0h | System block (owner 0008h: buffers, files, FCBs, current directories) | 16,640 | 7,712 |
| | COMMAND.COM resident part | 5,696 | 5,696 |
| | COMMAND.COM second block (3 paragraphs) | 48 | 48 |
| | COMMAND.COM environment | 160 | 160 |
| | First program, memory block to A0000h | **529,280** | **538,208** |

Each block is preceded by its 16-byte MCB. The first program starts at
1EC80h (default) or 1C9A0h (matched).

For comparison, FreeDOS M20 (release candidate 5) on the VA2 with 640 KiB
reports 507,216 bytes for the largest executable program with the swapping
FreeCOM, and 506,352 bytes free with the MS-DOS 4 COMMAND.COM shell. This
MS-DOS 4.0 configuration has no Japanese console, ANSI escape sequences,
AUX/PRN output or calendar clock.

Verified in VAEG: boot, AUTOEXEC.BAT, keyboard commands (`DIR`, `COPY`),
redirected file creation and readback on the VA and the VA2 for both disks.
Not run: 512, 384 and 256 KiB, drive B:, CONFIG.SYS options beyond the
matched set, hardware.
