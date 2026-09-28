/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <assert.h>
#include <stdio.h>
#include <dos.h>
#include <string.h>
#include "../../tools/m18/maintenance/volume.h"

static unsigned char disk[2][M18_TOTAL_SECTORS][M18_SECTOR_BYTES];
static unsigned writes;

int intdos(union REGS *input, union REGS *output)
{
  (void)input;
  (void)output;
  return 0;
}

unsigned m18_abs_sector(unsigned writing, unsigned drive, unsigned sector,
                        void *buffer)
{
  if (drive > 1 || sector >= M18_TOTAL_SECTORS || !buffer)
    return 1;
  if (writing) {
    memcpy(disk[drive][sector], buffer, M18_SECTOR_BYTES);
    ++writes;
  } else {
    memcpy(buffer, disk[drive][sector], M18_SECTOR_BYTES);
  }
  return 0;
}

void m18_critical(void) { }

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

static void set_fat(unsigned char *fat, unsigned cluster, unsigned value)
{
  unsigned offset = cluster + cluster / 2U;
  unsigned packed = fat[offset] | ((unsigned)fat[offset + 1] << 8);
  if (cluster & 1U)
    packed = (packed & 0x000fU) | (value << 4);
  else
    packed = (packed & 0xf000U) | value;
  fat[offset] = (unsigned char)packed;
  fat[offset + 1] = (unsigned char)(packed >> 8);
}

static void make_volume(void)
{
  unsigned char boot[M18_SECTOR_BYTES];
  unsigned char fat[M18_FAT_BYTES];
  unsigned char root[M18_ROOT_BYTES];
  unsigned char *dir;
  memset(disk, 0, sizeof(disk));
  memset(boot, 0, sizeof(boot));
  boot[0] = 0xeb;
  boot[1] = 0xfe;
  memcpy(boot + 3, "FDPC88VA", 8);
  put16(boot + 11, M18_SECTOR_BYTES);
  boot[13] = 1;
  put16(boot + 14, 1);
  boot[16] = 2;
  put16(boot + 17, M18_ROOT_ENTRIES);
  put16(boot + 19, M18_TOTAL_SECTORS);
  boot[21] = 0xfe;
  put16(boot + 22, 2);
  put16(boot + 24, 8);
  put16(boot + 26, 2);
  boot[38] = 0x29;
  put32(boot + 39, 0x4d180000UL);
  memcpy(boot + 43, "PC88VA-M18 ", 11);
  memcpy(boot + 54, "FAT12   ", 8);
  boot[510] = boot[1022] = 0x55;
  boot[511] = boot[1023] = 0xaa;
  memcpy(disk[0][0], boot, sizeof(boot));

  memset(fat, 0, sizeof(fat));
  fat[0] = 0xfe;
  fat[1] = fat[2] = 0xff;
  set_fat(fat, 2, 3);
  set_fat(fat, 3, 0xfff);
  set_fat(fat, 4, 0xfff);
  set_fat(fat, 5, 0xfff);
  memcpy(disk[0][1], fat, M18_FAT_BYTES);
  memcpy(disk[0][3], fat, M18_FAT_BYTES);

  memset(root, 0, sizeof(root));
  memcpy(root, "PC88VA-M18 ", 11);
  root[11] = 0x08;
  memcpy(root + 32, "HELLO   TXT", 11);
  root[32 + 11] = 0x20;
  put16(root + 32 + 26, 2);
  put32(root + 32 + 28, 1025);
  memcpy(root + 64, "SUBDIR     ", 11);
  root[64 + 11] = 0x10;
  put16(root + 64 + 26, 4);
  memcpy(disk[0][5], root, sizeof(root));

  dir = disk[0][M18_FIRST_DATA_SECTOR + 4 - 2];
  memcpy(dir, ".          ", 11);
  dir[11] = 0x10;
  put16(dir + 26, 4);
  memcpy(dir + 32, "..         ", 11);
  dir[32 + 11] = 0x10;
  memcpy(dir + 64, "INNER   TXT", 11);
  dir[64 + 11] = 0x20;
  put16(dir + 64 + 26, 5);
  put32(dir + 64 + 28, 1);
}

int main(void)
{
  struct m18_volume volume;
  struct m18_check_report report;
  unsigned writes_before;

  make_volume();
  writes_before = writes;
  assert(m18_load_volume(0, &volume));
  assert(m18_check_allocations(0, &volume, &report));
  assert(report.files == 2 && report.directories == 1);
  assert(report.root_entries_used == 3 && report.file_bytes == 1026UL);
  assert(report.allocated_clusters == 4 && report.free_clusters == 1265);
  assert(report.bad_clusters == 0 && report.lost_clusters == 0);
  assert(writes == writes_before);

  make_volume();
  disk[0][3][0] ^= 1;
  assert(!m18_load_volume(0, &volume));

  make_volume();
  set_fat(disk[0][1], 3, 2);
  set_fat(disk[0][3], 3, 2);
  assert(m18_load_volume(0, &volume));
  assert(!m18_check_allocations(0, &volume, &report));

  make_volume();
  set_fat(disk[0][1], 6, 0xfff);
  set_fat(disk[0][3], 6, 0xfff);
  assert(m18_load_volume(0, &volume));
  assert(!m18_check_allocations(0, &volume, &report));

  make_volume();
  put16(disk[0][M18_FIRST_DATA_SECTOR + 4 - 2] + 32 + 26, 1);
  assert(m18_load_volume(0, &volume));
  assert(!m18_check_allocations(0, &volume, &report));

  assert(!m18_load_volume(2, &volume));
  puts("M18 native-volume synthetic read-only tests: PASS");
  return 0;
}
