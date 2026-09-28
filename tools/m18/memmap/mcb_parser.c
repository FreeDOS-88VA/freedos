/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "mcb_parser.h"

struct owner_link {
  m18_u16 segment;
  m18_u8 found;
};

static m18_u16 read_u16(const m18_u8 *p)
{
  return (m18_u16)((m18_u16)p[0] | ((m18_u16)p[1] << 8));
}

static enum m18_mcb_status read_entry(
    m18_mcb_reader reader, void *context, m18_u16 segment,
    m18_u8 header[M18_MCB_HEADER_BYTES], m18_u16 *owner,
    m18_u16 *paragraphs, m18_u32 *next)
{
  m18_u32 end;

  if (!reader(context, segment, header))
    return M18_MCB_READ_FAILED;
  if (header[0] != M18_MCB_NORMAL && header[0] != M18_MCB_LAST)
    return M18_MCB_BAD_TYPE;

  *owner = read_u16(header + 1);
  *paragraphs = read_u16(header + 3);
  if (*paragraphs == 0xffffU)
    return M18_MCB_BAD_SIZE;

  end = (m18_u32)segment + 1UL + (m18_u32)*paragraphs;
  if (end <= (m18_u32)segment || end > M18_MCB_LIMIT_PARAGRAPHS)
    return M18_MCB_OUT_OF_RANGE;
  if (header[0] == M18_MCB_NORMAL && end >= M18_MCB_LIMIT_PARAGRAPHS)
    return M18_MCB_OUT_OF_RANGE;
  *next = end;
  return M18_MCB_OK;
}

static enum m18_mcb_status collect_owners(
    m18_u16 first, m18_mcb_reader reader, void *context,
    struct owner_link owners[M18_MCB_MAX_OWNERS], m18_u16 *owner_count)
{
  m18_u32 segment = first;
  m18_u32 count = 0;
  m18_u16 nowners = 0;

  for (;;) {
    m18_u8 header[M18_MCB_HEADER_BYTES];
    m18_u16 owner, paragraphs, i;
    m18_u32 next;
    enum m18_mcb_status status = read_entry(
        reader, context, (m18_u16)segment, header, &owner, &paragraphs, &next);
    if (status != M18_MCB_OK)
      return status;
    if (owner != 0 && owner != M18_MCB_SYSTEM_PSP) {
      for (i = 0; i < nowners && owners[i].segment != owner; ++i)
        ;
      if (i == nowners) {
        if (nowners >= M18_MCB_MAX_OWNERS)
          return M18_MCB_TOO_MANY_OWNERS;
        owners[nowners].segment = owner;
        owners[nowners].found = 0;
        ++nowners;
      }
    }
    ++count;
    if (count > M18_MCB_LIMIT_PARAGRAPHS)
      return M18_MCB_OUT_OF_RANGE;
    if (header[0] == M18_MCB_LAST)
      break;
    segment = next;
  }
  *owner_count = nowners;
  return M18_MCB_OK;
}

static enum m18_mcb_status validate_owners(
    m18_u16 first, m18_mcb_reader reader, void *context,
    struct owner_link owners[M18_MCB_MAX_OWNERS], m18_u16 owner_count)
{
  m18_u32 segment = first;
  m18_u32 count = 0;

  for (;;) {
    m18_u8 header[M18_MCB_HEADER_BYTES];
    m18_u16 owner, paragraphs, i;
    m18_u32 next;
    enum m18_mcb_status status = read_entry(
        reader, context, (m18_u16)segment, header, &owner, &paragraphs, &next);
    if (status != M18_MCB_OK)
      return status;

    for (i = 0; i < owner_count; ++i) {
      if (segment + 1UL == (m18_u32)owners[i].segment) {
        if (owner != owners[i].segment)
          return M18_MCB_OWNER_MISMATCH;
        if (paragraphs < 16U)
          return M18_MCB_PSP_BLOCK_TOO_SMALL;
        owners[i].found = 1;
      }
    }

    ++count;
    if (count > M18_MCB_LIMIT_PARAGRAPHS)
      return M18_MCB_OUT_OF_RANGE;
    if (header[0] == M18_MCB_LAST)
      break;
    segment = next;
  }

  for (count = 0; count < (m18_u32)owner_count; ++count)
    if (!owners[count].found)
      return M18_MCB_OWNER_MISSING;
  return M18_MCB_OK;
}

enum m18_mcb_status m18_mcb_walk(
    m18_u16 first_segment, m18_u16 current_psp,
    m18_mcb_reader reader, m18_mcb_visitor visitor, void *context,
    struct m18_mcb_summary *summary)
{
  struct owner_link owners[M18_MCB_MAX_OWNERS];
  struct m18_mcb_summary result;
  m18_u16 owner_count = 0;
  m18_u32 segment, blocks = 0;
  enum m18_mcb_status status;

  if (reader == 0 || summary == 0 || first_segment < 0x1000U)
    return M18_MCB_BAD_FIRST;

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
    m18_u8 header[M18_MCB_HEADER_BYTES];
    m18_u16 owner, paragraphs;
    m18_u32 next, payload_bytes;

    status = read_entry(reader, context, (m18_u16)segment,
                        header, &owner, &paragraphs, &next);
    if (status != M18_MCB_OK)
      return status;

    payload_bytes = (m18_u32)paragraphs * 16UL;
    result.mcb_overhead_bytes += M18_MCB_HEADER_BYTES;
    if (owner == 0) {
      result.free_payload_bytes += payload_bytes;
      if (payload_bytes > result.largest_free_bytes)
        result.largest_free_bytes = payload_bytes;
    } else {
      result.allocated_payload_bytes += payload_bytes;
      if (owner == M18_MCB_SYSTEM_PSP)
        result.system_payload_bytes += payload_bytes;
      if (current_psp != 0 && owner == current_psp)
        result.own_payload_bytes += payload_bytes;
    }

    ++blocks;
    if (blocks > M18_MCB_LIMIT_PARAGRAPHS)
      return M18_MCB_OUT_OF_RANGE;
    if (header[0] == M18_MCB_LAST) {
      result.terminal_segment = (m18_u16)segment;
      result.managed_bytes = (next - (m18_u32)first_segment) * 16UL;
      break;
    }
    segment = next;
  }
  result.block_count = blocks;

  if (result.free_payload_bytes + result.allocated_payload_bytes +
      result.mcb_overhead_bytes != result.managed_bytes)
    return M18_MCB_OUT_OF_RANGE;

  status = collect_owners(first_segment, reader, context, owners, &owner_count);
  if (status != M18_MCB_OK)
    return status;
  if (current_psp != 0 && current_psp != M18_MCB_SYSTEM_PSP) {
    m18_u16 i;
    for (i = 0; i < owner_count && owners[i].segment != current_psp; ++i)
      ;
    if (i == owner_count)
      return M18_MCB_CURRENT_PSP_MISSING;
  }
  status = validate_owners(first_segment, reader, context, owners, owner_count);
  if (status != M18_MCB_OK)
    return status;

  if (visitor != 0) {
    segment = first_segment;
    for (;;) {
      m18_u8 header[M18_MCB_HEADER_BYTES];
      m18_u16 owner, paragraphs;
      m18_u32 next;
      status = read_entry(reader, context, (m18_u16)segment,
                          header, &owner, &paragraphs, &next);
      if (status != M18_MCB_OK)
        return status;
      if (visitor(context, (m18_u16)segment, header[0], owner,
                  paragraphs, header + 8) != 0)
        return M18_MCB_VISITOR_FAILED;
      if (header[0] == M18_MCB_LAST)
        break;
      segment = next;
    }
  }

  *summary = result;
  return M18_MCB_OK;
}

const char *m18_mcb_status_text(enum m18_mcb_status status)
{
  switch (status) {
    case M18_MCB_OK: return "valid";
    case M18_MCB_BAD_FIRST: return "unsupported or missing first MCB";
    case M18_MCB_READ_FAILED: return "truncated or unreadable MCB header";
    case M18_MCB_BAD_TYPE: return "invalid MCB type";
    case M18_MCB_BAD_SIZE: return "invalid MCB paragraph count";
    case M18_MCB_OUT_OF_RANGE: return "MCB arithmetic exceeds real-mode bounds";
    case M18_MCB_NO_TERMINAL: return "missing terminal MCB";
    case M18_MCB_TOO_MANY_OWNERS: return "owner count exceeds the bounded checker";
    case M18_MCB_OWNER_MISSING: return "allocated block has no matching PSP block";
    case M18_MCB_CURRENT_PSP_MISSING: return "current PSP has no owned MCB block";
    case M18_MCB_OWNER_MISMATCH: return "PSP block owner does not match its segment";
    case M18_MCB_PSP_BLOCK_TOO_SMALL: return "PSP block is smaller than 256 bytes";
    case M18_MCB_VISITOR_FAILED: return "unable to report MCB entry";
    default: return "unknown MCB validation error";
  }
}
