/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Small ASCII pager using DOS file I/O and DOS AH=06 console input.
   AH=06 reads DOS standard input, so with redirected or piped input the
   paging keys come from a separate raw CON handle instead. */
#include <dos.h>
#include <fcntl.h>
#include <i86.h>
#include <io.h>
#include <stdio.h>
#include <string.h>

#define SCREEN_COLUMNS 80
#define PAGE_LINES 24
#define DOS_DEVICE_BIT 0x0080U
#define DOS_CONSOLE_INPUT_BIT 0x0001U

static int usage(void)
{
  puts("MORE - display text a page at a time");
  puts("Usage: MORE [/? | file]");
  puts("Keys: Space=next page, Enter=one line, Q=quit");
  puts("Uses an 80x25 VA text screen and DOS console input.");
  return 0;
}

static int stdin_is_console(void)
{
  union REGPACK regs;
  memset(&regs, 0, sizeof(regs));
  regs.w.ax = 0x4400;
  regs.w.bx = 0;
  intr(0x21, &regs);
  if (regs.w.flags & INTR_CF)
    return 0;
  return (regs.w.dx & (DOS_DEVICE_BIT | DOS_CONSOLE_INPUT_BIT)) ==
         (DOS_DEVICE_BIT | DOS_CONSOLE_INPUT_BIT);
}

/* When standard input is redirected or piped, read paging keys from a
   separate raw CON handle so that keys never consume the paged data. */
static int key_handle = -1;

static int open_console_keys(void)
{
  union REGPACK regs;
  if (stdin_is_console())
    return 1;
  key_handle = open("CON", O_RDONLY | O_BINARY);
  if (key_handle < 0)
    return 0;
  memset(&regs, 0, sizeof(regs));
  regs.w.ax = 0x4400;
  regs.w.bx = key_handle;
  intr(0x21, &regs);
  if (regs.w.flags & INTR_CF)
    return 0;
  regs.w.dx = (regs.w.dx & 0x00ffU) | 0x0020U;   /* raw: no line editing */
  regs.w.ax = 0x4401;
  regs.w.bx = key_handle;
  intr(0x21, &regs);
  return (regs.w.flags & INTR_CF) == 0;
}

static int console_key(void)
{
  union REGPACK regs;
  if (key_handle >= 0) {
    unsigned char ch;
    if (read(key_handle, &ch, 1) != 1)
      return 'q';
    return ch;
  }
  for (;;) {
    memset(&regs, 0, sizeof(regs));
    regs.h.ah = 0x06;
    regs.h.dl = 0xff;
    intr(0x21, &regs);
    if ((regs.w.flags & INTR_ZF) == 0 && regs.h.al != 0)
      return regs.h.al;
  }
}

static int page_input(FILE *input)
{
  unsigned lines = 0;
  unsigned column = 0;
  int ch;

  while ((ch = fgetc(input)) != EOF) {
    if (ch == '\t') {
      unsigned spaces = 4U - (column & 3U);
      while (spaces-- != 0) {
        if (putchar(' ') == EOF)
          return 3;
        if (++column == SCREEN_COLUMNS) {
          column = 0;
          if (++lines == PAGE_LINES)
            goto prompt;
        }
      }
      continue;
    }
    if (putchar(ch) == EOF)
      return 3;
    if (ch == '\r') {
      column = 0;
      continue;
    }
    if (ch == '\n' || ++column == SCREEN_COLUMNS) {
      column = 0;
      if (++lines == PAGE_LINES) {
prompt:
        {
          int key;
          fflush(stdout);
          fputs("-- MORE -- Space/Enter/Q: ", stderr);
          fflush(stderr);
          key = console_key();
          fputs("\r                         \r", stderr);
          if (key == 'q' || key == 'Q' || key == 3)
            return 1;
          lines = key == '\r' || key == '\n' ? PAGE_LINES - 1 : 0;
        }
      }
    }
  }
  if (ferror(input)) {
    fputs("MORE: read error.\n", stderr);
    return 2;
  }
  return 0;
}

int main(int argc, char **argv)
{
  FILE *input = stdin;
  int result;

  if (argc > 2) {
    usage();
    return 2;
  }
  if (argc == 2) {
    if (strcmp(argv[1], "/?") == 0 || strcmp(argv[1], "-?") == 0)
      return usage();
    if (argv[1][0] == '/' || argv[1][0] == '-') {
      usage();
      return 2;
    }
    input = fopen(argv[1], "rb");
    if (input == NULL) {
      fprintf(stderr, "MORE: cannot open %s.\n", argv[1]);
      return 2;
    }
  }
  if (!open_console_keys()) {
    fputs("MORE: cannot open console input.\n", stderr);
    if (input != stdin)
      fclose(input);
    return 2;
  }
  result = page_input(input);
  if (input != stdin && fclose(input) != 0 && result == 0) {
    fputs("MORE: close error.\n", stderr);
    return 3;
  }
  return result;
}
