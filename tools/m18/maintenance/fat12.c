/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <string.h>
#include "fat12.h"

static unsigned m18_word(const unsigned char *p)
{
  return (unsigned)p[0] | ((unsigned)p[1] << 8);
}

static unsigned long m18_dword(const unsigned char *p)
{
  return (unsigned long)m18_word(p) | ((unsigned long)m18_word(p + 2) << 16);
}

int m18_validate_bpb(const unsigned char *boot, unsigned bytes,
                     struct m18_layout *layout)
{
  unsigned root_sectors;
  unsigned first_data;
  unsigned clusters;

  if (!boot || !layout || bytes < M18_SECTOR_BYTES)
    return 0;
  if (m18_word(boot + 11) != M18_SECTOR_BYTES || boot[13] != 1 ||
      m18_word(boot + 14) != 1 || boot[16] != 2 ||
      m18_word(boot + 17) != M18_ROOT_ENTRIES ||
      m18_word(boot + 19) != M18_TOTAL_SECTORS || boot[21] != 0xfe ||
      m18_word(boot + 22) != 2 || m18_word(boot + 24) != 8 ||
      m18_word(boot + 26) != 2 || m18_dword(boot + 28) != 0 ||
      m18_dword(boot + 32) != 0 || boot[38] != 0x29 ||
      boot[510] != 0x55 || boot[511] != 0xaa ||
      boot[1022] != 0x55 || boot[1023] != 0xaa)
    return 0;

  root_sectors = (M18_ROOT_ENTRIES * 32U + M18_SECTOR_BYTES - 1U) /
                 M18_SECTOR_BYTES;
  first_data = 1U + 2U * 2U + root_sectors;
  if (first_data >= M18_TOTAL_SECTORS)
    return 0;
  clusters = M18_TOTAL_SECTORS - first_data;
  if (clusters != M18_DATA_CLUSTERS ||
      (clusters + 2U) * 3U / 2U > M18_FAT_BYTES)
    return 0;

  layout->bytes_per_sector = M18_SECTOR_BYTES;
  layout->sectors_per_cluster = 1;
  layout->reserved_sectors = 1;
  layout->fat_count = 2;
  layout->root_entries = M18_ROOT_ENTRIES;
  layout->total_sectors = M18_TOTAL_SECTORS;
  layout->media_descriptor = 0xfe;
  layout->sectors_per_fat = 2;
  layout->sectors_per_track = 8;
  layout->heads = 2;
  layout->fat_start = 1;
  layout->root_start = 5;
  layout->root_sectors = root_sectors;
  layout->first_data_sector = first_data;
  layout->data_clusters = clusters;
  return 1;
}

int m18_fat12_get(const unsigned char *fat, unsigned fat_bytes,
                  unsigned cluster, unsigned *value)
{
  unsigned offset;
  unsigned packed;
  if (!fat || !value || cluster > 0xfffU)
    return 0;
  offset = cluster + cluster / 2U;
  if (offset >= fat_bytes || fat_bytes - offset < 2U)
    return 0;
  packed = (unsigned)fat[offset] | ((unsigned)fat[offset + 1U] << 8);
  *value = (cluster & 1U) ? packed >> 4 : packed & 0xfffU;
  return 1;
}

enum m18_chain_error m18_validate_chain(
    const unsigned char *fat, unsigned fat_bytes, unsigned data_clusters,
    unsigned first_cluster, unsigned expected_clusters,
    unsigned char *owned, unsigned owned_bytes, unsigned *actual_clusters)
{
  unsigned current, next, count = 0, limit, index;
  unsigned required_bytes;
  unsigned char local[512];

  if (actual_clusters)
    *actual_clusters = 0;
  if (!fat || !owned || !data_clusters || data_clusters > 0xffeU ||
      (expected_clusters && expected_clusters > data_clusters))
    return M18_CHAIN_BAD_ARGUMENT;
  limit = data_clusters + 2U;
  required_bytes = (limit + 7U) / 8U;
  if (owned_bytes < required_bytes ||
      (((limit - 1U) * 3U) / 2U) + 2U > fat_bytes)
    return M18_CHAIN_TRUNCATED_FAT;
  if (first_cluster < 2U || first_cluster >= limit)
    return M18_CHAIN_BAD_START;

  memset(local, 0, sizeof(local));
  current = first_cluster;
  for (;;) {
    unsigned byte_index;
    unsigned char bit;
    if (current < 2U || current >= limit)
      return M18_CHAIN_OUT_OF_RANGE;
    index = current;
    byte_index = index >> 3;
    bit = (unsigned char)(1U << (index & 7U));
    if (local[byte_index] & bit)
      return M18_CHAIN_CYCLE;
    if (owned[byte_index] & bit)
      return M18_CHAIN_CROSS_LINK;
    local[byte_index] |= bit;
    owned[byte_index] |= bit;
    ++count;
    if (!m18_fat12_get(fat, fat_bytes, current, &next))
      return M18_CHAIN_TRUNCATED_FAT;

    if (next >= 0xff8U && next <= 0xfffU) {
      if (expected_clusters && count < expected_clusters)
        return M18_CHAIN_EARLY_END;
      if (expected_clusters && count > expected_clusters)
        return M18_CHAIN_EXTRA_LINK;
      if (actual_clusters)
        *actual_clusters = count;
      return M18_CHAIN_OK;
    }
    if (expected_clusters && count >= expected_clusters)
      return M18_CHAIN_EXTRA_LINK;
    if (next == 0)
      return M18_CHAIN_FREE_LINK;
    if (next == 1U || (next >= 0xff0U && next <= 0xff6U))
      return M18_CHAIN_RESERVED_LINK;
    if (next == 0xff7U)
      return M18_CHAIN_BAD_CLUSTER_LINK;
    if (next < 2U || next >= limit)
      return M18_CHAIN_OUT_OF_RANGE;
    if (count >= data_clusters)
      return M18_CHAIN_CYCLE;
    current = next;
  }
}
