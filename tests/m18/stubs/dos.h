/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M18_DOS_TEST_STUB_H
#define M18_DOS_TEST_STUB_H
#define __cdecl
#define __interrupt
#define __far
union REGS {
  struct { unsigned char al; unsigned char ah; } h;
};
int intdos(union REGS *input, union REGS *output);
#endif
