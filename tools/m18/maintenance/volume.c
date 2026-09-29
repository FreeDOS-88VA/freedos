/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <dos.h>
#include <string.h>
#include "volume.h"

static unsigned char sector_buffer[M18_SECTOR_BYTES];
static unsigned char mirror_buffer[M18_SECTOR_BYTES];

void m18_reset_disk(void)
{
  union REGS in, out;
  memset(&in, 0, sizeof(in));
  in.h.ah = 0x0d;
  intdos(&in, &out);
}

int m18_bind_volume(unsigned drive)
{
  union REGS in, out;
  if (drive > 1)
    return 0;
  memset(&in, 0, sizeof(in));
  in.h.ah = 0x32;
  in.h.dl = (unsigned char)(drive + 1);
  /* Establish a fresh DOS media binding before starting an operation.
     Never rebind/retry inside a failed absolute-sector transfer: that could
     replay a write against replacement media. No returned DPB is dereferenced. */
  intdos(&in, &out);
  return out.h.al == 0;
}

int m18_read_sector(unsigned drive, unsigned sector, void *buffer)
{
  return m18_abs_sector(0, drive, sector, buffer) == 0;
}

int m18_write_sector(unsigned drive, unsigned sector, void *buffer)
{
  return m18_abs_sector(1, drive, sector, buffer) == 0;
}

int m18_load_volume(unsigned drive, struct m18_volume *volume)
{
  unsigned i;
  if (!volume || drive > 1)
    return 0;
  m18_reset_disk();
  if (!m18_bind_volume(drive) ||
      !m18_read_sector(drive, 0, volume->boot) ||
      !m18_validate_bpb(volume->boot, sizeof(volume->boot), &volume->layout))
    return 0;

  for (i = 0; i < volume->layout.sectors_per_fat; ++i) {
    if (!m18_read_sector(drive, volume->layout.fat_start + i,
                         volume->fat + i * M18_SECTOR_BYTES) ||
        !m18_read_sector(drive, volume->layout.fat_start +
                         volume->layout.sectors_per_fat + i, mirror_buffer) ||
        memcmp(volume->fat + i * M18_SECTOR_BYTES, mirror_buffer,
               M18_SECTOR_BYTES))
      return 0;
  }
  if (volume->fat[0] != 0xfe || volume->fat[1] != 0xff ||
      volume->fat[2] != 0xff)
    return 0;

  for (i = 0; i < volume->layout.root_sectors; ++i)
    if (!m18_read_sector(drive, volume->layout.root_start + i,
                         volume->root + i * M18_SECTOR_BYTES))
      return 0;
  memset(volume->owned, 0, sizeof(volume->owned));
  return 1;
}

static unsigned m18_word(const unsigned char *p)
{
  return (unsigned)p[0] | ((unsigned)p[1] << 8);
}

static unsigned long m18_dword(const unsigned char *p)
{
  return (unsigned long)m18_word(p) | ((unsigned long)m18_word(p + 2) << 16);
}

static int m18_is_dot(const unsigned char *entry)
{
  unsigned n;
  if (entry[0] != '.')
    return 0;
  if (entry[1] == '.') {
    if (entry[2] != ' ')
      return 0;
    for (n = 2; n < 11; ++n)
      if (entry[n] != ' ')
        return 0;
    return 2;
  }
  for (n = 1; n < 11; ++n)
    if (entry[n] != ' ')
      return 0;
  return 1;
}

static int m18_mark_file(struct m18_volume *volume, unsigned first,
                         unsigned long size)
{
  unsigned expected, actual;
  enum m18_chain_error error;
  if (!size)
    return first == 0;
  if (size > (unsigned long)M18_DATA_CLUSTERS * M18_SECTOR_BYTES)
    return 0;
  expected = (unsigned)((size + M18_SECTOR_BYTES - 1U) / M18_SECTOR_BYTES);
  error = m18_validate_chain(volume->fat, sizeof(volume->fat),
                             volume->layout.data_clusters, first, expected,
                             volume->owned, sizeof(volume->owned), &actual);
  return error == M18_CHAIN_OK && actual == expected;
}

static int m18_mark_directory(struct m18_volume *volume, unsigned first,
                              unsigned *actual)
{
  return m18_validate_chain(volume->fat, sizeof(volume->fat),
                            volume->layout.data_clusters, first, 0,
                            volume->owned, sizeof(volume->owned), actual) ==
         M18_CHAIN_OK;
}

struct directory_node {
  unsigned cluster;
  unsigned parent;
};

static struct directory_node directory_queue[M18_DATA_CLUSTERS];

static int m18_process_entry(struct m18_volume *volume,
                             const unsigned char *entry, int is_root,
                             unsigned directory_cluster, unsigned parent,
                             struct m18_check_report *report,
                             unsigned *labels, unsigned *queue_count)
{
  unsigned attributes, first;
  unsigned long size;
  int dot;

  if (entry[0] == 0xe5 || entry[0] == 0)
    return 1;
  attributes = entry[11];
  if (attributes == 0x0f)
    return 1;
  if (attributes & 0xc0)
    return 0;
  dot = m18_is_dot(entry);
  first = m18_word(entry + 26);
  size = m18_dword(entry + 28);

  if (dot) {
    unsigned expected = dot == 1 ? directory_cluster : parent;
    if (is_root || !(attributes & 0x10) || (attributes & 0x08) ||
        size || first != expected)
      return 0;
    return 1;
  }
  if (attributes & 0x08) {
    if (!is_root || attributes != 0x08 || first || size || ++*labels > 1)
      return 0;
    return 1;
  }
  if (attributes & 0x10) {
    unsigned actual;
    if (size || *queue_count >= M18_DATA_CLUSTERS ||
        !m18_mark_directory(volume, first, &actual))
      return 0;
    directory_queue[*queue_count].cluster = first;
    directory_queue[*queue_count].parent = is_root ? 0 : directory_cluster;
    ++*queue_count;
    ++report->directories;
    return 1;
  }
  if (!m18_mark_file(volume, first, size))
    return 0;
  ++report->files;
  report->file_bytes += size;
  return 1;
}

static int m18_check_directory(unsigned drive, struct m18_volume *volume,
                               struct directory_node node,
                               struct m18_check_report *report,
                               unsigned *queue_count)
{
  unsigned current = node.cluster;
  unsigned label_count = 0;
  int ended = 0;
  int saw_dot = 0, saw_dotdot = 0;

  for (;;) {
    unsigned i, next;
    if (current < 2 || current >= M18_CLUSTER_LIMIT ||
        !m18_read_sector(drive,
             volume->layout.first_data_sector + current - 2,
             sector_buffer))
      return 0;
    for (i = 0; i < M18_SECTOR_BYTES; i += 32) {
      const unsigned char *entry = sector_buffer + i;
      int dot;
      if (!entry[0]) {
        ended = 1;
        break;
      }
      dot = m18_is_dot(entry);
      if (dot == 1) ++saw_dot;
      if (dot == 2) ++saw_dotdot;
      if (!m18_process_entry(volume, entry, 0, node.cluster,
                             node.parent, report, &label_count,
                             queue_count))
        return 0;
    }
    if (ended)
      break;
    if (!m18_fat12_get(volume->fat, sizeof(volume->fat), current, &next))
      return 0;
    if (next >= 0xff8 && next <= 0xfff)
      break;
    current = next;
  }
  return saw_dot == 1 && saw_dotdot == 1;
}

int m18_check_allocations(unsigned drive, struct m18_volume *volume,
                          struct m18_check_report *report)
{
  unsigned n, labels = 0, queue_count = 0, queue_index = 0;
  int ended = 0;
  if (!volume || !report || drive > 1)
    return 0;
  memset(report, 0, sizeof(*report));
  memset(volume->owned, 0, sizeof(volume->owned));
  for (n = 0; n < M18_ROOT_ENTRIES; ++n) {
    const unsigned char *entry = volume->root + n * 32U;
    if (ended)
      continue;
    if (!entry[0]) {
      ended = 1;
      continue;
    }
    if (entry[0] != 0xe5)
      ++report->root_entries_used;
    if (!m18_process_entry(volume, entry, 1, 0, 0, report,
                           &labels, &queue_count))
      return 0;
  }

  while (queue_index < queue_count) {
    if (!m18_check_directory(drive, volume,
                             directory_queue[queue_index], report,
                             &queue_count))
      return 0;
    ++queue_index;
  }

  for (n = 2; n < M18_CLUSTER_LIMIT; ++n) {
    unsigned value, byte = n >> 3;
    unsigned char bit = (unsigned char)(1U << (n & 7U));
    if (!m18_fat12_get(volume->fat, sizeof(volume->fat), n, &value))
      return 0;
    if (volume->owned[byte] & bit) {
      if (!value)
        return 0;
      ++report->allocated_clusters;
    } else if (!value) {
      ++report->free_clusters;
    } else if (value == 0xff7) {
      ++report->bad_clusters;
    } else {
      ++report->lost_clusters;
    }
  }
  return report->lost_clusters == 0;
}
