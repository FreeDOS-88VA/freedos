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
CHOICE.EXE   Wait for a key choice in batch files.
DELTREE.COM  Delete a directory tree.
COMP.COM     Compare two files byte by byte.
ATTRIB.COM   Display or change file attributes.
TREE.EXE     Display the directory structure (ASCII lines).

Every program is built from its pinned public FreeDOS source (as of the
FreeDOS 1.4 release) with Open Watcom 1.9 or NASM for 8086 real mode;
messages are English. CHOICE, DELTREE and TREE use small PC-88VA-only
changes that replace PC BIOS services with DOS ones; FC, COMP, ATTRIB and
TREE carry small fixes for the Open Watcom and NASM toolchains. The
corresponding source of every program is in the separate host-side M20
source bundle.

Licenses
--------
COPYING      GNU General Public License version 2 (GPL programs and
             tnyprntf).
KITTEN.LIC   GNU Lesser General Public License version 2.1 (kitten library
             linked into FIND, SORT, LABEL, MOVE, FC and CHOICE).
COMP.LIC     Copyright and MIT permission notice of COMP.
TREE (pdTree) is public domain; it is built without the optional LGPL Cats
files.
