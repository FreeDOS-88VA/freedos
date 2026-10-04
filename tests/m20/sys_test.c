/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Host fixtures for the production SYS transfer: A: and B: sector images with a
   minimal DOS file layer whose cluster allocator start can be selected. */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define main m20_sys_main
#include "../../tools/m20/maintenance/sys.c"
#undef main

#define ROOT_SECTOR 5U
#define MAX_HANDLES 4

static unsigned char image[2][M20_TOTAL_SECTORS][M20_SECTOR_BYTES];
static unsigned allocation_start[2];
static unsigned long target_writes;
static unsigned target_total = M20_TOTAL_SECTORS;

struct test_handle {
  int used;
  unsigned drive;
  unsigned entry;
  unsigned first;
  unsigned last;
  unsigned long position;
  unsigned long size;
  int writing;
};

static struct test_handle handles[MAX_HANDLES];

static void set16(unsigned char *p, unsigned value)
{
  p[0] = (unsigned char)value;
  p[1] = (unsigned char)(value >> 8);
}

static void set32(unsigned char *p, unsigned long value)
{
  set16(p, (unsigned)value);
  set16(p + 2, (unsigned)(value >> 16));
}

static unsigned get16(const unsigned char *p)
{
  return (unsigned)p[0] | ((unsigned)p[1] << 8);
}

static unsigned long get32(const unsigned char *p)
{
  return (unsigned long)get16(p) | ((unsigned long)get16(p + 2) << 16);
}

static unsigned char *root_entry(unsigned drive, unsigned index)
{
  return image[drive][ROOT_SECTOR + index / 32U] + (index % 32U) * 32U;
}

static unsigned fat_value(unsigned drive, unsigned cluster)
{
  unsigned value;
  assert(m20_fat12_get(image[drive][1], M20_FAT_BYTES, cluster, &value));
  return value;
}

static void fat_store(unsigned drive, unsigned cluster, unsigned value)
{
  unsigned copy;
  for (copy = 0; copy < 2; ++copy) {
    unsigned char *fat = image[drive][1U + copy * 2U];
    unsigned offset = cluster + cluster / 2U;
    unsigned packed = fat[offset] | ((unsigned)fat[offset + 1] << 8);
    if (cluster & 1U)
      packed = (packed & 0x000fU) | (value << 4);
    else
      packed = (packed & 0xf000U) | value;
    fat[offset] = (unsigned char)packed;
    fat[offset + 1] = (unsigned char)(packed >> 8);
  }
}

static unsigned char *cluster_data(unsigned drive, unsigned cluster)
{
  return image[drive][M20_FIRST_DATA_SECTOR + cluster - 2U];
}

static void format_image(unsigned drive, unsigned char first_byte)
{
  unsigned char *boot = image[drive][0];
  memset(image[drive], 0, sizeof(image[drive]));
  boot[0] = first_byte;
  boot[1] = first_byte == 0xeb ? 0xfe : 0x3c;
  boot[2] = 0x90;
  memcpy(boot + 3, "FDPC88VA", 8);
  set16(boot + 11, M20_SECTOR_BYTES);
  boot[13] = 1;
  set16(boot + 14, 1);
  boot[16] = 2;
  set16(boot + 17, M20_ROOT_ENTRIES);
  set16(boot + 19, drive == 1 ? target_total : M20_TOTAL_SECTORS);
  boot[21] = 0xfe;
  set16(boot + 22, 2);
  set16(boot + 24, 8);
  set16(boot + 26, 2);
  boot[38] = 0x29;
  memcpy(boot + 43, drive == 1 ? "TARGETDISK " : "PC88VA-M20 ", 11);
  memcpy(boot + 54, "FAT12   ", 8);
  boot[100] = (unsigned char)(drive + 0x40);
  boot[510] = boot[1022] = 0x55;
  boot[511] = boot[1023] = 0xaa;
  image[drive][1][0] = image[drive][3][0] = 0xfe;
  image[drive][1][1] = image[drive][3][1] = 0xff;
  image[drive][1][2] = image[drive][3][2] = 0xff;
  memcpy(root_entry(drive, 0), "PC88VA-M20 ", 11);
  root_entry(drive, 0)[11] = 0x08;
}

/* Place one file at explicit clusters; used for source and pre-existing files. */
static void place_file(unsigned drive, unsigned index, const char *dos_name,
                       unsigned long size, const unsigned *clusters,
                       unsigned count)
{
  unsigned char *entry = root_entry(drive, index);
  unsigned n;
  memcpy(entry, dos_name, 11);
  entry[11] = 0x20;
  set16(entry + 26, count ? clusters[0] : 0);
  set32(entry + 28, size);
  for (n = 0; n < count; ++n) {
    memset(cluster_data(drive, clusters[n]), (int)(index * 17U + n), M20_SECTOR_BYTES);
    fat_store(drive, clusters[n], n + 1U < count ? clusters[n + 1U] : 0xfffU);
  }
}

static void make_source(int fragmented_loader)
{
  static const unsigned loader[] = {2, 3};
  static const unsigned loader_split[] = {2, 4};
  static const unsigned kernel[] = {5, 6, 7};
  static const unsigned command[] = {8, 9};
  static const unsigned country[] = {10};
  static const unsigned config[] = {11};
  format_image(0, 0xe9);
  place_file(0, 1, "LOADER  BIN", 1500UL,
             fragmented_loader ? loader_split : loader, 2);
  place_file(0, 2, "KERNEL  SYS", 2100UL, kernel, 3);
  place_file(0, 3, "COMMAND COM", 2048UL, command, 2);
  place_file(0, 4, "COUNTRY SYS", 10UL, country, 1);
  place_file(0, 5, "CONFIG  SYS", 20UL, config, 1);
}

static void make_target(int user_file_at_two)
{
  static const unsigned user[] = {2};
  format_image(1, 0xeb);
  if (user_file_at_two)
    place_file(1, 1, "USER    TXT", 5UL, user, 1);
  allocation_start[1] = 2;
}

int intdos(union REGS *input, union REGS *output)
{
  memset(output, 0, sizeof(*output));
  assert(input->h.ah == 0x36 || input->h.ah == 0x0d);
  return 0;
}

unsigned m20_abs_sector(unsigned writing, unsigned drive, unsigned sector,
                        void *buffer)
{
  if (drive > 1 || sector >= M20_TOTAL_SECTORS || !buffer)
    return 1;
  if (writing) {
    memcpy(image[drive][sector], buffer, M20_SECTOR_BYTES);
    if (drive == 1)
      ++target_writes;
  } else {
    memcpy(buffer, image[drive][sector], M20_SECTOR_BYTES);
  }
  return 0;
}

void m20_critical(void) { }

void (*_dos_getvect(unsigned vector))(void)
{
  (void)vector;
  return m20_critical;
}

void _dos_setvect(unsigned vector, void (*handler)(void))
{
  (void)vector;
  (void)handler;
}

static int parse_path(const char *path, unsigned *drive, char name[11])
{
  const char *p;
  unsigned n = 0;
  if ((path[0] != 'A' && path[0] != 'B') || path[1] != ':' || path[2] != '\\')
    return 0;
  *drive = (unsigned)(path[0] - 'A');
  memset(name, ' ', 11);
  for (p = path + 3; *p && *p != '.'; ++p)
    name[n++] = *p;
  if (*p == '.')
    for (n = 8, ++p; *p; ++p)
      name[n++] = *p;
  return 1;
}

static int find_entry(unsigned drive, const char name[11], unsigned *index)
{
  unsigned n;
  for (n = 0; n < M20_ROOT_ENTRIES; ++n) {
    unsigned char *entry = root_entry(drive, n);
    if (!entry[0])
      return 0;
    if (entry[0] != 0xe5 && !(entry[11] & 0x08) && !memcmp(entry, name, 11)) {
      *index = n;
      return 1;
    }
  }
  return 0;
}

static int new_handle(void)
{
  int n;
  for (n = 0; n < MAX_HANDLES; ++n)
    if (!handles[n].used) {
      memset(&handles[n], 0, sizeof(handles[n]));
      handles[n].used = 1;
      return n;
    }
  return -1;
}

unsigned _dos_open(const char *path, unsigned mode, int *handle)
{
  unsigned drive, index;
  char name[11];
  int h;
  (void)mode;
  if (!parse_path(path, &drive, name) || !find_entry(drive, name, &index) ||
      (h = new_handle()) < 0)
    return 2;
  handles[h].drive = drive;
  handles[h].entry = index;
  handles[h].first = get16(root_entry(drive, index) + 26);
  handles[h].size = get32(root_entry(drive, index) + 28);
  *handle = h;
  return 0;
}

unsigned _dos_creatnew(const char *path, unsigned attributes, int *handle)
{
  unsigned drive, index, n;
  char name[11];
  int h;
  (void)attributes;
  if (!parse_path(path, &drive, name) || find_entry(drive, name, &index))
    return 80;
  for (n = 0; n < M20_ROOT_ENTRIES; ++n) {
    unsigned char *entry = root_entry(drive, n);
    if (!entry[0] || entry[0] == 0xe5)
      break;
  }
  if (n == M20_ROOT_ENTRIES || (h = new_handle()) < 0)
    return 5;
  memset(root_entry(drive, n), 0, 32);
  memcpy(root_entry(drive, n), name, 11);
  root_entry(drive, n)[11] = 0x20;
  handles[h].drive = drive;
  handles[h].entry = n;
  handles[h].writing = 1;
  *handle = h;
  return 0;
}

static unsigned cluster_at(struct test_handle *h, unsigned long position)
{
  unsigned cluster = h->first;
  unsigned long skip = position / M20_SECTOR_BYTES;
  while (skip--)
    cluster = fat_value(h->drive, cluster);
  return cluster;
}

unsigned _dos_read(int handle, void *buffer, unsigned count, unsigned *bytes)
{
  struct test_handle *h = &handles[handle];
  unsigned char *out = buffer;
  unsigned done = 0;
  while (done < count && h->position < h->size) {
    unsigned cluster = cluster_at(h, h->position);
    out[done++] = cluster_data(h->drive, cluster)[h->position % M20_SECTOR_BYTES];
    ++h->position;
  }
  *bytes = done;
  return 0;
}

static unsigned allocate(unsigned drive)
{
  unsigned n, cluster = allocation_start[drive];
  for (n = 0; n < M20_DATA_CLUSTERS; ++n) {
    if (!fat_value(drive, cluster)) {
      fat_store(drive, cluster, 0xfffU);
      allocation_start[drive] = cluster + 1U;
      return cluster;
    }
    if (++cluster >= M20_CLUSTER_LIMIT)
      cluster = 2;
  }
  return 0;
}

unsigned _dos_write(int handle, void *buffer, unsigned count, unsigned *bytes)
{
  struct test_handle *h = &handles[handle];
  const unsigned char *in = buffer;
  unsigned done = 0;
  while (done < count) {
    if (h->position % M20_SECTOR_BYTES == 0) {
      unsigned cluster = allocate(h->drive);
      if (!cluster)
        return 39;
      if (h->last)
        fat_store(h->drive, h->last, cluster);
      else
        h->first = cluster;
      h->last = cluster;
    }
    cluster_data(h->drive, h->last)[h->position % M20_SECTOR_BYTES] = in[done++];
    ++h->position;
  }
  if (h->position > h->size)
    h->size = h->position;
  *bytes = done;
  return 0;
}

unsigned _dos_commit(int handle)
{
  (void)handle;
  return 0;
}

unsigned _dos_close(int handle)
{
  struct test_handle *h = &handles[handle];
  if (h->writing) {
    set16(root_entry(h->drive, h->entry) + 26, h->first);
    set32(root_entry(h->drive, h->entry) + 28, h->size);
  }
  h->used = 0;
  return 0;
}

static int run_sys(void)
{
  static char program[] = "SYS", source[] = "A:", target[] = "B:";
  char *argv[4];
  unsigned n;
  argv[0] = program;
  argv[1] = source;
  argv[2] = target;
  argv[3] = NULL;
  for (n = 0; n < SYSTEM_FILES; ++n)
    files[n].size = 0;
  target_writes = 0;
  return m20_sys_main(3, argv);
}

static unsigned target_loader_first(void)
{
  unsigned index;
  assert(find_entry(1, "LOADER  BIN", &index));
  return get16(root_entry(1, index) + 26);
}

int main(void)
{
  static unsigned char before[M20_TOTAL_SECTORS][M20_SECTOR_BYTES];
  unsigned char formatted_boot[M20_SECTOR_BYTES];

  /* Fresh B:: LOADER.BIN lands on the source extent and the boot is written. */
  make_source(0);
  make_target(0);
  assert(run_sys() == 0);
  assert(!memcmp(image[1][0], image[0][0], 11));
  assert(!memcmp(image[1][0] + 11, image[0][0] + 11, 28));
  assert(!memcmp(image[1][0] + 43, "TARGETDISK ", 11));
  assert(!memcmp(image[1][0] + 62, image[0][0] + 62, M20_SECTOR_BYTES - 62));
  assert(target_loader_first() == 2);
  assert(fat_value(1, 2) == 3 && fat_value(1, 3) >= 0xff8);

  /* A user file on the loader extent is refused before any B: write. */
  make_source(0);
  make_target(1);
  memcpy(before, image[1], sizeof(before));
  assert(run_sys() == 1);
  assert(target_writes == 0 && !memcmp(before, image[1], sizeof(before)));

  /* DOS placed LOADER.BIN elsewhere: the boot sector is never installed. */
  make_source(0);
  make_target(0);
  allocation_start[1] = 100;
  memcpy(formatted_boot, image[1][0], sizeof(formatted_boot));
  assert(run_sys() == 1);
  assert(!memcmp(image[1][0], formatted_boot, sizeof(formatted_boot)));
  assert(target_loader_first() == 100);

  /* A fragmented source loader is not a valid boot source. */
  make_source(1);
  make_target(0);
  memcpy(before, image[1], sizeof(before));
  assert(run_sys() == 1);
  assert(target_writes == 0 && !memcmp(before, image[1], sizeof(before)));

  /* A 77-cylinder target keeps its own geometry and label; the code is A:'s. */
  make_source(0);
  target_total = M20_TOTAL_SECTORS_77;
  make_target(0);
  assert(run_sys() == 0);
  assert(get16(image[1][0] + 19) == M20_TOTAL_SECTORS_77);
  assert(!memcmp(image[1][0] + 43, "TARGETDISK ", 11));
  assert(!memcmp(image[1][0] + 62, image[0][0] + 62, M20_SECTOR_BYTES - 62));
  assert(!memcmp(image[1][0], image[0][0], 3) && image[1][0][38] == 0x29);
  target_total = M20_TOTAL_SECTORS;

  puts("M20 SYS loader-extent transfer tests: PASS");
  return 0;
}
