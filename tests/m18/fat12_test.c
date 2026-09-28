/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../../tools/m18/maintenance/fat12.h"

static void put16(unsigned char *p, unsigned n)
{
  p[0] = (unsigned char)n;
  p[1] = (unsigned char)(n >> 8);
}

static void put32(unsigned char *p, unsigned long n)
{
  put16(p, (unsigned)n);
  put16(p + 2, (unsigned)(n >> 16));
}

static void set_fat(unsigned char *fat, unsigned cluster, unsigned value)
{
  unsigned offset = cluster + cluster / 2U;
  unsigned word = fat[offset] | ((unsigned)fat[offset + 1] << 8);
  if (cluster & 1U)
    word = (word & 0x000fU) | (value << 4);
  else
    word = (word & 0xf000U) | value;
  fat[offset] = (unsigned char)word;
  fat[offset + 1] = (unsigned char)(word >> 8);
}

static void make_boot(unsigned char *boot)
{
  memset(boot, 0, M18_SECTOR_BYTES);
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
  boot[510] = 0x55;
  boot[511] = 0xaa;
  boot[1022] = 0x55;
  boot[1023] = 0xaa;
}

static enum m18_chain_error chain(unsigned char *fat, unsigned first,
                                  unsigned expected, unsigned char *owned,
                                  unsigned *count)
{
  return m18_validate_chain(fat, M18_FAT_BYTES, M18_DATA_CLUSTERS,
                            first, expected, owned, sizeof(unsigned char) * 512,
                            count);
}

int main(void)
{
  unsigned char boot[M18_SECTOR_BYTES];
  unsigned char fat[M18_FAT_BYTES];
  unsigned char owned[512];
  struct m18_layout layout;
  unsigned count, value;

  make_boot(boot);
  assert(m18_validate_bpb(boot, sizeof(boot), &layout));
  assert(layout.first_data_sector == 11 && layout.data_clusters == 1269);
  assert(layout.root_sectors == 6 && layout.fat_start == 1 && layout.root_start == 5);
  assert(!m18_validate_bpb(boot, 511, &layout));
  boot[13] = 2;
  assert(!m18_validate_bpb(boot, sizeof(boot), &layout));
  make_boot(boot);
  put16(boot + 24, 9);
  assert(!m18_validate_bpb(boot, sizeof(boot), &layout));
  make_boot(boot);
  put16(boot + 17, 193);
  assert(!m18_validate_bpb(boot, sizeof(boot), &layout));
  make_boot(boot);
  put32(boot + 28, 1);
  assert(!m18_validate_bpb(boot, sizeof(boot), &layout));
  make_boot(boot);
  boot[1023] = 0;
  assert(!m18_validate_bpb(boot, sizeof(boot), &layout));

  memset(fat, 0, sizeof(fat));
  set_fat(fat, 0, 0x0fe);
  set_fat(fat, 1, 0xfff);
  set_fat(fat, 2, 0xfff);
  set_fat(fat, 3, 4);
  set_fat(fat, 4, 0xff8);
  assert(m18_fat12_get(fat, sizeof(fat), 0, &value) && value == 0x0fe);
  assert(m18_fat12_get(fat, sizeof(fat), 1, &value) && value == 0xfff);
  assert(m18_fat12_get(fat, sizeof(fat), 2, &value) && value == 0xfff);
  assert(!m18_fat12_get(fat, 1906, 1270, &value));

  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 1, owned, &count) == M18_CHAIN_OK && count == 1);
  assert(chain(fat, 3, 2, owned, &count) == M18_CHAIN_OK && count == 2);
  set_fat(fat, 5, 3);
  assert(chain(fat, 5, 0, owned, &count) == M18_CHAIN_CROSS_LINK);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 3, 2, owned, &count) == M18_CHAIN_OK && count == 2);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 3, 1, owned, &count) == M18_CHAIN_EXTRA_LINK);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 3, 3, owned, &count) == M18_CHAIN_EARLY_END);

  memset(fat, 0, sizeof(fat));
  set_fat(fat, 2, 0);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M18_CHAIN_FREE_LINK);
  set_fat(fat, 2, 1);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M18_CHAIN_RESERVED_LINK);
  set_fat(fat, 2, 0xff7);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M18_CHAIN_BAD_CLUSTER_LINK);
  set_fat(fat, 2, 1271);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M18_CHAIN_OUT_OF_RANGE);
  set_fat(fat, 2, 3);
  set_fat(fat, 3, 2);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M18_CHAIN_CYCLE);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 1, 0, owned, &count) == M18_CHAIN_BAD_START);
  assert(m18_validate_chain(fat, 2, M18_DATA_CLUSTERS, 2, 0,
                            owned, sizeof(owned), &count) == M18_CHAIN_TRUNCATED_FAT);
  assert(m18_validate_chain(fat, M18_FAT_BYTES, M18_DATA_CLUSTERS, 2, 0,
                            owned, 1, &count) == M18_CHAIN_TRUNCATED_FAT);

  puts("M18 FAT12 native-profile tests: PASS");
  return 0;
}
