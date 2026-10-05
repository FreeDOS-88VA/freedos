PC-88VA FreeDOS M20 - English/ASCII basic system

This disk is one native PC-88VA 2HD boot disk. It contains the FreeDOS kernel,
the FreeCOM 0.86 shell built for PC-88VA, and a compact set of public DOS
tools. It is not a complete FreeDOS distribution and does not include
Japanese/NLS support, a protected-mode toolchain, XMS/EMS, or a hard-disk
boot path.

Boot
----
Insert this disk in drive A: and boot through the PC-88VA native floppy path.
Compatibility with any emulator or machine must be established by the matching
qualification record; it is not implied by this disk. Leave B: empty for normal
startup. At the DOS prompt, use DIR, TYPE, COPY, REN, DEL, MD, RD, CD,
ECHO, SET, PATH, batch files, and shell redirection. Use HELP for shell help.
At startup a menu offers two command shells; press its digit, or Enter (or
wait 5 seconds) for 1:
  1  FreeCOM 0.86, loaded through KSSF. It swaps itself out while an external
     program runs, so the program gets the shell's memory too. Commands in
     batch files, with redirection or in pipes run without swapping.
  2  MS-DOS 4.0 COMMAND.COM in A:\MSDOS (Microsoft MIT source, MSDOS.LIC).
     Its resident part is small; it has no HELP, history or aliases.
0 runs neither numbered SHELL line (FreeCOM without KSSF). F5 skips CONFIG.SYS
and AUTOEXEC.BAT; F8 asks for each line. AUTOEXEC.BAT sets PATH for both.

Files and examples
------------------
EDLIN is a line editor. MORE pages text with Space, Enter, or Q. MEMMAP lists
the validated DOS MCB chain; it does not report physical or reserved memory.
JWASMR is a real-mode 8086-class assembler. HELLO.ASM includes its COM build
command; HELLO.DOC explains and builds it step by step. MZDEMO.ASM and BUILD.BAT
show direct COM and MZ output without a linker.
DEBUG is the DOS-debug 2.50 debugger (DEBUG prog.com, commands R, D, U, A, G,
T, P, E, N, L, W, Q; type ? for help). It reads the keyboard through the
console driver and writes through INT 29h, so it works on this machine; it
shows no special tracing of the kernel and has no protected-mode support.

Create a writable work directory before editing or assembling. Keep the
original release image unchanged; make a writable copy for ordinary file work.
See HELLO.DOC for the individual COM build and QUICKSTR.TXT for the complete
edit/assemble/run example.

RAM limits of the tested small workflow
---------------------------------------
At installed 512 KiB, the shell, EDLIN editing, MORE, MEMMAP and native 2HD
maintenance worked on the tested VA/VA2 models. JWASMR could not start a COM
or MZ sample build: DOS reported insufficient memory. Use at least 640 KiB
installed for the bundled edit/assemble/run example; this is a tested sample
setting, not a guarantee for larger source files. A saved 640 KiB selection
cannot replace missing physical RAM. Do not count an old executable as output
from a failed build.

Floppy maintenance
------------------
CHKDSK checks a native 2HD FAT12 disk (80 or 77 cylinders) without repairing
it. FORMAT B: formats every track of a blank or used 2HD disk in B:, verifies
every sector, and writes an empty FAT12 volume: 80 cylinders by default, or
FORMAT B: /T:77 for the NEC-compatible 77-cylinder form. FORMAT B: /Q only
rewrites the FAT12 metadata of a disk that already has a valid native BPB.
FORMAT is destructive. SYS A: B: transfers the boot system to a formatted
native 2HD disk in B: and keeps B:'s own geometry and volume label; B: needs
the same free clusters for LOADER.BIN as on A: (a freshly formatted disk has
them). Use FORMAT and SYS only on target media in B:; never use the release
master as a target. Read each command's confirmation and help first.

License and corresponding source
--------------------------------
COPYING contains the GNU GPL version 2 terms used by the FreeDOS and M20 GPL
programs. DEBUG.LIC contains the MIT license of DEBUG, MSDOS\MSDOS.LIC that of
MS-DOS 4.0 COMMAND.COM. JWASM.LIC contains the
Sybase Open Watcom Public License 1.0. The
project and component corresponding source, build recipes, patches, notices,
and license files accompany this disk in a separate host-side source bundle.
The unmodified Open Watcom 1.9 DOS compiler runtime, linked into programs,
shares JWASM.LIC terms. Its official upstream source archive is publicly
available from open-watcom/open-watcom-1.9 GitHub release ow1.9 under the
name open_watcom_1.9.0-src.tar.bz2, SHA-256
6d303327988ee2dda60cfabebf3f45a9758aee4da117d41cf3153fccb7e5e4bf.
The official compiler binary is separately identity-locked by this project's
host toolchain recipe. See the host README and package manifest for URLs and
exact component revisions.
