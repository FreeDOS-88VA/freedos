/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M20_MCB_PARSER_H
#define M20_MCB_PARSER_H

#define M20_MCB_NORMAL 0x4d
#define M20_MCB_LAST   0x5a
#define M20_MCB_SYSTEM_PSP 8
#define M20_MCB_HEADER_BYTES 16UL
#define M20_MCB_LIMIT_PARAGRAPHS 0x10000UL
#define M20_MCB_MAX_OWNERS 128

typedef unsigned char m20_u8;
typedef unsigned short m20_u16;
typedef unsigned long m20_u32;

typedef int (*m20_mcb_reader)(void *context, m20_u16 segment,
                              m20_u8 header[M20_MCB_HEADER_BYTES]);
typedef int (*m20_mcb_visitor)(void *context, m20_u16 segment,
                               m20_u8 type, m20_u16 owner,
                               m20_u16 paragraphs, const m20_u8 name[8]);

enum m20_mcb_status {
  M20_MCB_OK = 0,
  M20_MCB_BAD_FIRST,
  M20_MCB_READ_FAILED,
  M20_MCB_BAD_TYPE,
  M20_MCB_BAD_SIZE,
  M20_MCB_OUT_OF_RANGE,
  M20_MCB_NO_TERMINAL,
  M20_MCB_TOO_MANY_OWNERS,
  M20_MCB_OWNER_MISSING,
  M20_MCB_CURRENT_PSP_MISSING,
  M20_MCB_OWNER_MISMATCH,
  M20_MCB_PSP_BLOCK_TOO_SMALL,
  M20_MCB_VISITOR_FAILED
};

struct m20_mcb_summary {
  m20_u16 first_segment;
  m20_u16 terminal_segment;
  m20_u32 managed_bytes;
  m20_u32 free_payload_bytes;
  m20_u32 allocated_payload_bytes;
  m20_u32 system_payload_bytes;
  m20_u32 largest_free_bytes;
  m20_u32 own_payload_bytes;
  m20_u32 mcb_overhead_bytes;
  m20_u32 block_count;
};

/*
 * Walk the pinned FreeDOS VA MCB format using a caller-supplied bounded reader.
 * The chain is read once for arithmetic and totals, once to validate process
 * owners, and once more (only when visitor is non-NULL) to report entries.
 * Physical-map information is deliberately not inferred from the MCB chain.
 */
enum m20_mcb_status m20_mcb_walk(
    m20_u16 first_segment, m20_u16 current_psp,
    m20_mcb_reader reader, m20_mcb_visitor visitor, void *context,
    struct m20_mcb_summary *summary);

const char *m20_mcb_status_text(enum m20_mcb_status status);

#endif
