PC-88VA FreeDOS M18 - English/ASCII basic system

This disk is one native PC-88VA 2HD boot disk. It contains the FreeDOS kernel,
the NECPC88VA FreeCOM shell, and a compact set of public DOS tools. It is not a
complete FreeDOS distribution and does not include Japanese/NLS support, a
protected-mode toolchain, XMS/EMS, or a hard-disk boot path.

Boot
----
Insert this disk in drive A: and boot through the PC-88VA native floppy path.
Compatibility with any emulator or machine must be established by the matching
qualification record; it is not implied by this disk. Leave B: empty for normal
startup. At the DOS prompt, use DIR, TYPE, COPY, REN, DEL, MD, RD, CD,
ECHO, SET, PATH, batch files, and shell redirection. Use HELP for shell help.

Files and examples
------------------
EDLIN is a line editor. MORE pages text with Space, Enter, or Q. MEMMAP lists
the validated DOS MCB chain; it does not report physical or reserved memory.
JWASMR is a real-mode 8086-class assembler. HELLO.ASM, MZDEMO.ASM, and BUILD.BAT
show direct COM and MZ output without a linker.

Create a writable work directory before editing or assembling. Keep the
original release image unchanged; make a writable copy for ordinary file work.
See QUICKSTR.TXT for the complete edit/assemble/run example.

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
CHKDSK checks the documented native 2HD FAT12 filesystem without repairing it.
FORMAT B: initializes filesystem metadata only when B: has a readable, valid
native 2HD BPB from prior preparation; it does not low-level format tracks.
FORMAT is destructive. SYS A: B:
transfers the boot system to a prepared native 2HD target and writes its boot
record. Both FORMAT and SYS are intended for disposable target media in B:;
never use the release master as a target. Read each command's confirmation and
help before proceeding. Only the native 2HD FAT12 profile is supported by these
maintenance commands. CHKDSK B: on a prepared 2HD disk was checked. Redirected
CHKDSK A: output to a file on A: may be empty (open issue); do not treat an
empty file as a completed check.

License and corresponding source
--------------------------------
COPYING contains the GNU GPL version 2 terms used by the FreeDOS and M18 GPL
programs. JWASM.LIC contains the Sybase Open Watcom Public License 1.0. The
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
