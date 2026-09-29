/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "volume.h"

#define VOLUME_SERIAL 0x4d180000UL

static struct m18_volume volume;
static struct m18_check_report report;
static unsigned char sector[M18_SECTOR_BYTES];
static unsigned char verify[M18_SECTOR_BYTES];
static unsigned char fat[M18_FAT_BYTES];
static unsigned char root[M18_ROOT_BYTES];

static void put16(unsigned char *p, unsigned value)
{
  p[0] = (unsigned char)value;
  p[1] = (unsigned char)(value >> 8);
}

static void put32(unsigned char *p, unsigned long value)
{
  put16(p, (unsigned)value);
  put16(p + 2, (unsigned)(value >> 16));
}

static void make_boot(void)
{
  memset(sector, 0, sizeof(sector));
  sector[0] = 0xeb;
  sector[1] = 0xfe;
  sector[2] = 0x90;
  memcpy(sector + 3, "FDPC88VA", 8);
  put16(sector + 11, M18_SECTOR_BYTES);
  sector[13] = 1;
  put16(sector + 14, 1);
  sector[16] = 2;
  put16(sector + 17, M18_ROOT_ENTRIES);
  put16(sector + 19, M18_TOTAL_SECTORS);
  sector[21] = 0xfe;
  put16(sector + 22, 2);
  put16(sector + 24, 8);
  put16(sector + 26, 2);
  sector[38] = 0x29;
  put32(sector + 39, VOLUME_SERIAL);
  memcpy(sector + 43, "PC88VA-M18 ", 11);
  memcpy(sector + 54, "FAT12   ", 8);
  sector[510] = 0x55;
  sector[511] = 0xaa;
  sector[1022] = 0x55;
  sector[1023] = 0xaa;
}

static int write_verified(unsigned drive, unsigned lba,
                          unsigned char *data)
{
  return m18_write_sector(drive, lba, data) &&
         m18_read_sector(drive, lba, verify) &&
         memcmp(data, verify, M18_SECTOR_BYTES) == 0;
}

static int confirm_format(void)
{
  char line[32];
  puts("This initializes FAT12 metadata on already sector-formatted B: only.");
  puts("It does NOT low-level format tracks and does NOT erase old data sectors.");
  puts("All existing B: directory entries and files will be lost.");
  fputs("Type YES to initialize B: (anything else cancels): ", stdout);
  fflush(stdout);
  if (!fgets(line, sizeof(line), stdin))
    return 0;
  line[strcspn(line, "\r\n")] = 0;
  return strcmp(line, "YES") == 0;
}

int main(int argc, char **argv)
{
  unsigned i;
  void (__interrupt __far *old24)(void);
  int good = 1;

  if (argc == 2 && (!strcmp(argv[1], "/?") || !strcmp(argv[1], "-?"))) {
    puts("FORMAT - initialize native PC-88VA 2HD FAT12 metadata");
    puts("Usage: FORMAT B:");
    puts("B: must have a readable native 2HD BPB from prior preparation.");
    puts("This program performs no track/low-level format and is destructive.");
    return 0;
  }
  if (argc != 2 || (strcmp(argv[1], "B:") && strcmp(argv[1], "b:"))) {
    fputs("FORMAT: use FORMAT B: only; A: and other profiles are refused.\n", stderr);
    return 2;
  }

  old24 = _dos_getvect(0x24);
  _dos_setvect(0x24, m18_critical);
  if (!m18_bind_volume(1) || !m18_read_sector(1, 0, verify) ||
      !m18_validate_bpb(verify, sizeof(verify), &volume.layout)) {
    fputs("FORMAT: B: lacks a valid native 2HD BPB; no write was attempted.\n", stderr);
    _dos_setvect(0x24, old24);
    return 1;
  }
  if (!confirm_format()) {
    puts("FORMAT: cancelled; B: was not changed.");
    _dos_setvect(0x24, old24);
    return 1;
  }

  memset(fat, 0, sizeof(fat));
  fat[0] = 0xfe;
  fat[1] = 0xff;
  fat[2] = 0xff;
  memset(root, 0, sizeof(root));
  memcpy(root, "PC88VA-M18 ", 11);
  root[11] = 0x08;
  make_boot();

  m18_reset_disk();
  for (i = 0; i < 4 && good; ++i)
    good = write_verified(1, 1U + i,
                          fat + (i % 2U) * M18_SECTOR_BYTES);
  for (i = 0; i < 6 && good; ++i)
    good = write_verified(1, 5U + i, root + i * M18_SECTOR_BYTES);
  if (good)
    good = write_verified(1, 0, sector);
  m18_reset_disk();
  if (good)
    good = m18_load_volume(1, &volume) &&
           m18_check_allocations(1, &volume, &report) &&
           report.free_clusters == M18_DATA_CLUSTERS;

  if (good) {
    puts("FORMAT: native 2HD FAT12 filesystem initialized and read back.");
    puts("B: is a data disk; use SYS A: B: to transfer the boot system.");
    puts("No low-level track format or file-data wipe was performed.");
  } else {
    fputs("FORMAT: write/readback or filesystem validation failed; B: may be incomplete.\n",
          stderr);
  }
  _dos_setvect(0x24, old24);
  return good ? 0 : 1;
}
