# M20 survey: FreeDOS 1.4 Floppy Edition packages for a PC-88VA floppy set

Status: survey only. Nothing here is a build input or a qualification; every
inclusion still needs a source pin, a reproducible build in the M20 pipeline
and a VAEG run. Language scope: English first; Japanese is a later stage.

## Why not reuse the Floppy Edition directly

The FreeDOS 1.4 Floppy-Only Edition (archive SHA-256
`45b1fa7c52dd996c3bfa5e352ffcd410781b952a6ad629f15a4c9ec4bbaefc5a`) cannot
be used as is on the VA:

- its installer (`SETUP.BAT` with the V8Power tools) needs PC EGA/VGA text
  services, and the packages are stored in installer-specific `freedos.NNN`
  slice archives;
- its images are 1.44 MB / 1.2 MB / 720 KB with 512-byte sectors; the VA set
  uses the M20 native 2HD format (1024-byte sectors, ~1.25 MB);
- many packages drive PC hardware or BIOS directly;
- it installs to a hard disk, and the VA port has no hard-disk boot path.

A VA set therefore re-selects programs, builds them from source in the M20
pipeline and writes VA-format disks; a plain copy script replaces the
installer.

## Method

- The package list (68 names) was read from the plain-text headers of the
  Floppy Edition slice archives.
- Package zips were downloaded from the public FreeDOS 1.4 repository
  (`https://www.ibiblio.org/pub/micro/pc-stuff/freedos/files/repositories/1.4/`,
  `listing.csv` SHA-256
  `fd5addcb197f960846c0924ad62521e96e529a334d1405985e576bb6064e53d4`). The
  repository has been updated since the release, so versions below are the
  current repository versions, not necessarily the exact Floppy Edition
  builds. `fdinst` and `shsufdrv` are absent from the current listing.
- `tools/m20/floppy_survey.py` records license, source presence, languages,
  build-tool mentions, binary size and heuristic PC-hardware hits in the
  source (PC BIOS INT 10h/13h/15h/16h/17h/1Ah, BIOS data area, direct video
  memory, port I/O). Hits flag code for review only.
- Toolchains available and pinned in M20 today: Open Watcom 1.9, NASM 2.15,
  JWasm (component). Turbo/Borland C, TASM, MASM and Pascal compilers are
  not part of the pinned toolchain; a package whose only build path needs
  them requires either a build port to Open Watcom/NASM or a separately
  pinned, publicly obtainable toolchain.

All 66 surveyed packages include source.

## Classification

Classes: **A** likely to run on the VA unchanged (DOS services only; at most
trivial findings); **B** small VA adaptation (a few PC BIOS calls, usually a
key wait or prompt, replaceable as done for FreeCOM); **C** needs a larger
port (full-screen UI or video layer); **X** not applicable to the VA (PC
hardware, 286/386-only, CD-ROM, network, hard-disk tools, PC
keyboard/video/codepage drivers, the PC installer); **M20** already provided
by the M20 disk.

| Package | Version | License | Class | Toolchain in hand? | Notes |
| --- | --- | --- | --- | --- | --- |
| append | 5.0-0.7 | GPL-2 | A | NASM: yes | TSR path append |
| assign | 1.4a | GPL-2 | A | check (no build file found) | one INT 10h hit to review |
| attrib | 2.1a | GPL-2 | A | Turbo C only: port | |
| callver | 2007-08-19a | PD | A | check | version reporting TSR |
| choice | 4.4a | GPL-2 | B | OW: yes | key wait/timeout via INT 16h and BIOS data area |
| comp | 1.04a | MIT | A | check | |
| deltree | 1.02g | GPL-2 | B | check | INT 16h confirmation prompt |
| devload | 3.25a | GPL-2 | A | NASM: yes | one INT 10h hit to review |
| exe2bin | 1.5a | OWPL-1.0 | A | Turbo C/TASM: port | |
| fc | 3.03a | GPL-2 | A | check | |
| find | 3.0b | GPL-2 | A | OW: yes | |
| label | 1.5 | GPL-2 | B | OW: yes | one INT 16h prompt |
| move | 3.5 | GPL-2 | B | OW: yes | one INT 16h prompt |
| nlsfunc | 0.4a | GPL-2 | A | NASM: yes | only useful with NLS data |
| replace | 1.2a | GPL-2 | A | Turbo C only: port | |
| share | 08/2006a | GPL | A | Turbo C only: port | TSR; needs kernel SHARE interface check |
| sort | 1.5.1a | GPL-2 | A | OW: yes | |
| swsubst | 3.2a | GPL-2 | A | Turbo C only: port | SUBST/JOIN; uses DOS internals, check against kernel |
| tree | 3.7.3 | GPL-2 | A | Turbo C/MSC: port | |
| undelete | 2008a | GPL-2 | A | Turbo C only: port | FAT access via DOS; check 1024-byte sectors |
| xcopy | 1.8b | GPL-2 | A | OW: yes | |
| gzip | 1.2.4a | GPL-2 | A | check (several makefiles) | |
| unzip | 6.00a | Info-ZIP | A | OW: yes | large; 8086 build needed |
| zip | 3.0 | Info-ZIP | A | OW: yes | large; 8086 build needed |
| debug | 2.51 | MIT | B | JWasm: yes | review its INT 10h/13h/16h use |
| diskcopy | beta 0.95 | GPL-2 | B | Turbo C/NASM: port | no BIOS hits; check 1024-byte sector media |
| diskcomp | 06jun2003 | GPL-2 | B | Turbo C only: port | INT 13h |
| print | 1.02.ea | GPL-2 | B | check | INT 17h PC printer BIOS |
| mem | 1.12 | GPL-2 | B | OW/NASM: yes | MEMMAP already covers MCB view |
| edit | 0.9b | GPL-2 | C | OW: partly | full-screen UI; its video layer is not in the package source |
| htmlhelp | 1.1.1a | GPL/FDL | C | OW: yes | full-screen UI with INT 10h/16h |
| edlin, more, format, chkdsk | | | M20 | | M20 builds EDLIN and its own MORE, FORMAT, SYS, CHKDSK |
| kernel, freecom | | | M20 | | rebuilt on 1.4 in M20 |
| ctmouse, graphics, display, cpidos, mode, keyb, mkeyb, nansi | | | X | | PC mouse/video/keyboard/codepage drivers |
| fdxms, fdxms286, himemx, jemm, cwsdpmi | | | X | | XMS/EMS/DPMI: 286/386 or PC memory hardware |
| fdisk, lbacache, mirror, unformat, recover, defrag | | | X | | hard-disk / PC disk BIOS tools |
| fdapm | | | X | | PC APM |
| shsucdx, udvd2 | | | X | | CD-ROM |
| fdnet, fdnpkg | | | X | | network / network package manager |
| fdimples, pkgtools, slicer, v8power, fdhelper | | | X | | PC installer and its UI tools |

Binary sizes from the repository zips (all bundled variants counted) are in
the generated `survey.md`; the largest class-A items are `zip` and `unzip`.

## Proposed set (2-3 disks, English)

1. **System disk:** the current M20 disk (kernel, FreeCOM 0.86, EDLIN,
   MORE, FORMAT, SYS, CHKDSK, MEMMAP, JWasm, samples).
2. **Utilities disk:** class A/B tools that build with the pinned toolchain
   first: `find`, `sort`, `xcopy`, `choice`, `label`, `move`, `append`,
   `devload`, `nlsfunc`, `fc`, `comp`, `deltree`, `callver`; then the Turbo-C
   ports `attrib`, `tree`, `replace`, `exe2bin`, `swsubst`, `undelete`,
   `share` after a build port to Open Watcom.
3. **Archivers/tools disk:** `unzip`, `zip`, `gzip`, `debug`. UNZIP, ZIP
   and GZIP are on `freedos-PC88VA-M20-ARC.D88` (16-bit builds of the
   unmodified package sources; 640 KiB required) and DEBUG (DOS-debug
   fork with a PC88VA console option).

Not proposed for the first set: class C (`edit`, `htmlhelp`) and all class X.

## Progress

- On the utilities disk with VAEG VA2/VA 640 KiB checks: `find`, `sort`,
  `xcopy`, `label`, `move` (8 KiB stack), `append`, `nlsfunc`, `devload`,
  and from project forks `choice` (DOS-clock `/T`) and `deltree` (DOS
  confirmation key).
- From project forks with toolchain fixes: `comp` (NASM 2.x syntax;
  reproduces the FreeDOS 1.4 binary) and `fc` (Open Watcom LFN-failure
  detection on DOS without LFN support) and `attrib` (Open Watcom branches
  in a Borland/Turbo C program).
- `tree` from a project fork (Open Watcom DOS layer, C++ via the pinned
  `wpp`; PC88VA ASCII/80x25 defaults).
- `share`: deferred by owner decision.
- `replace`, `exe2bin`: project repositories importing the FreeDOS 1.4
  package sources, with Open Watcom branches; on the utilities disk.
- `undelete` (512-byte sectors only) and `swsubst` (SUPPL/msglib and CDS
  rewriting): repositories created and imported; port deferred by owner
  decision.

## Open points

- Exact Floppy Edition package versions versus current repository versions;
  pin each source by upstream Git commit where an FDOS repository exists,
  otherwise by archive URL and SHA-256.
- A build port to Open Watcom for Turbo-C-only packages, or a decision to
  pin an additional public toolchain.
- 8086 compatibility of each build (the VA CPU is a V30).
- Class B adaptations reuse the FreeCOM approach: `PC88VA`-only branches,
  non-VA build kept identical to upstream.
- Japanese support (DBCS kernel/FreeCOM, NLS 081/932, display and input) is a
  later stage.
