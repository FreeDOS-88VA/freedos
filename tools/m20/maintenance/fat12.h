/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M20_FAT12_H
#define M20_FAT12_H

#define M20_SECTOR_BYTES 1024U
/* Two native 2HD profiles share 8 sectors x 2 heads x 1024 bytes and the
   same FAT12 metadata layout: 80 cylinders (FreeDOS distribution) and the
   NEC-compatible 77 cylinders. The larger values size static buffers. */
#define M20_TOTAL_SECTORS 1280U
#define M20_TOTAL_SECTORS_77 1232U
#define M20_SECTORS_PER_TRACK 8U
#define M20_HEADS 2U
#define M20_FAT_BYTES 2048U
#define M20_ROOT_ENTRIES 192U
#define M20_ROOT_BYTES 6144U
#define M20_FIRST_DATA_SECTOR 11U
#define M20_DATA_CLUSTERS 1269U
#define M20_CLUSTER_LIMIT (M20_DATA_CLUSTERS + 2U)

struct m20_layout {
  unsigned bytes_per_sector;
  unsigned sectors_per_cluster;
  unsigned reserved_sectors;
  unsigned fat_count;
  unsigned root_entries;
  unsigned total_sectors;
  unsigned media_descriptor;
  unsigned sectors_per_fat;
  unsigned sectors_per_track;
  unsigned heads;
  unsigned fat_start;
  unsigned root_start;
  unsigned root_sectors;
  unsigned first_data_sector;
  unsigned data_clusters;
  unsigned cylinders;
};

enum m20_chain_error {
  M20_CHAIN_OK = 0,
  M20_CHAIN_BAD_ARGUMENT,
  M20_CHAIN_TRUNCATED_FAT,
  M20_CHAIN_BAD_START,
  M20_CHAIN_CROSS_LINK,
  M20_CHAIN_FREE_LINK,
  M20_CHAIN_RESERVED_LINK,
  M20_CHAIN_BAD_CLUSTER_LINK,
  M20_CHAIN_OUT_OF_RANGE,
  M20_CHAIN_CYCLE,
  M20_CHAIN_EARLY_END,
  M20_CHAIN_EXTRA_LINK
};

/* Return the cylinder count for a supported total, otherwise 0. */
unsigned m20_profile_cylinders(unsigned total_sectors);
/* Accept an extended BPB (signature 29h plus 55AA marks) or a DOS 2.x short
   BPB without marks, for either native profile. */
int m20_validate_bpb(const unsigned char *boot, unsigned bytes,
                     struct m20_layout *layout);
int m20_fat12_get(const unsigned char *fat, unsigned fat_bytes,
                  unsigned cluster, unsigned *value);
enum m20_chain_error m20_validate_chain(
    const unsigned char *fat, unsigned fat_bytes, unsigned data_clusters,
    unsigned first_cluster, unsigned expected_clusters,
    unsigned char *owned, unsigned owned_bytes, unsigned *actual_clusters);

#endif
