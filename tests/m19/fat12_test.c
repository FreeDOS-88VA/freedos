/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../../tools/m19/maintenance/fat12.h"

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
  memset(boot, 0, M19_SECTOR_BYTES);
  put16(boot + 11, M19_SECTOR_BYTES);
  boot[13] = 1;
  put16(boot + 14, 1);
  boot[16] = 2;
  put16(boot + 17, M19_ROOT_ENTRIES);
  put16(boot + 19, M19_TOTAL_SECTORS);
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

static enum m19_chain_error chain(unsigned char *fat, unsigned first,
                                  unsigned expected, unsigned char *owned,
                                  unsigned *count)
{
  return m19_validate_chain(fat, M19_FAT_BYTES, M19_DATA_CLUSTERS,
                            first, expected, owned, sizeof(unsigned char) * 512,
                            count);
}

int main(void)
{
  unsigned char boot[M19_SECTOR_BYTES];
  unsigned char fat[M19_FAT_BYTES];
  unsigned char owned[512];
  struct m19_layout layout;
  unsigned count, value;

  make_boot(boot);
  assert(m19_validate_bpb(boot, sizeof(boot), &layout));
  assert(layout.first_data_sector == 11 && layout.data_clusters == 1269);
  assert(layout.root_sectors == 6 && layout.fat_start == 1 && layout.root_start == 5);
  assert(!m19_validate_bpb(boot, 511, &layout));
  boot[13] = 2;
  assert(!m19_validate_bpb(boot, sizeof(boot), &layout));
  make_boot(boot);
  put16(boot + 24, 9);
  assert(!m19_validate_bpb(boot, sizeof(boot), &layout));
  make_boot(boot);
  put16(boot + 17, 193);
  assert(!m19_validate_bpb(boot, sizeof(boot), &layout));
  make_boot(boot);
  put32(boot + 28, 1);
  assert(!m19_validate_bpb(boot, sizeof(boot), &layout));
  make_boot(boot);
  boot[1023] = 0;
  assert(!m19_validate_bpb(boot, sizeof(boot), &layout));

  /* NEC-compatible 77 cylinders share the metadata layout. */
  make_boot(boot);
  put16(boot + 19, M19_TOTAL_SECTORS_77);
  assert(m19_validate_bpb(boot, sizeof(boot), &layout));
  assert(layout.cylinders == 77 && layout.total_sectors == 1232);
  assert(layout.data_clusters == 1221 && layout.first_data_sector == 11);
  put16(boot + 19, 1250);
  assert(!m19_validate_bpb(boot, sizeof(boot), &layout));
  assert(m19_profile_cylinders(1280) == 80 && m19_profile_cylinders(1232) == 77 &&
         !m19_profile_cylinders(1440));

  /* A DOS 2.x short BPB (MS-DOS 2.11 media) has no 29h mark or 55AA; the
     bytes after offset 30 are boot code and are not interpreted. */
  make_boot(boot);
  put16(boot + 19, M19_TOTAL_SECTORS_77);
  boot[38] = 0x8e;
  put16(boot + 32, 0xbcfe);
  boot[510] = boot[511] = boot[1022] = boot[1023] = 0;
  assert(m19_validate_bpb(boot, sizeof(boot), &layout) && layout.cylinders == 77);
  put16(boot + 28, 1);
  assert(!m19_validate_bpb(boot, sizeof(boot), &layout));

  memset(fat, 0, sizeof(fat));
  set_fat(fat, 0, 0x0fe);
  set_fat(fat, 1, 0xfff);
  set_fat(fat, 2, 0xfff);
  set_fat(fat, 3, 4);
  set_fat(fat, 4, 0xff8);
  assert(m19_fat12_get(fat, sizeof(fat), 0, &value) && value == 0x0fe);
  assert(m19_fat12_get(fat, sizeof(fat), 1, &value) && value == 0xfff);
  assert(m19_fat12_get(fat, sizeof(fat), 2, &value) && value == 0xfff);
  assert(!m19_fat12_get(fat, 1906, 1270, &value));

  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 1, owned, &count) == M19_CHAIN_OK && count == 1);
  assert(chain(fat, 3, 2, owned, &count) == M19_CHAIN_OK && count == 2);
  set_fat(fat, 5, 3);
  assert(chain(fat, 5, 0, owned, &count) == M19_CHAIN_CROSS_LINK);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 3, 2, owned, &count) == M19_CHAIN_OK && count == 2);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 3, 1, owned, &count) == M19_CHAIN_EXTRA_LINK);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 3, 3, owned, &count) == M19_CHAIN_EARLY_END);

  memset(fat, 0, sizeof(fat));
  set_fat(fat, 2, 0);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M19_CHAIN_FREE_LINK);
  set_fat(fat, 2, 1);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M19_CHAIN_RESERVED_LINK);
  set_fat(fat, 2, 0xff7);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M19_CHAIN_BAD_CLUSTER_LINK);
  set_fat(fat, 2, 1271);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M19_CHAIN_OUT_OF_RANGE);
  set_fat(fat, 2, 3);
  set_fat(fat, 3, 2);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 2, 0, owned, &count) == M19_CHAIN_CYCLE);
  memset(owned, 0, sizeof(owned));
  assert(chain(fat, 1, 0, owned, &count) == M19_CHAIN_BAD_START);
  assert(m19_validate_chain(fat, 2, M19_DATA_CLUSTERS, 2, 0,
                            owned, sizeof(owned), &count) == M19_CHAIN_TRUNCATED_FAT);
  assert(m19_validate_chain(fat, M19_FAT_BYTES, M19_DATA_CLUSTERS, 2, 0,
                            owned, 1, &count) == M19_CHAIN_TRUNCATED_FAT);

  puts("M19 FAT12 native-profile tests: PASS");
  return 0;
}
