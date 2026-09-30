/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Small ASCII pager using DOS file I/O and DOS AH=06 console input.
   AH=06 reads DOS standard input, so a redirected or piped standard input
   is moved to a private handle and handle 0 is rebound to CON first. */
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

/* Keep piped/redirected data readable through a duplicate handle and make
   DOS standard input the console, so paging keys never consume data. */
static FILE *bind_console_input(int data_from_stdin)
{
  int console, data;
  FILE *stream;
  if (stdin_is_console())
    return stdin;
  console = open("CON", O_RDONLY | O_BINARY);
  if (console < 0)
    return NULL;
  data = -1;
  if (data_from_stdin) {
    data = dup(0);
    if (data < 0) {
      close(console);
      return NULL;
    }
  }
  if (dup2(console, 0) != 0) {
    close(console);
    if (data >= 0)
      close(data);
    return NULL;
  }
  close(console);
  if (!data_from_stdin)
    return stdin;
  stream = fdopen(data, "rb");
  if (stream == NULL)
    close(data);
  return stream;
}

static int console_key(void)
{
  union REGPACK regs;
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
  FILE *console_data;
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
  console_data = bind_console_input(input == stdin);
  if (console_data == NULL) {
    fputs("MORE: cannot bind console input.\n", stderr);
    if (input != stdin)
      fclose(input);
    return 2;
  }
  if (input == stdin)
    input = console_data;
  result = page_input(input);
  if (input != stdin && fclose(input) != 0 && result == 0) {
    fputs("MORE: close error.\n", stderr);
    return 3;
  }
  return result;
}
