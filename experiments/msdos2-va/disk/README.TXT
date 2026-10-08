MS-DOS 2.0 for the NEC PC-88VA (English)

This disk holds MS-DOS 2.0 from the MIT-licensed Microsoft release
(https://github.com/microsoft/MS-DOS) with a PC-88VA BIOS part.  It is an
unofficial build by the FreeDOS-88VA project and is not supported by
Microsoft or NEC.  See LICENSE.TXT.

Source and build recipe:
  https://github.com/FreeDOS-88VA/MS-DOS        (branch release/msdos-va)
  https://github.com/FreeDOS-88VA/freedos       (experiments/msdos2-va)

MSDOS.SYS, COMMAND.COM, CHKDSK, DEBUG, DISKCOPY, EDLIN, EXE2BIN, FC,
FIND, MORE, RECOVER and SORT are the Microsoft-supplied binaries of the
2.0 release; the published 2.0 sources cannot rebuild them.  IO.SYS is
the PC-88VA BIOS part linked with the Microsoft-supplied SYSINIT.

PC-88VA specifics
- Console: the ROM text BIOS.  Carriage return, line feed, backspace and
  printable ASCII are shown; other control codes are not.  The keyboard
  delivers ASCII keys only; function and cursor keys are ignored.
  There is no Japanese input or display.
- Drives A: and B: are the 2HD floppy drives: 1024-byte sectors,
  8 sectors per track, 2 heads, 80 cylinders (1,280 sectors).
- CLOCK uses the built-in calendar clock.
- AUX and PRN discard output (PRINT is not included).
- Conventional memory is measured at startup.
- FORMAT, SYS and MEMINFO are PC-88VA programs:
    FORMAT d: [/S] [/V:label]     SYS d:     MEMINFO

Status: tested on the VAEG emulator only (PC-88VA and PC-88VA2).
It has not been tested on real hardware.
