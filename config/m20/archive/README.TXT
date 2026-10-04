PC-88VA FreeDOS M20 - archiver disk (drive B:)

This is a data disk for drive B:. It is not bootable: boot from the M20
system disk in drive A:, insert this disk in drive B: and run the programs
from B: (for example B:UNZIP -l FILE.ZIP), or copy them to a working disk.

Programs
--------
UNZIP.EXE    Extract, list and test ZIP archives (Info-ZIP UnZip 6.00).
ZIP.EXE      Create and update ZIP archives (Info-ZIP Zip 3.0).
GZIP.EXE     Compress and decompress gzip files (gzip 1.2.4).

Notes
-----
These programs need a PC-88VA with 640 KiB of conventional RAM. With 512
KiB they stop with "cannot allocate unzip buffers" or "insufficient
memory".

Without the TZ environment variable, UNZIP warns "TZ environment variable
not found, cannot use UTC times!!" and returns exit code 1 although the
files are extracted. Set a time zone first to avoid this, for example:

    SET TZ=JST-9

GZIP keeps DOS 8.3 names: G.TXT is compressed to G.TXZ and decompressed
to G.TX. Use GZIP -d -N to restore the original name stored in the file.

Every program is built from the FreeDOS 1.4 package source, unmodified,
with Open Watcom 1.9 for 8086 real mode; messages are English. FreeDOS 1.4
shipped 32-bit builds of UNZIP and ZIP, which do not run on the PC-88VA.
The package sources are kept in project repositories, and the
corresponding source of every program is in the separate host-side M20
source bundle.

Licenses
--------
COPYING      GNU General Public License version 2 (GZIP).
UNZIP.LIC    Info-ZIP license, version 2009-Jan-02 (UNZIP).
ZIP.LIC      Info-ZIP license, version 2007-Mar-4 (ZIP).
