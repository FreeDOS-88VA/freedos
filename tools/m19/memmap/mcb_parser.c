/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "mcb_parser.h"

struct owner_link {
  m19_u16 segment;
  m19_u8 found;
};

static m19_u16 read_u16(const m19_u8 *p)
{
  return (m19_u16)((m19_u16)p[0] | ((m19_u16)p[1] << 8));
}

static enum m19_mcb_status read_entry(
    m19_mcb_reader reader, void *context, m19_u16 segment,
    m19_u8 header[M19_MCB_HEADER_BYTES], m19_u16 *owner,
    m19_u16 *paragraphs, m19_u32 *next)
{
  m19_u32 end;

  if (!reader(context, segment, header))
    return M19_MCB_READ_FAILED;
  if (header[0] != M19_MCB_NORMAL && header[0] != M19_MCB_LAST)
    return M19_MCB_BAD_TYPE;

  *owner = read_u16(header + 1);
  *paragraphs = read_u16(header + 3);
  if (*paragraphs == 0xffffU)
    return M19_MCB_BAD_SIZE;

  end = (m19_u32)segment + 1UL + (m19_u32)*paragraphs;
  if (end <= (m19_u32)segment || end > M19_MCB_LIMIT_PARAGRAPHS)
    return M19_MCB_OUT_OF_RANGE;
  if (header[0] == M19_MCB_NORMAL && end >= M19_MCB_LIMIT_PARAGRAPHS)
    return M19_MCB_OUT_OF_RANGE;
  *next = end;
  return M19_MCB_OK;
}

static enum m19_mcb_status collect_owners(
    m19_u16 first, m19_mcb_reader reader, void *context,
    struct owner_link owners[M19_MCB_MAX_OWNERS], m19_u16 *owner_count)
{
  m19_u32 segment = first;
  m19_u32 count = 0;
  m19_u16 nowners = 0;

  for (;;) {
    m19_u8 header[M19_MCB_HEADER_BYTES];
    m19_u16 owner, paragraphs, i;
    m19_u32 next;
    enum m19_mcb_status status = read_entry(
        reader, context, (m19_u16)segment, header, &owner, &paragraphs, &next);
    if (status != M19_MCB_OK)
      return status;
    if (owner != 0 && owner != M19_MCB_SYSTEM_PSP) {
      for (i = 0; i < nowners && owners[i].segment != owner; ++i)
        ;
      if (i == nowners) {
        if (nowners >= M19_MCB_MAX_OWNERS)
          return M19_MCB_TOO_MANY_OWNERS;
        owners[nowners].segment = owner;
        owners[nowners].found = 0;
        ++nowners;
      }
    }
    ++count;
    if (count > M19_MCB_LIMIT_PARAGRAPHS)
      return M19_MCB_OUT_OF_RANGE;
    if (header[0] == M19_MCB_LAST)
      break;
    segment = next;
  }
  *owner_count = nowners;
  return M19_MCB_OK;
}

static enum m19_mcb_status validate_owners(
    m19_u16 first, m19_mcb_reader reader, void *context,
    struct owner_link owners[M19_MCB_MAX_OWNERS], m19_u16 owner_count)
{
  m19_u32 segment = first;
  m19_u32 count = 0;

  for (;;) {
    m19_u8 header[M19_MCB_HEADER_BYTES];
    m19_u16 owner, paragraphs, i;
    m19_u32 next;
    enum m19_mcb_status status = read_entry(
        reader, context, (m19_u16)segment, header, &owner, &paragraphs, &next);
    if (status != M19_MCB_OK)
      return status;

    for (i = 0; i < owner_count; ++i) {
      if (segment + 1UL == (m19_u32)owners[i].segment) {
        if (owner != owners[i].segment)
          return M19_MCB_OWNER_MISMATCH;
        if (paragraphs < 16U)
          return M19_MCB_PSP_BLOCK_TOO_SMALL;
        owners[i].found = 1;
      }
    }

    ++count;
    if (count > M19_MCB_LIMIT_PARAGRAPHS)
      return M19_MCB_OUT_OF_RANGE;
    if (header[0] == M19_MCB_LAST)
      break;
    segment = next;
  }

  for (count = 0; count < (m19_u32)owner_count; ++count)
    if (!owners[count].found)
      return M19_MCB_OWNER_MISSING;
  return M19_MCB_OK;
}

enum m19_mcb_status m19_mcb_walk(
    m19_u16 first_segment, m19_u16 current_psp,
    m19_mcb_reader reader, m19_mcb_visitor visitor, void *context,
    struct m19_mcb_summary *summary)
{
  struct owner_link owners[M19_MCB_MAX_OWNERS];
  struct m19_mcb_summary result;
  m19_u16 owner_count = 0;
  m19_u32 segment, blocks = 0;
  enum m19_mcb_status status;

  if (reader == 0 || summary == 0 || first_segment < 0x1000U)
    return M19_MCB_BAD_FIRST;

  result.first_segment = first_segment;
  result.terminal_segment = 0;
  result.managed_bytes = 0;
  result.free_payload_bytes = 0;
  result.allocated_payload_bytes = 0;
  result.system_payload_bytes = 0;
  result.largest_free_bytes = 0;
  result.own_payload_bytes = 0;
  result.mcb_overhead_bytes = 0;
  result.block_count = 0;

  segment = first_segment;
  for (;;) {
    m19_u8 header[M19_MCB_HEADER_BYTES];
    m19_u16 owner, paragraphs;
    m19_u32 next, payload_bytes;

    status = read_entry(reader, context, (m19_u16)segment,
                        header, &owner, &paragraphs, &next);
    if (status != M19_MCB_OK)
      return status;

    payload_bytes = (m19_u32)paragraphs * 16UL;
    result.mcb_overhead_bytes += M19_MCB_HEADER_BYTES;
    if (owner == 0) {
      result.free_payload_bytes += payload_bytes;
      if (payload_bytes > result.largest_free_bytes)
        result.largest_free_bytes = payload_bytes;
    } else {
      result.allocated_payload_bytes += payload_bytes;
      if (owner == M19_MCB_SYSTEM_PSP)
        result.system_payload_bytes += payload_bytes;
      if (current_psp != 0 && owner == current_psp)
        result.own_payload_bytes += payload_bytes;
    }

    ++blocks;
    if (blocks > M19_MCB_LIMIT_PARAGRAPHS)
      return M19_MCB_OUT_OF_RANGE;
    if (header[0] == M19_MCB_LAST) {
      result.terminal_segment = (m19_u16)segment;
      result.managed_bytes = (next - (m19_u32)first_segment) * 16UL;
      break;
    }
    segment = next;
  }
  result.block_count = blocks;

  if (result.free_payload_bytes + result.allocated_payload_bytes +
      result.mcb_overhead_bytes != result.managed_bytes)
    return M19_MCB_OUT_OF_RANGE;

  status = collect_owners(first_segment, reader, context, owners, &owner_count);
  if (status != M19_MCB_OK)
    return status;
  if (current_psp != 0 && current_psp != M19_MCB_SYSTEM_PSP) {
    m19_u16 i;
    for (i = 0; i < owner_count && owners[i].segment != current_psp; ++i)
      ;
    if (i == owner_count)
      return M19_MCB_CURRENT_PSP_MISSING;
  }
  status = validate_owners(first_segment, reader, context, owners, owner_count);
  if (status != M19_MCB_OK)
    return status;

  if (visitor != 0) {
    segment = first_segment;
    for (;;) {
      m19_u8 header[M19_MCB_HEADER_BYTES];
      m19_u16 owner, paragraphs;
      m19_u32 next;
      status = read_entry(reader, context, (m19_u16)segment,
                          header, &owner, &paragraphs, &next);
      if (status != M19_MCB_OK)
        return status;
      if (visitor(context, (m19_u16)segment, header[0], owner,
                  paragraphs, header + 8) != 0)
        return M19_MCB_VISITOR_FAILED;
      if (header[0] == M19_MCB_LAST)
        break;
      segment = next;
    }
  }

  *summary = result;
  return M19_MCB_OK;
}

const char *m19_mcb_status_text(enum m19_mcb_status status)
{
  switch (status) {
    case M19_MCB_OK: return "valid";
    case M19_MCB_BAD_FIRST: return "unsupported or missing first MCB";
    case M19_MCB_READ_FAILED: return "truncated or unreadable MCB header";
    case M19_MCB_BAD_TYPE: return "invalid MCB type";
    case M19_MCB_BAD_SIZE: return "invalid MCB paragraph count";
    case M19_MCB_OUT_OF_RANGE: return "MCB arithmetic exceeds real-mode bounds";
    case M19_MCB_NO_TERMINAL: return "missing terminal MCB";
    case M19_MCB_TOO_MANY_OWNERS: return "owner count exceeds the bounded checker";
    case M19_MCB_OWNER_MISSING: return "allocated block has no matching PSP block";
    case M19_MCB_CURRENT_PSP_MISSING: return "current PSP has no owned MCB block";
    case M19_MCB_OWNER_MISMATCH: return "PSP block owner does not match its segment";
    case M19_MCB_PSP_BLOCK_TOO_SMALL: return "PSP block is smaller than 256 bytes";
    case M19_MCB_VISITOR_FAILED: return "unable to report MCB entry";
    default: return "unknown MCB validation error";
  }
}
