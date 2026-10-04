/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef M20_DOS_TEST_STUB_H
#define M20_DOS_TEST_STUB_H
#define __cdecl
#define __interrupt
#define __far
#define _A_NORMAL 0x00
union REGS {
  struct {
    unsigned char al, ah, bl, bh, cl, ch, dl, dh;
  } h;
  struct {
    unsigned short ax, bx, cx, dx, si, di, cflag;
  } x;
};
int intdos(union REGS *input, union REGS *output);
/* Host fixtures map a real-mode segment:offset to fixture memory. */
void *test_mk_fp(unsigned segment, unsigned offset);
#define MK_FP(segment, offset) test_mk_fp((segment), (offset))
/* Host fixtures for the DOS file services used by SYS. */
unsigned _dos_open(const char *path, unsigned mode, int *handle);
unsigned _dos_creatnew(const char *path, unsigned attributes, int *handle);
unsigned _dos_read(int handle, void *buffer, unsigned count, unsigned *bytes);
unsigned _dos_write(int handle, void *buffer, unsigned count, unsigned *bytes);
unsigned _dos_commit(int handle);
unsigned _dos_close(int handle);
void (*_dos_getvect(unsigned vector))(void);
void _dos_setvect(unsigned vector, void (*handler)(void));
#endif
