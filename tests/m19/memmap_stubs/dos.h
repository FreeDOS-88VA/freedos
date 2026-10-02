/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M19_MEMMAP_TEST_DOS_H
#define M19_MEMMAP_TEST_DOS_H
#include <stdint.h>
#define far
union REGS {
  struct { uint16_t ax, bx, cx, dx, si, di, cflag; } x;
  struct { uint8_t al, ah, bl, bh, cl, ch, dl, dh; } h;
};
struct SREGS { uint16_t es, cs, ss, ds; };
void *m19_test_far_pointer(unsigned segment, unsigned offset);
#define MK_FP(segment, offset) m19_test_far_pointer((segment), (offset))
int intdosx(const union REGS *, union REGS *, struct SREGS *);
#endif
