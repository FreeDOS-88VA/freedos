/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M18_FAT12_H
#define M18_FAT12_H

#define M18_SECTOR_BYTES 1024U
#define M18_TOTAL_SECTORS 1280U
#define M18_FAT_BYTES 2048U
#define M18_ROOT_ENTRIES 192U
#define M18_ROOT_BYTES 6144U
#define M18_FIRST_DATA_SECTOR 11U
#define M18_DATA_CLUSTERS 1269U
#define M18_CLUSTER_LIMIT (M18_DATA_CLUSTERS + 2U)

struct m18_layout {
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
};

enum m18_chain_error {
  M18_CHAIN_OK = 0,
  M18_CHAIN_BAD_ARGUMENT,
  M18_CHAIN_TRUNCATED_FAT,
  M18_CHAIN_BAD_START,
  M18_CHAIN_CROSS_LINK,
  M18_CHAIN_FREE_LINK,
  M18_CHAIN_RESERVED_LINK,
  M18_CHAIN_BAD_CLUSTER_LINK,
  M18_CHAIN_OUT_OF_RANGE,
  M18_CHAIN_CYCLE,
  M18_CHAIN_EARLY_END,
  M18_CHAIN_EXTRA_LINK
};

int m18_validate_bpb(const unsigned char *boot, unsigned bytes,
                     struct m18_layout *layout);
int m18_fat12_get(const unsigned char *fat, unsigned fat_bytes,
                  unsigned cluster, unsigned *value);
enum m18_chain_error m18_validate_chain(
    const unsigned char *fat, unsigned fat_bytes, unsigned data_clusters,
    unsigned first_cluster, unsigned expected_clusters,
    unsigned char *owned, unsigned owned_bytes, unsigned *actual_clusters);

#endif
