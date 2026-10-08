MS-DOS 4.0 for the NEC PC-88VA (English)

This disk holds MS-DOS 4.0 built from the MIT-licensed Microsoft source
release (https://github.com/microsoft/MS-DOS) with a PC-88VA BIOS part.
It is an unofficial build by the FreeDOS-88VA project and is not
supported by Microsoft or NEC.  See LICENSE.TXT.

Source and build recipe:
  https://github.com/FreeDOS-88VA/MS-DOS        (branch release/msdos-va)
  https://github.com/FreeDOS-88VA/freedos       (experiments/msdos4-va)

PC-88VA specifics
- Console: the ROM text BIOS.  Carriage return, line feed, backspace and
  printable ASCII are shown; other control codes and ANSI escape
  sequences are not.  The keyboard delivers ASCII keys only; function
  and cursor keys are ignored.  There is no Japanese input or display.
- Drives A: and B: are the 2HD floppy drives: 1024-byte sectors,
  8 sectors per track, 2 heads, 80 cylinders (1,280 sectors).
- CLOCK$ uses the built-in calendar clock.
- AUX and PRN discard output.
- Conventional memory is measured at startup.
- FORMAT and SYS are PC-88VA programs:
    FORMAT d: [/S] [/V:label]     SYS d:

Not included (IBM PC hardware specific or not applicable): ANSI.SYS,
DISPLAY.SYS, DRIVER.SYS, KEYBOARD.SYS, PRINTER.SYS, RAMDRIVE.SYS,
SMARTDRV.SYS, VDISK.SYS, XMA2EMS.SYS, XMAEM.SYS, DISKCOMP, DISKCOPY,
FDISK, GRAFTABL, GRAPHICS, KEYB, MODE, PRINT, DOSSHELL, SELECT,
FILESYS and IFSFUNC.

Status: tested on the VAEG emulator only (PC-88VA and PC-88VA2).
It has not been tested on real hardware.
