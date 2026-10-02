/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M19_MCB_PARSER_H
#define M19_MCB_PARSER_H

#define M19_MCB_NORMAL 0x4d
#define M19_MCB_LAST   0x5a
#define M19_MCB_SYSTEM_PSP 8
#define M19_MCB_HEADER_BYTES 16UL
#define M19_MCB_LIMIT_PARAGRAPHS 0x10000UL
#define M19_MCB_MAX_OWNERS 128

typedef unsigned char m19_u8;
typedef unsigned short m19_u16;
typedef unsigned long m19_u32;

typedef int (*m19_mcb_reader)(void *context, m19_u16 segment,
                              m19_u8 header[M19_MCB_HEADER_BYTES]);
typedef int (*m19_mcb_visitor)(void *context, m19_u16 segment,
                               m19_u8 type, m19_u16 owner,
                               m19_u16 paragraphs, const m19_u8 name[8]);

enum m19_mcb_status {
  M19_MCB_OK = 0,
  M19_MCB_BAD_FIRST,
  M19_MCB_READ_FAILED,
  M19_MCB_BAD_TYPE,
  M19_MCB_BAD_SIZE,
  M19_MCB_OUT_OF_RANGE,
  M19_MCB_NO_TERMINAL,
  M19_MCB_TOO_MANY_OWNERS,
  M19_MCB_OWNER_MISSING,
  M19_MCB_CURRENT_PSP_MISSING,
  M19_MCB_OWNER_MISMATCH,
  M19_MCB_PSP_BLOCK_TOO_SMALL,
  M19_MCB_VISITOR_FAILED
};

struct m19_mcb_summary {
  m19_u16 first_segment;
  m19_u16 terminal_segment;
  m19_u32 managed_bytes;
  m19_u32 free_payload_bytes;
  m19_u32 allocated_payload_bytes;
  m19_u32 system_payload_bytes;
  m19_u32 largest_free_bytes;
  m19_u32 own_payload_bytes;
  m19_u32 mcb_overhead_bytes;
  m19_u32 block_count;
};

/*
 * Walk the pinned FreeDOS VA MCB format using a caller-supplied bounded reader.
 * The chain is read once for arithmetic and totals, once to validate process
 * owners, and once more (only when visitor is non-NULL) to report entries.
 * Physical-map information is deliberately not inferred from the MCB chain.
 */
enum m19_mcb_status m19_mcb_walk(
    m19_u16 first_segment, m19_u16 current_psp,
    m19_mcb_reader reader, m19_mcb_visitor visitor, void *context,
    struct m19_mcb_summary *summary);

const char *m19_mcb_status_text(enum m19_mcb_status status);

#endif
