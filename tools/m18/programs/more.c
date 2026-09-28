/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Small ASCII pager using DOS file I/O and DOS AH=06 console input. */
#include <dos.h>
#include <stdio.h>
#include <string.h>

#define SCREEN_COLUMNS 80
#define PAGE_LINES 24
#define DOS_ZERO_FLAG 0x0040U

static int usage(void)
{
  puts("MORE - display text a page at a time");
  puts("Usage: MORE [/? | file]");
  puts("Keys: Space=next page, Enter=one line, Q=quit");
  puts("Uses an 80x25 VA text screen and DOS console input.");
  return 0;
}

static int console_key(void)
{
  union REGS regs;
  for (;;) {
    memset(&regs, 0, sizeof(regs));
    regs.h.ah = 0x06;
    regs.h.dl = 0xff;
    intdos(&regs, &regs);
    if ((regs.x.cflag & DOS_ZERO_FLAG) == 0 && regs.h.al != 0)
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
  result = page_input(input);
  if (input != stdin && fclose(input) != 0 && result == 0) {
    fputs("MORE: close error.\n", stderr);
    return 3;
  }
  return result;
}
