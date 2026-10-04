PC-88VA FreeDOS M20 - utilities disk (drive B:)

This is a data disk for drive B:. It is not bootable: boot from the M20
system disk in drive A:, insert this disk in drive B: and run the programs
from B: (for example B:FIND /?), or copy them to a working disk.

Programs
--------
FIND.EXE     Search for text in files.
SORT.EXE     Sort lines of text.
XCOPY.EXE    Copy files and directory trees.
LABEL.EXE    Create, change or delete a volume label.
MOVE.EXE     Move or rename files and directories.
FC.EXE       Compare files.
APPEND.EXE   Data file search path (TSR).
NLSFUNC.EXE  Load country-specific information (TSR).
DEVLOAD.COM  Load device drivers from the command line.

Every program is built from its pinned public FreeDOS source (as of the
FreeDOS 1.4 release) with Open Watcom 1.9 or NASM for 8086 real mode;
messages are English. The corresponding source of every program is in the
separate host-side M20 source bundle.

Licenses
--------
COPYING      GNU General Public License version 2 (all programs, tnyprntf).
KITTEN.LIC   GNU Lesser General Public License version 2.1 (kitten library
             linked into FIND, SORT, LABEL, MOVE and FC).
