/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <string.h>
#include "fat12.h"

/* Compile-time proof that the fixed native profile constants agree. */
typedef char m20_profile_constants_agree[
    (M20_ROOT_BYTES == M20_ROOT_ENTRIES * 32U &&
     M20_ROOT_BYTES % M20_SECTOR_BYTES == 0 &&
     M20_FIRST_DATA_SECTOR == 1U + 2U * 2U + M20_ROOT_BYTES / M20_SECTOR_BYTES &&
     M20_TOTAL_SECTORS - M20_FIRST_DATA_SECTOR == M20_DATA_CLUSTERS &&
     (M20_DATA_CLUSTERS + 2U) * 3U / 2U <= M20_FAT_BYTES &&
     M20_FAT_BYTES == 2U * M20_SECTOR_BYTES) ? 1 : -1];

static unsigned m20_word(const unsigned char *p)
{
  return (unsigned)p[0] | ((unsigned)p[1] << 8);
}

static unsigned long m20_dword(const unsigned char *p)
{
  return (unsigned long)m20_word(p) | ((unsigned long)m20_word(p + 2) << 16);
}

unsigned m20_profile_cylinders(unsigned total_sectors)
{
  if (total_sectors == M20_TOTAL_SECTORS)
    return 80;
  if (total_sectors == M20_TOTAL_SECTORS_77)
    return 77;
  return 0;
}

int m20_validate_bpb(const unsigned char *boot, unsigned bytes,
                     struct m20_layout *layout)
{
  unsigned total, cylinders;
  int extended;

  if (!boot || !layout || bytes < M20_SECTOR_BYTES)
    return 0;
  total = m20_word(boot + 19);
  cylinders = m20_profile_cylinders(total);
  extended = boot[38] == 0x29;
  if (!cylinders ||
      m20_word(boot + 11) != M20_SECTOR_BYTES || boot[13] != 1 ||
      m20_word(boot + 14) != 1 || boot[16] != 2 ||
      m20_word(boot + 17) != M20_ROOT_ENTRIES || boot[21] != 0xfe ||
      m20_word(boot + 22) != 2 || m20_word(boot + 24) != M20_SECTORS_PER_TRACK ||
      m20_word(boot + 26) != M20_HEADS || m20_word(boot + 28) != 0)
    return 0;
  /* The extended form carries 32-bit hidden/huge fields and boot marks.
     A DOS 2.x short BPB ends before them; its later bytes are boot code. */
  if (extended &&
      (m20_dword(boot + 28) != 0 || m20_dword(boot + 32) != 0 ||
       boot[510] != 0x55 || boot[511] != 0xaa ||
       boot[1022] != 0x55 || boot[1023] != 0xaa))
    return 0;

  layout->bytes_per_sector = M20_SECTOR_BYTES;
  layout->sectors_per_cluster = 1;
  layout->reserved_sectors = 1;
  layout->fat_count = 2;
  layout->root_entries = M20_ROOT_ENTRIES;
  layout->total_sectors = total;
  layout->media_descriptor = 0xfe;
  layout->sectors_per_fat = 2;
  layout->sectors_per_track = M20_SECTORS_PER_TRACK;
  layout->heads = M20_HEADS;
  layout->fat_start = 1;
  layout->root_start = 5;
  layout->root_sectors = M20_ROOT_BYTES / M20_SECTOR_BYTES;
  layout->first_data_sector = M20_FIRST_DATA_SECTOR;
  layout->data_clusters = total - M20_FIRST_DATA_SECTOR;
  layout->cylinders = cylinders;
  return 1;
}

int m20_fat12_get(const unsigned char *fat, unsigned fat_bytes,
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

enum m20_chain_error m20_validate_chain(
    const unsigned char *fat, unsigned fat_bytes, unsigned data_clusters,
    unsigned first_cluster, unsigned expected_clusters,
    unsigned char *owned, unsigned owned_bytes, unsigned *actual_clusters)
{
  unsigned current, next, count = 0, limit;
  unsigned required_bytes;
  unsigned char local[512];

  if (actual_clusters)
    *actual_clusters = 0;
  if (!fat || !owned || !data_clusters || data_clusters > 0xffeU ||
      (expected_clusters && expected_clusters > data_clusters))
    return M20_CHAIN_BAD_ARGUMENT;
  limit = data_clusters + 2U;
  required_bytes = (limit + 7U) / 8U;
  if (owned_bytes < required_bytes ||
      (((limit - 1U) * 3U) / 2U) + 2U > fat_bytes)
    return M20_CHAIN_TRUNCATED_FAT;
  if (first_cluster < 2U || first_cluster >= limit)
    return M20_CHAIN_BAD_START;

  memset(local, 0, sizeof(local));
  current = first_cluster;
  for (;;) {
    unsigned byte_index;
    unsigned char bit;
    if (current < 2U || current >= limit)
      return M20_CHAIN_OUT_OF_RANGE;
    byte_index = current >> 3;
    bit = (unsigned char)(1U << (current & 7U));
    if (local[byte_index] & bit)
      return M20_CHAIN_CYCLE;
    if (owned[byte_index] & bit)
      return M20_CHAIN_CROSS_LINK;
    local[byte_index] |= bit;
    owned[byte_index] |= bit;
    ++count;
    if (!m20_fat12_get(fat, fat_bytes, current, &next))
      return M20_CHAIN_TRUNCATED_FAT;

    if (next >= 0xff8U) {
      /* count can never exceed expected_clusters here: that case already
         returned M20_CHAIN_EXTRA_LINK on the previous link. */
      if (expected_clusters && count < expected_clusters)
        return M20_CHAIN_EARLY_END;
      if (actual_clusters)
        *actual_clusters = count;
      return M20_CHAIN_OK;
    }
    if (expected_clusters && count >= expected_clusters)
      return M20_CHAIN_EXTRA_LINK;
    if (next == 0)
      return M20_CHAIN_FREE_LINK;
    if (next == 1U || (next >= 0xff0U && next <= 0xff6U))
      return M20_CHAIN_RESERVED_LINK;
    if (next == 0xff7U)
      return M20_CHAIN_BAD_CLUSTER_LINK;
    if (next < 2U || next >= limit)
      return M20_CHAIN_OUT_OF_RANGE;
    /* A revisit is reported by the local bitmap as M20_CHAIN_CYCLE. */
    current = next;
  }
}
