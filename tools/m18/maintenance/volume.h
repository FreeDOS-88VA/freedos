/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M18_VOLUME_H
#define M18_VOLUME_H
#include "fat12.h"

struct m18_volume {
  unsigned char boot[M18_SECTOR_BYTES];
  unsigned char fat[M18_FAT_BYTES];
  unsigned char root[M18_ROOT_BYTES];
  unsigned char owned[(M18_CLUSTER_LIMIT + 7U) / 8U];
  struct m18_layout layout;
};

struct m18_check_report {
  unsigned files;
  unsigned directories;
  unsigned free_clusters;
  unsigned allocated_clusters;
  unsigned bad_clusters;
  unsigned lost_clusters;
  unsigned root_entries_used;
  unsigned long file_bytes;
};

extern unsigned __far __cdecl m18_abs_sector(unsigned writing, unsigned drive,
                                       unsigned sector, void __far *buffer);
extern void __interrupt __far m18_critical(void);

void m18_reset_disk(void);
int m18_bind_volume(unsigned drive);
int m18_read_sector(unsigned drive, unsigned sector, void *buffer);
int m18_write_sector(unsigned drive, unsigned sector, void *buffer);
int m18_load_volume(unsigned drive, struct m18_volume *volume);
int m18_check_allocations(unsigned drive, struct m18_volume *volume,
                          struct m18_check_report *report);

#endif
