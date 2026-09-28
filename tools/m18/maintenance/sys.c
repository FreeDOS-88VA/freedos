/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <dos.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include "volume.h"

#define COPY_BYTES 8192U
#define SYSTEM_FILES 5U

struct system_file {
  const char *name;
  const char *dos_name;
  unsigned long size;
};

static struct system_file files[SYSTEM_FILES] = {
  {"LOADER.BIN", "LOADER  BIN", 0},
  {"KERNEL.SYS", "KERNEL  SYS", 0},
  {"COMMAND.COM", "COMMAND COM", 0},
  {"COUNTRY.SYS", "COUNTRY SYS", 0},
  {"CONFIG.SYS", "CONFIG  SYS", 0}
};
static struct m18_volume source_volume;
static struct m18_volume target_volume;
static struct m18_check_report source_report;
static struct m18_check_report target_report;
static unsigned char copy_buffer[COPY_BYTES];
static unsigned char verify_buffer[COPY_BYTES];
static unsigned char boot_verify[M18_SECTOR_BYTES];
static unsigned dos_error;

static unsigned word(const unsigned char *p)
{
  return (unsigned)p[0] | ((unsigned)p[1] << 8);
}

static unsigned long dword(const unsigned char *p)
{
  return (unsigned long)word(p) | ((unsigned long)word(p + 2) << 16);
}

static unsigned char *find_root(struct m18_volume *volume, const char *name)
{
  unsigned n;
  for (n = 0; n < M18_ROOT_ENTRIES; ++n) {
    unsigned char *entry = volume->root + n * 32U;
    if (!entry[0])
      break;
    if (entry[0] != 0xe5 && entry[11] != 0x0f &&
        !(entry[11] & 0x08) && memcmp(entry, name, 11) == 0)
      return entry;
  }
  return NULL;
}

static unsigned free_root_slots(struct m18_volume *volume)
{
  unsigned n, free_slots = 0;
  int ended = 0;
  for (n = 0; n < M18_ROOT_ENTRIES; ++n) {
    unsigned char *entry = volume->root + n * 32U;
    if (ended || entry[0] == 0xe5) {
      ++free_slots;
      continue;
    }
    if (!entry[0]) {
      ended = 1;
      ++free_slots;
    }
  }
  return free_slots;
}

static int validate_source(void)
{
  unsigned char *loader;
  unsigned first, current, count, expected, n;
  unsigned long size;
  if (source_volume.boot[0] == 0xeb && source_volume.boot[1] == 0xfe &&
      source_volume.boot[2] == 0x90)
    return 0;
  loader = find_root(&source_volume, "LOADER  BIN");
  if (!loader)
    return 0;
  first = current = word(loader + 26);
  size = dword(loader + 28);
  if (!size || size > 65535UL)
    return 0;
  expected = (unsigned)((size + M18_SECTOR_BYTES - 1U) / M18_SECTOR_BYTES);
  for (n = 0; n < SYSTEM_FILES; ++n) {
    unsigned char *entry = find_root(&source_volume, files[n].dos_name);
    if (!entry || (entry[11] & 0x18) || !dword(entry + 28))
      return 0;
    files[n].size = dword(entry + 28);
  }
  count = 0;
  while (count < expected) {
    unsigned next;
    if (current < 2 || current >= M18_CLUSTER_LIMIT ||
        !m18_fat12_get(source_volume.fat, sizeof(source_volume.fat),
                       current, &next))
      return 0;
    ++count;
    if (count == expected)
      return next >= 0xff8 && next <= 0xfff;
    if (next != current + 1U)
      return 0;
    current = next;
  }
  return 0;
}

static int confirm_install(void)
{
  char line[32];
  puts("SYS copies the native boot files from A: to the prepared 2HD B: disk.");
  puts("It writes the boot sector last; existing B: user files are preserved.");
  fputs("Type SYS to continue (anything else cancels): ", stdout);
  fflush(stdout);
  if (!fgets(line, sizeof(line), stdin))
    return 0;
  line[strcspn(line, "\r\n")] = 0;
  return strcmp(line, "SYS") == 0;
}

static int copy_file(unsigned index)
{
  char source_path[20], target_path[20];
  unsigned long remaining = files[index].size;
  unsigned got, written, amount;
  int source, target;
  sprintf(source_path, "A:\\%s", files[index].name);
  sprintf(target_path, "B:\\%s", files[index].name);
  dos_error = _dos_open(source_path, O_RDONLY, &source);
  if (dos_error)
    return 0;
  dos_error = _dos_creatnew(target_path, _A_NORMAL, &target);
  if (dos_error) {
    _dos_close(source);
    return 0;
  }
  while (remaining) {
    amount = remaining > COPY_BYTES ? COPY_BYTES : (unsigned)remaining;
    dos_error = _dos_read(source, copy_buffer, (unsigned)amount, &got);
    if (dos_error || got != amount) {
      _dos_close(source);
      _dos_close(target);
      return 0;
    }
    dos_error = _dos_write(target, copy_buffer, (unsigned)amount, &written);
    if (dos_error || written != amount) {
      _dos_close(source);
      _dos_close(target);
      return 0;
    }
    remaining -= amount;
  }
  dos_error = _dos_read(source, copy_buffer, 1, &got);
  if (dos_error || got) {
    _dos_close(source);
    _dos_close(target);
    return 0;
  }
  dos_error = _dos_commit(target);
  if (_dos_close(source) || _dos_close(target) || dos_error)
    return 0;

  dos_error = _dos_open(source_path, O_RDONLY, &source);
  if (dos_error)
    return 0;
  dos_error = _dos_open(target_path, O_RDONLY, &target);
  if (dos_error) {
    _dos_close(source);
    return 0;
  }
  remaining = files[index].size;
  while (remaining) {
    amount = remaining > COPY_BYTES ? COPY_BYTES : (unsigned)remaining;
    dos_error = _dos_read(source, copy_buffer, (unsigned)amount, &got);
    if (dos_error || got != amount) {
      _dos_close(source);
      _dos_close(target);
      return 0;
    }
    dos_error = _dos_read(target, verify_buffer, (unsigned)amount, &written);
    if (dos_error || written != amount ||
        memcmp(copy_buffer, verify_buffer, amount)) {
      _dos_close(source);
      _dos_close(target);
      return 0;
    }
    remaining -= amount;
  }
  dos_error = _dos_read(source, copy_buffer, 1, &got);
  if (dos_error || got) {
    _dos_close(source);
    _dos_close(target);
    return 0;
  }
  dos_error = _dos_read(target, verify_buffer, 1, &written);
  if (_dos_close(source) || _dos_close(target) || dos_error || written)
    return 0;
  return 1;
}

int main(int argc, char **argv)
{
  unsigned n, required_clusters = 0;
  unsigned long required_bytes = 0;
  unsigned free_slots;
  int good = 1;
  void (__interrupt __far *old24)(void);

  if (argc == 2 && (!strcmp(argv[1], "/?") || !strcmp(argv[1], "-?"))) {
    puts("SYS - install native PC-88VA 2HD boot files");
    puts("Usage: SYS A: B:");
    puts("Requires a validated bootable M18 2HD source in A: and a formatted 2HD B:.");
    puts("B: is the only permitted target; the boot sector is written last.");
    return 0;
  }
  if (argc != 3 || (strcmp(argv[1], "A:") && strcmp(argv[1], "a:")) ||
      (strcmp(argv[2], "B:") && strcmp(argv[2], "b:"))) {
    fputs("SYS: use SYS A: B:; other source/target combinations are refused.\n", stderr);
    return 2;
  }

  old24 = _dos_getvect(0x24);
  _dos_setvect(0x24, m18_critical);
  if (!m18_load_volume(0, &source_volume) ||
      !m18_check_allocations(0, &source_volume, &source_report) ||
      !validate_source()) {
    fputs("SYS: A: is not a valid native M18 boot source; B: was not changed.\n", stderr);
    _dos_setvect(0x24, old24);
    return 1;
  }
  if (!m18_load_volume(1, &target_volume) ||
      !m18_check_allocations(1, &target_volume, &target_report)) {
    fputs("SYS: B: must be a valid, already formatted native 2HD FAT12 disk.\n", stderr);
    _dos_setvect(0x24, old24);
    return 1;
  }
  for (n = 0; n < SYSTEM_FILES; ++n) {
    if (find_root(&target_volume, files[n].dos_name)) {
      fprintf(stderr, "SYS: B: already contains %s; no file was replaced.\n",
              files[n].name);
      _dos_setvect(0x24, old24);
      return 1;
    }
    required_clusters += (unsigned)((files[n].size + M18_SECTOR_BYTES - 1U) /
                                    M18_SECTOR_BYTES);
    required_bytes += ((files[n].size + M18_SECTOR_BYTES - 1U) /
                       M18_SECTOR_BYTES) * (unsigned long)M18_SECTOR_BYTES;
  }
  free_slots = free_root_slots(&target_volume);
  if (target_report.free_clusters < required_clusters ||
      free_slots < SYSTEM_FILES) {
    fprintf(stderr, "SYS: B: lacks space (needs %u clusters and %u root slots).\n",
            required_clusters, SYSTEM_FILES);
    _dos_setvect(0x24, old24);
    return 1;
  }
  if (!confirm_install()) {
    puts("SYS: cancelled; B: was not changed.");
    _dos_setvect(0x24, old24);
    return 1;
  }

  for (n = 0; n < SYSTEM_FILES && good; ++n)
    good = copy_file(n);
  if (good) {
    m18_reset_disk();
    good = m18_write_sector(1, 0, source_volume.boot) &&
           m18_read_sector(1, 0, boot_verify) &&
           memcmp(source_volume.boot, boot_verify, M18_SECTOR_BYTES) == 0;
  }
  m18_reset_disk();
  if (good)
    good = m18_load_volume(1, &target_volume) &&
           m18_check_allocations(1, &target_volume, &target_report) &&
           !memcmp(target_volume.boot, source_volume.boot, M18_SECTOR_BYTES);
  for (n = 0; n < SYSTEM_FILES && good; ++n) {
    unsigned char *entry = find_root(&target_volume, files[n].dos_name);
    if (!entry || dword(entry + 28) != files[n].size)
      good = 0;
  }
  if (good) {
    printf("SYS: installed %u boot files (%lu data bytes) on native 2HD B:.\n",
           SYSTEM_FILES, required_bytes);
    puts("Boot B: separately; the source A: disk was not modified.");
  } else {
    fprintf(stderr, "SYS: transfer/readback failed (DOS error %u); B: may be incomplete.\n",
            dos_error);
  }
  _dos_setvect(0x24, old24);
  return good ? 0 : 1;
}
