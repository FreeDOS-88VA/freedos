/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M19_VOLUME_H
#define M19_VOLUME_H
#include "fat12.h"

struct m19_volume {
  unsigned char boot[M19_SECTOR_BYTES];
  unsigned char fat[M19_FAT_BYTES];
  unsigned char root[M19_ROOT_BYTES];
  unsigned char owned[(M19_CLUSTER_LIMIT + 7U) / 8U];
  struct m19_layout layout;
};

struct m19_check_report {
  unsigned files;
  unsigned directories;
  unsigned free_clusters;
  unsigned allocated_clusters;
  unsigned bad_clusters;
  unsigned lost_clusters;
  unsigned root_entries_used;
  unsigned long file_bytes;
};

extern unsigned __far __cdecl m19_abs_sector(unsigned writing, unsigned drive,
                                       unsigned sector, void __far *buffer);
extern void __interrupt __far m19_critical(void);
/* VA floppy BIOS INT 80h with AX, CX, DX and ES:BP=buffer; BX=0.
   Returns 0 on success, otherwise the nonzero BIOS status (FFh if none). */
extern unsigned __far __cdecl m19_fdd_bios(unsigned ax, unsigned cx, unsigned dx,
                                           void __far *buffer);

void m19_reset_disk(void);
int m19_bind_volume(unsigned drive);
int m19_read_sector(unsigned drive, unsigned sector, void *buffer);
int m19_write_sector(unsigned drive, unsigned sector, void *buffer);
int m19_load_volume(unsigned drive, struct m19_volume *volume);
int m19_check_allocations(unsigned drive, struct m19_volume *volume,
                          struct m19_check_report *report);

#endif
