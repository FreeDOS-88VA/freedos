/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M20_VOLUME_H
#define M20_VOLUME_H
#include "fat12.h"

struct m20_volume {
  unsigned char boot[M20_SECTOR_BYTES];
  unsigned char fat[M20_FAT_BYTES];
  unsigned char root[M20_ROOT_BYTES];
  unsigned char owned[(M20_CLUSTER_LIMIT + 7U) / 8U];
  struct m20_layout layout;
};

struct m20_check_report {
  unsigned files;
  unsigned directories;
  unsigned free_clusters;
  unsigned allocated_clusters;
  unsigned bad_clusters;
  unsigned lost_clusters;
  unsigned root_entries_used;
  unsigned long file_bytes;
};

extern unsigned __far __cdecl m20_abs_sector(unsigned writing, unsigned drive,
                                       unsigned sector, void __far *buffer);
extern void __interrupt __far m20_critical(void);
/* VA floppy BIOS INT 80h with AX, CX, DX and ES:BP=buffer; BX=0.
   Returns 0 on success, otherwise the nonzero BIOS status (FFh if none). */
extern unsigned __far __cdecl m20_fdd_bios(unsigned ax, unsigned cx, unsigned dx,
                                           void __far *buffer);

void m20_reset_disk(void);
int m20_bind_volume(unsigned drive);
int m20_read_sector(unsigned drive, unsigned sector, void *buffer);
int m20_write_sector(unsigned drive, unsigned sector, void *buffer);
int m20_load_volume(unsigned drive, struct m20_volume *volume);
int m20_check_allocations(unsigned drive, struct m20_volume *volume,
                          struct m20_check_report *report);

#endif
