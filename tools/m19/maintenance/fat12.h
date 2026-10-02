/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M19_FAT12_H
#define M19_FAT12_H

#define M19_SECTOR_BYTES 1024U
/* Two native 2HD profiles share 8 sectors x 2 heads x 1024 bytes and the
   same FAT12 metadata layout: 80 cylinders (FreeDOS distribution) and the
   NEC-compatible 77 cylinders. The larger values size static buffers. */
#define M19_TOTAL_SECTORS 1280U
#define M19_TOTAL_SECTORS_77 1232U
#define M19_SECTORS_PER_TRACK 8U
#define M19_HEADS 2U
#define M19_FAT_BYTES 2048U
#define M19_ROOT_ENTRIES 192U
#define M19_ROOT_BYTES 6144U
#define M19_FIRST_DATA_SECTOR 11U
#define M19_DATA_CLUSTERS 1269U
#define M19_CLUSTER_LIMIT (M19_DATA_CLUSTERS + 2U)

struct m19_layout {
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

enum m19_chain_error {
  M19_CHAIN_OK = 0,
  M19_CHAIN_BAD_ARGUMENT,
  M19_CHAIN_TRUNCATED_FAT,
  M19_CHAIN_BAD_START,
  M19_CHAIN_CROSS_LINK,
  M19_CHAIN_FREE_LINK,
  M19_CHAIN_RESERVED_LINK,
  M19_CHAIN_BAD_CLUSTER_LINK,
  M19_CHAIN_OUT_OF_RANGE,
  M19_CHAIN_CYCLE,
  M19_CHAIN_EARLY_END,
  M19_CHAIN_EXTRA_LINK
};

/* Return the cylinder count for a supported total, otherwise 0. */
unsigned m19_profile_cylinders(unsigned total_sectors);
/* Accept an extended BPB (signature 29h plus 55AA marks) or a DOS 2.x short
   BPB without marks, for either native profile. */
int m19_validate_bpb(const unsigned char *boot, unsigned bytes,
                     struct m19_layout *layout);
int m19_fat12_get(const unsigned char *fat, unsigned fat_bytes,
                  unsigned cluster, unsigned *value);
enum m19_chain_error m19_validate_chain(
    const unsigned char *fat, unsigned fat_bytes, unsigned data_clusters,
    unsigned first_cluster, unsigned expected_clusters,
    unsigned char *owned, unsigned owned_bytes, unsigned *actual_clusters);

#endif
