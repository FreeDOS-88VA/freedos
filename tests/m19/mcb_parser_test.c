/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <stdio.h>
#include <string.h>
#include "../../tools/m19/memmap/mcb_parser.h"

#define IMAGE_BYTES 0x100000UL

static m19_u8 image[IMAGE_BYTES];
static m19_u32 extent = IMAGE_BYTES;
static unsigned visited;

static int read_header(void *context, m19_u16 segment,
                       m19_u8 header[M19_MCB_HEADER_BYTES])
{
  m19_u32 address = (m19_u32)segment * 16UL;
  (void)context;
  if (address + M19_MCB_HEADER_BYTES > extent ||
      address + M19_MCB_HEADER_BYTES > IMAGE_BYTES)
    return 0;
  memcpy(header, image + address, M19_MCB_HEADER_BYTES);
  return 1;
}

static void put_mcb(m19_u16 segment, m19_u8 type, m19_u16 owner,
                    m19_u16 paragraphs, const char *name)
{
  m19_u8 *header = image + (m19_u32)segment * 16UL;
  memset(header, 0, M19_MCB_HEADER_BYTES);
  header[0] = type;
  header[1] = (m19_u8)(owner & 0xffU);
  header[2] = (m19_u8)(owner >> 8);
  header[3] = (m19_u8)(paragraphs & 0xffU);
  header[4] = (m19_u8)(paragraphs >> 8);
  if (name != NULL)
    strncpy((char *)header + 8, name, 8);
}

static int count_entry(void *context, m19_u16 segment, m19_u8 type,
                       m19_u16 owner, m19_u16 paragraphs,
                       const m19_u8 name[8])
{
  (void)context;
  (void)segment;
  (void)type;
  (void)owner;
  (void)paragraphs;
  (void)name;
  ++visited;
  return 0;
}

static int check(int condition, const char *message)
{
  if (!condition) {
    fprintf(stderr, "FAIL: %s\n", message);
    return 0;
  }
  return 1;
}

static void blank(void)
{
  memset(image, 0, sizeof(image));
  extent = IMAGE_BYTES;
  visited = 0;
}

static int valid_chain(void)
{
  struct m19_mcb_summary s;
  enum m19_mcb_status rc;
  blank();
  put_mcb(0x1000, M19_MCB_NORMAL, 8, 0x10, "KERNEL");
  put_mcb(0x1011, M19_MCB_NORMAL, 0x1012, 0x10, "MEMMAP");
  put_mcb(0x1022, M19_MCB_NORMAL, 0x1012, 2, "ENV");
  put_mcb(0x1025, M19_MCB_LAST, 0, 0x20, "");
  rc = m19_mcb_walk(0x1000, 0x1012, read_header, count_entry,
                    NULL, &s);
  return check(rc == M19_MCB_OK, "valid owner-linked chain accepted") &&
         check(s.block_count == 4, "all MCBs counted") &&
         check(s.terminal_segment == 0x1025, "terminal segment recorded") &&
         check(s.managed_bytes == 0x460UL, "managed bytes include headers") &&
         check(s.free_payload_bytes == 0x200UL, "free payload total") &&
         check(s.allocated_payload_bytes == 0x220UL, "allocated payload total") &&
         check(s.system_payload_bytes == 0x100UL, "system-owned payload total") &&
         check(s.largest_free_bytes == 0x200UL, "largest free block") &&
         check(s.own_payload_bytes == 0x120UL, "observer-owned blocks include environment") &&
         check(s.mcb_overhead_bytes == 0x40UL, "MCB headers counted") &&
         check(s.free_payload_bytes + s.allocated_payload_bytes +
               s.mcb_overhead_bytes == s.managed_bytes, "accounting closes") &&
         check(visited == 4, "visitor sees the complete valid chain");
}

static int zero_sized_blocks(void)
{
  struct m19_mcb_summary s;
  enum m19_mcb_status rc;
  blank();
  put_mcb(0x1000, M19_MCB_NORMAL, 8, 0, "EMPTY");
  put_mcb(0x1001, M19_MCB_LAST, 0, 0, "");
  rc = m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s);
  return check(rc == M19_MCB_OK, "zero-size MCB payloads are accepted") &&
         check(s.block_count == 2 && s.managed_bytes == 32UL,
               "zero-size MCB headers remain accounted") &&
         check(s.free_payload_bytes == 0 && s.allocated_payload_bytes == 0,
               "zero-size blocks add no payload");
}

static int rejects_bad_type(void)
{
  struct m19_mcb_summary s;
  blank();
  put_mcb(0x1000, 'X', 0, 0, "BAD");
  return check(m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s) ==
               M19_MCB_BAD_TYPE, "bad type rejected");
}

static int rejects_size_sentinel(void)
{
  struct m19_mcb_summary s;
  blank();
  put_mcb(0x1000, M19_MCB_NORMAL, 0, 0xffffU, "WRAP");
  return check(m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s) ==
               M19_MCB_BAD_SIZE, "kernel-invalid FFFFh paragraph count rejected");
}

static int rejects_cycle_wrap(void)
{
  struct m19_mcb_summary s;
  blank();
  put_mcb(0x1000, M19_MCB_NORMAL, 0, 0xefffU, "WRAP");
  return check(m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s) ==
               M19_MCB_OUT_OF_RANGE, "paragraph wrap cannot form a cycle");
}

static int rejects_truncated_header(void)
{
  struct m19_mcb_summary s;
  blank();
  extent = 0x1000UL * 16UL + 15UL;
  return check(m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s) ==
               M19_MCB_READ_FAILED, "truncated header rejected before decode");
}

static int rejects_unterminated_chain(void)
{
  struct m19_mcb_summary s;
  blank();
  put_mcb(0x1000, M19_MCB_NORMAL, 8, 1, "NOEND");
  put_mcb(0x1002, 0, 0, 0, "");
  return check(m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s) ==
               M19_MCB_BAD_TYPE, "missing terminal marker rejected");
}

static int rejects_missing_psp(void)
{
  struct m19_mcb_summary s;
  blank();
  put_mcb(0x1000, M19_MCB_NORMAL, 0x2000, 1, "ORPHAN");
  put_mcb(0x1002, M19_MCB_LAST, 0, 0, "");
  return check(m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s) ==
               M19_MCB_OWNER_MISSING, "orphan process owner rejected");
}

static int rejects_missing_current_psp(void)
{
  struct m19_mcb_summary s;
  blank();
  put_mcb(0x1000, M19_MCB_NORMAL, 0x1012, 0x10, "OWNER");
  put_mcb(0x1011, M19_MCB_NORMAL, 0x1012, 0x10, "MEMMAP");
  put_mcb(0x1022, M19_MCB_LAST, 0, 0, "");
  return check(m19_mcb_walk(0x1000, 0x1033, read_header, NULL, NULL, &s) ==
               M19_MCB_CURRENT_PSP_MISSING,
               "current PSP must own an MCB block in the chain");
}

static int rejects_wrong_psp_owner(void)
{
  struct m19_mcb_summary s;
  blank();
  put_mcb(0x1000, M19_MCB_NORMAL, 0x1012, 0x10, "OWNER");
  put_mcb(0x1011, M19_MCB_NORMAL, 8, 0x10, "NOTPSP");
  put_mcb(0x1022, M19_MCB_LAST, 0, 0, "");
  return check(m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s) ==
               M19_MCB_OWNER_MISMATCH, "PSP MCB owner mismatch rejected");
}

static int rejects_short_psp(void)
{
  struct m19_mcb_summary s;
  blank();
  put_mcb(0x1000, M19_MCB_NORMAL, 0x1001, 15, "SHORT");
  put_mcb(0x1010, M19_MCB_LAST, 0, 0, "");
  return check(m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s) ==
               M19_MCB_PSP_BLOCK_TOO_SMALL, "short PSP allocation rejected");
}

static int rejects_owner_limit(void)
{
  struct m19_mcb_summary s;
  unsigned i;
  blank();
  for (i = 0; i < M19_MCB_MAX_OWNERS + 1; ++i)
    put_mcb((m19_u16)(0x1000U + i), M19_MCB_NORMAL,
            (m19_u16)(0x2000U + i), 0, "OWNER");
  put_mcb((m19_u16)(0x1000U + M19_MCB_MAX_OWNERS + 1U),
          M19_MCB_LAST, 0, 0, "");
  return check(m19_mcb_walk(0x1000, 0, read_header, NULL, NULL, &s) ==
               M19_MCB_TOO_MANY_OWNERS, "distinct-owner traversal is bounded");
}

int main(void)
{
  if (!valid_chain() || !zero_sized_blocks() || !rejects_bad_type() ||
      !rejects_size_sentinel() || !rejects_cycle_wrap() ||
      !rejects_truncated_header() || !rejects_unterminated_chain() ||
      !rejects_missing_psp() || !rejects_missing_current_psp() ||
      !rejects_wrong_psp_owner() || !rejects_short_psp() ||
      !rejects_owner_limit())
    return 1;
  puts("M19 MCB parser tests passed");
  return 0;
}
