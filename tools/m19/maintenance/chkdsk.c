/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "volume.h"

static struct m19_volume volume;
static struct m19_check_report report;

static int usage(void)
{
  puts("CHKDSK - read-only native PC-88VA 2HD FAT12 check");
  puts("Usage: CHKDSK [A:|B:]");
  puts("Only 80x2x8 or 77x2x8, 1024-byte-sector 2HD FAT12 media are checked.");
  puts("No repair option is provided; other floppy profiles are unsupported.");
  return 0;
}

static int parse_drive(int argc, char **argv, unsigned *drive)
{
  int i;
  *drive = 0;
  for (i = 1; i < argc; ++i) {
    if (!strcmp(argv[i], "/?") || !strcmp(argv[i], "-?"))
      return usage();
    /* Accepted for compatibility; every run is already a read-only check. */
    if (!strcmp(argv[i], "/CHECK") || !strcmp(argv[i], "/check"))
      continue;
    if ((argv[i][0] == 'A' || argv[i][0] == 'a') &&
        argv[i][1] == ':' && argv[i][2] == 0) {
      *drive = 0;
      continue;
    }
    if ((argv[i][0] == 'B' || argv[i][0] == 'b') &&
        argv[i][1] == ':' && argv[i][2] == 0) {
      *drive = 1;
      continue;
    }
    fprintf(stderr, "CHKDSK: unsupported argument: %s\n", argv[i]);
    return -1;
  }
  return 1;
}

int main(int argc, char **argv)
{
  unsigned drive;
  int parsed, good;
  void (__interrupt __far *old24)(void);

  parsed = parse_drive(argc, argv, &drive);
  if (parsed <= 0)
    return parsed < 0 ? 2 : 0;

  old24 = _dos_getvect(0x24);
  _dos_setvect(0x24, m19_critical);
  good = m19_load_volume(drive, &volume);
  if (good)
    good = m19_check_allocations(drive, &volume, &report);

  if (good) {
    printf("Drive %c: native 2HD FAT12; %u cylinders; %u-byte sectors; %u data clusters.\n",
           drive ? 'B' : 'A', volume.layout.cylinders,
           volume.layout.bytes_per_sector, volume.layout.data_clusters);
    printf("Files: %u; directories: %u; root entries: %u; file bytes: %lu.\n",
           report.files, report.directories, report.root_entries_used,
           report.file_bytes);
    printf("Allocated clusters: %u; free clusters: %u (%lu bytes); bad clusters: %u.\n",
           report.allocated_clusters, report.free_clusters,
           (unsigned long)report.free_clusters * M19_SECTOR_BYTES,
           report.bad_clusters);
    puts("Result: valid. Read-only check; no filesystem repair was attempted.");
  } else {
    fprintf(stderr,
            "CHKDSK: invalid, inconsistent, unreadable, or unsupported 2HD volume on %c:.\n",
            drive ? 'B' : 'A');
    puts("Result: check failed; no write was attempted.");
  }
  _dos_setvect(0x24, old24);
  return good ? 0 : 1;
}
