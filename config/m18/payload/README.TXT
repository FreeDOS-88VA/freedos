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
startup. At the DOS prompt, use DIR, TYPE, COPY, REN, DEL, MD, RD, CD, ECHO, SET, PATH, batch files,
and shell redirection. Use HELP for shell help.

Files and examples
------------------
EDLIN is a line editor. MORE pages text with Space, Enter, or Q. MEMMAP lists
the validated DOS MCB chain; it does not report physical or reserved memory.
JWASMR is a real-mode 8086-class assembler. HELLO.ASM, MZDEMO.ASM, and BUILD.BAT
show direct COM and MZ output without a linker.

Create a writable work directory before editing or assembling. Keep the
original release image unchanged; make a writable copy for ordinary file work.
See QUICKSTR.TXT for the complete edit/assemble/run example.

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
maintenance commands.

License and corresponding source
--------------------------------
COPYING contains the GNU GPL version 2 terms used by the FreeDOS and M18 GPL
programs. JWASM.LIC contains the Sybase Open Watcom Public License 1.0. The
complete corresponding source, build recipes, patches, component notices, and
license files accompany the public M18 disk as a separate host-side source
bundle. See its README and package manifest for exact source revisions.
