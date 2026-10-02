/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Read-only FreeDOS VA MCB map; stdout is DOS standard output. */
#include <dos.h>
#include <malloc.h>
#include <stdio.h>
#include <string.h>
#include "mcb_parser.h"

#define DOS_MAJOR 6
#define DOS_MINOR 22
#define DOS_OEM_ID 0xfd
#define DOS_REVISION 43

static unsigned current_psp;
static unsigned first_mcb;

static int read_mcb(void *context, m19_u16 segment,
                    m19_u8 header[M19_MCB_HEADER_BYTES])
{
  const unsigned char far *source;
  unsigned i;
  (void)context;
  source = (const unsigned char far *)MK_FP(segment, 0);
  for (i = 0; i < M19_MCB_HEADER_BYTES; ++i)
    header[i] = source[i];
  return 1;
}

static int query_version(void)
{
  union REGS inregs, outregs;
  struct SREGS segregs;

  memset(&inregs, 0, sizeof(inregs));
  memset(&segregs, 0, sizeof(segregs));
  inregs.h.ah = 0x30;
  intdosx(&inregs, &outregs, &segregs);
  return outregs.h.al == DOS_MAJOR && outregs.h.ah == DOS_MINOR &&
         outregs.h.bh == DOS_OEM_ID && outregs.h.bl == DOS_REVISION;
}

static int query_first_mcb(void)
{
  union REGS inregs, outregs;
  struct SREGS segregs;
  const unsigned far *first_word;

  memset(&inregs, 0, sizeof(inregs));
  memset(&segregs, 0, sizeof(segregs));
  inregs.h.ah = 0x52;
  intdosx(&inregs, &outregs, &segregs);
  if (segregs.es == 0 || outregs.x.bx < 2)
    return 0;
  first_word = (const unsigned far *)MK_FP(segregs.es, outregs.x.bx - 2);
  first_mcb = *first_word;

  memset(&inregs, 0, sizeof(inregs));
  memset(&segregs, 0, sizeof(segregs));
  inregs.h.ah = 0x62;
  intdosx(&inregs, &outregs, &segregs);
  current_psp = outregs.x.bx;
  return first_mcb >= 0x1000U && current_psp != 0 &&
         current_psp != M19_MCB_SYSTEM_PSP;
}

static void clean_name(const m19_u8 input[8], char output[9])
{
  unsigned i, length = 8;
  for (i = 0; i < 8; ++i) {
    unsigned char c = input[i];
    output[i] = c >= 0x20 && c <= 0x7e ? (char)c : '?';
  }
  while (length != 0 && (output[length - 1] == ' ' || output[length - 1] == 0))
    --length;
  if (length == 0) {
    output[0] = '-';
    length = 1;
  }
  output[length] = 0;
}

static int print_entry(void *context, m19_u16 segment, m19_u8 type,
                       m19_u16 owner, m19_u16 paragraphs,
                       const m19_u8 name[8])
{
  char label[9];
  unsigned long start, end;
  const char *classification;
  (void)context;

  clean_name(name, label);
  start = ((unsigned long)segment + 1UL) * 16UL;
  end = start + (unsigned long)paragraphs * 16UL;
  if (owner == 0)
    classification = "FREE";
  else if (owner == M19_MCB_SYSTEM_PSP)
    classification = "SYSTEM";
  else
    classification = "PSP";

  printf("MCB %04X %c owner=%04X %-6s name=%-8s payload=%05lX-%05lX bytes=%lu paras=%u\n",
         segment, type, owner, classification, label, start, end,
         (unsigned long)paragraphs * 16UL, paragraphs);
  return 0;
}

static void print_summary(const struct m19_mcb_summary *s)
{
  unsigned long start, end;
  start = (unsigned long)s->first_segment * 16UL;
  end = start + s->managed_bytes;
  printf("Managed MCB range: %05lX-%05lX bytes (end exclusive)\n",
         start, end);
  printf("Blocks: %lu; managed bytes: %lu; MCB overhead: %lu\n",
         s->block_count, s->managed_bytes, s->mcb_overhead_bytes);
  printf("Free payload: %lu bytes; largest free block: %lu bytes\n",
         s->free_payload_bytes, s->largest_free_bytes);
  printf("Allocated payload: %lu bytes; system-owned: %lu bytes\n",
         s->allocated_payload_bytes, s->system_payload_bytes);
  printf("MEMMAP-owned payload (PSP %04X, including owned environment): %lu bytes\n",
         current_psp, s->own_payload_bytes);
  puts("Physical/reserved map: unavailable (DOS MCB chain only)");
}

static int print_check_summary(const struct m19_mcb_summary *s)
{
  printf("MCB chain: VALID (%lu blocks; %lu free; largest %lu bytes)\n",
         s->block_count, s->free_payload_bytes, s->largest_free_bytes);
  printf("MEMMAP-owned payload: %lu bytes\n", s->own_payload_bytes);
  puts("Physical/reserved map: unavailable (DOS MCB chain only)");
  return 0;
}

static void usage(void)
{
  puts("MEMMAP - FreeDOS PC-88VA conventional-memory map");
  puts("Usage: MEMMAP [/? | /CHECK]");
  puts("MEMMAP lists checked MCBs; /CHECK validates the MCB chain only.");
  puts("Output uses DOS standard output and may be redirected.");
}

int main(int argc, char **argv)
{
  struct m19_mcb_summary summary;
  enum m19_mcb_status status;
  int check_only = 0;

  if (argc > 2) {
    usage();
    return 2;
  }
  if (argc == 2) {
    if (strcmp(argv[1], "/?") == 0 || strcmp(argv[1], "-?") == 0) {
      usage();
      return 0;
    }
    if (strcmp(argv[1], "/CHECK") == 0 || strcmp(argv[1], "/check") == 0) {
      check_only = 1;
    } else {
      usage();
      return 2;
    }
  }

  /* Validate the pinned DOS interface before output or MCB traversal. The
     MZ header bounds the process allocation before DOS executes this program. */
  if (!query_version()) {
    fputs("MEMMAP: unsupported DOS layout; requires FreeDOS VA 6.22, OEM FD, revision 43.\n",
          stderr);
    return 3;
  }
  if (!query_first_mcb()) {
    fputs("MEMMAP: AH=52h/AH=62h returned an unsupported layout.\n", stderr);
    return 3;
  }
  /* Prime standard output before validation so any library-owned output
     buffer is included in the observed process state. */
  if (check_only)
    fputs("MEMMAP /CHECK: ", stdout);
  else
    fputs("MEMMAP: validating DOS MCB chain\n", stdout);
  fflush(stdout);
  /* OW 1.9 startup can expand DGROUP and create library heap blocks even
     with a bounded MZ maxalloc. Use its ownership-aware APIs to return only
     unused heap tails, retaining the active stack, stdio buffer and all live
     allocations. Never resize to a guessed linked-image minimum. */
  if (_nheapshrink() != 0 || _fheapshrink() != 0) {
    fputs("MEMMAP: unable to trim unused runtime heap safely.\n", stderr);
    return 3;
  }

  status = m19_mcb_walk((m19_u16)first_mcb, (m19_u16)current_psp,
                        read_mcb, check_only ? 0 : print_entry,
                        NULL, &summary);
  if (status != M19_MCB_OK) {
    fprintf(stderr, "MEMMAP: invalid chain: %s.\n", m19_mcb_status_text(status));
    return 1;
  }
  if (check_only)
    return print_check_summary(&summary);
  print_summary(&summary);
  puts("MCB chain: VALID");
  return 0;
}
