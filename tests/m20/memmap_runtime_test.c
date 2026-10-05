/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Synthetic interface/control-flow test; not a Watcom heap implementation. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>

static int unbuffered, primed, shrinks, reads, near_result, far_result;

static int test_setvbuf(FILE *stream, char *buffer, int mode, size_t size)
{
  /* No library buffer block may sit above the program after the trim. */
  assert(stream == stdout && buffer == NULL && mode == _IONBF && size == 0);
  assert(!primed && shrinks == 0);
  unbuffered = 1;
  return setvbuf(stream, buffer, mode, size);
}

static int test_fflush(FILE *stream)
{
  assert(stream == stdout && unbuffered);
  primed = 1;
  return fflush(stream);
}

int _nheapshrink(void)
{
  assert(primed && shrinks == 0);
  ++shrinks;
  return near_result;
}

int _fheapshrink(void)
{
  assert(primed && shrinks == 1);
  ++shrinks;
  return far_result;
}

int intdosx(const union REGS *input, union REGS *output, struct SREGS *segments)
{
  memset(output, 0, sizeof(*output));
  switch (input->h.ah) {
  case 0x30:
    output->h.al = 6;
    output->h.ah = 22;
    output->h.bh = 0xfd;
    output->h.bl = 43;
    break;
  case 0x52:
    output->x.bx = 0x20;
    segments->es = 0x2000;
    break;
  case 0x62:
    output->x.bx = 0x1001;
    break;
  default:
    abort();
  }
  return 0;
}

void *m20_test_far_pointer(unsigned segment, unsigned offset)
{
  /* query_first_mcb uses the target's native unsigned word; the host stub
     returns a native host word. Real 16-bit DOS is checked separately. */
  static unsigned first = 0x1000;
  static unsigned char header[16] = {
    'Z', 1, 0x10, 0, 1, 0, 0, 0, 'M','E','M','M','A','P',' ',' '
  };
  if (segment == 0x2000 && offset == 0x1e)
    return &first;
  assert(segment == 0x1000 && offset == 0);
  assert(primed && shrinks == 2 && !near_result && !far_result);
  ++reads;
  return header;
}

#define main m20_memmap_main
#define fflush test_fflush
#define setvbuf test_setvbuf
#include "../../tools/m20/memmap/memmap.c"
#undef setvbuf
#undef fflush
#undef main

static void check(int near_status, int far_status, int expected, int calls)
{
  char *arguments[] = {"MEMMAP", "/CHECK", NULL};
  unbuffered = primed = shrinks = reads = 0;
  near_result = near_status;
  far_result = far_status;
  assert(m20_memmap_main(2, arguments) == expected);
  assert(shrinks == calls);
  assert((reads != 0) == (expected == 0));
}

int main(void)
{
  check(0, 0, 0, 2);
  check(-1, 0, 3, 1);
  check(0, -1, 3, 2);
  return 0;
}
