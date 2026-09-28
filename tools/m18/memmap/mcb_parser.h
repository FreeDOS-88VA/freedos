/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M18_MCB_PARSER_H
#define M18_MCB_PARSER_H

#define M18_MCB_NORMAL 0x4d
#define M18_MCB_LAST   0x5a
#define M18_MCB_SYSTEM_PSP 8
#define M18_MCB_HEADER_BYTES 16UL
#define M18_MCB_LIMIT_PARAGRAPHS 0x10000UL
#define M18_MCB_MAX_OWNERS 128

typedef unsigned char m18_u8;
typedef unsigned short m18_u16;
typedef unsigned long m18_u32;

typedef int (*m18_mcb_reader)(void *context, m18_u16 segment,
                              m18_u8 header[M18_MCB_HEADER_BYTES]);
typedef int (*m18_mcb_visitor)(void *context, m18_u16 segment,
                               m18_u8 type, m18_u16 owner,
                               m18_u16 paragraphs, const m18_u8 name[8]);

enum m18_mcb_status {
  M18_MCB_OK = 0,
  M18_MCB_BAD_FIRST,
  M18_MCB_READ_FAILED,
  M18_MCB_BAD_TYPE,
  M18_MCB_BAD_SIZE,
  M18_MCB_OUT_OF_RANGE,
  M18_MCB_NO_TERMINAL,
  M18_MCB_TOO_MANY_OWNERS,
  M18_MCB_OWNER_MISSING,
  M18_MCB_CURRENT_PSP_MISSING,
  M18_MCB_OWNER_MISMATCH,
  M18_MCB_PSP_BLOCK_TOO_SMALL,
  M18_MCB_VISITOR_FAILED
};

struct m18_mcb_summary {
  m18_u16 first_segment;
  m18_u16 terminal_segment;
  m18_u32 managed_bytes;
  m18_u32 free_payload_bytes;
  m18_u32 allocated_payload_bytes;
  m18_u32 system_payload_bytes;
  m18_u32 largest_free_bytes;
  m18_u32 own_payload_bytes;
  m18_u32 mcb_overhead_bytes;
  m18_u32 block_count;
};

/*
 * Walk the pinned FreeDOS VA MCB format using a caller-supplied bounded reader.
 * The chain is read once for arithmetic and totals, once to validate process
 * owners, and once more (only when visitor is non-NULL) to report entries.
 * Physical-map information is deliberately not inferred from the MCB chain.
 */
enum m18_mcb_status m18_mcb_walk(
    m18_u16 first_segment, m18_u16 current_psp,
    m18_mcb_reader reader, m18_mcb_visitor visitor, void *context,
    struct m18_mcb_summary *summary);

const char *m18_mcb_status_text(enum m18_mcb_status status);

#endif
