/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Host fixtures for the production FORMAT: a drive-B: track model behind the
   VA floppy BIOS (INT 80h) and DOS absolute-sector access to the same image. */
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define main m19_format_main
#include "../../tools/m19/maintenance/format.c"
#undef main

#define TRACKS 160U

static unsigned char image[M19_TOTAL_SECTORS][M19_SECTOR_BYTES];
static int formatted[TRACKS];
static unsigned char work[0x30];
static unsigned bad_lba = 0xffffU;
static unsigned formats_issued, bios_writes;

static void reset_media(void)
{
  memset(image, 0, sizeof(image));
  memset(formatted, 0, sizeof(formatted));
  memset(work, 0, sizeof(work));
  work[WORK_SURFMODE] = 0x03;          /* both drives double-sided */
  work[1] = 0xff;                      /* drive 1 mode unset at boot */
  bad_lba = 0xffffU;
  formats_issued = bios_writes = 0;
}

static int lba_ok(unsigned lba)
{
  return lba < M19_TOTAL_SECTORS && formatted[lba / M19_SECTORS_PER_TRACK] &&
         lba != bad_lba;
}

void *test_mk_fp(unsigned segment, unsigned offset)
{
  assert(segment == BIOS_WORK_SEGMENT && offset == 0);
  return work;
}

int intdos(union REGS *input, union REGS *output)
{
  unsigned char function = input->h.ah;
  memset(output, 0, sizeof(*output));
  assert(function == 0x36 || function == 0x0d || function == 0x2a ||
         function == 0x2c);
  if (function == 0x2a) {
    output->x.cx = 2026;
    output->x.dx = 0x0a01;
  } else if (function == 0x2c) {
    output->x.cx = 0x0c22;
    output->x.dx = 0x0b00;
  }
  return 0;
}

unsigned m19_fdd_bios(unsigned ax, unsigned cx, unsigned dx, void *buffer)
{
  unsigned function = ax >> 8, unit = cx >> 8, track = cx & 0xffU;
  unsigned lba = track * M19_SECTORS_PER_TRACK + (dx >> 8) - 1U;
  assert(unit == 1);
  switch (function) {
  case BIOS_SET_MODE:
    work[1] = (unsigned char)ax;
    return 0;
  case BIOS_FORMAT_TRACK:
    assert(work[1] == DISK_MODE_2HD_1024 && (dx & 0xffU) == N_1024_MFM);
    if (track >= TRACKS)
      return 0x0e;
    formatted[track] = 1;
    memset(image[track * M19_SECTORS_PER_TRACK], (int)(ax & 0xffU),
           M19_SECTORS_PER_TRACK * M19_SECTOR_BYTES);
    ++formats_issued;
    return 0;
  case BIOS_READ_NO_RETRY:
    if (!lba_ok(lba))
      return 0x05;
    memcpy(buffer, image[lba], M19_SECTOR_BYTES);
    return 0;
  case BIOS_WRITE:
    if (!lba_ok(lba))
      return 0x05;
    memcpy(image[lba], buffer, M19_SECTOR_BYTES);
    ++bios_writes;
    return 0;
  }
  assert(0);
  return 0xff;
}

unsigned m19_abs_sector(unsigned writing, unsigned drive, unsigned sector,
                        void *buffer)
{
  if (drive != 1 || !lba_ok(sector))
    return 1;
  if (writing)
    memcpy(image[sector], buffer, M19_SECTOR_BYTES);
  else
    memcpy(buffer, image[sector], M19_SECTOR_BYTES);
  return 0;
}

void m19_critical(void) { }

void (*_dos_getvect(unsigned vector))(void)
{
  (void)vector;
  return m19_critical;
}

void _dos_setvect(unsigned vector, void (*handler)(void))
{
  (void)vector;
  (void)handler;
}

static int run_format(const char *a1, const char *a2, const char *a3)
{
  static char program[] = "FORMAT";
  char *argv[5];
  int argc = 1;
  argv[0] = program;
  if (a1) argv[argc++] = (char *)a1;
  if (a2) argv[argc++] = (char *)a2;
  if (a3) argv[argc++] = (char *)a3;
  argv[argc] = NULL;
  cylinders = 80;
  quick = 0;
  geometry_given = 0;
  return m19_format_main(argc, argv);
}

static unsigned word_at(const unsigned char *p)
{
  return p[0] | ((unsigned)p[1] << 8);
}

int main(void)
{
  struct m19_layout layout;
  static unsigned char before[M19_TOTAL_SECTORS][M19_SECTOR_BYTES];

  /* Blank disk, default 80 cylinders: every track formatted, volume valid. */
  reset_media();
  assert(run_format("B:", NULL, NULL) == 0);
  assert(formats_issued == 160 && work[1] == DISK_MODE_2HD_1024);
  assert(m19_validate_bpb(image[0], M19_SECTOR_BYTES, &layout));
  assert(layout.cylinders == 80 && word_at(image[0] + 19) == 1280);
  assert(image[1][0] == 0xfe && image[3][0] == 0xfe && image[11][0] == FILL_BYTE);

  /* Blank disk, NEC-compatible 77 cylinders. */
  reset_media();
  assert(run_format("B:", "/T:77", NULL) == 0);
  assert(formats_issued == 154 && !formatted[154]);
  assert(m19_validate_bpb(image[0], M19_SECTOR_BYTES, &layout));
  assert(layout.cylinders == 77 && layout.data_clusters == 1221);

  /* An unreadable data sector becomes one bad cluster. */
  reset_media();
  bad_lba = 300;
  assert(run_format("B:", "/T:77", NULL) == 0);
  {
    unsigned cluster = 300 - M19_FIRST_DATA_SECTOR + 2U, value;
    assert(m19_fat12_get(image[1], M19_FAT_BYTES, cluster, &value) && value == 0xff7);
  }

  /* An unreadable system sector fails. */
  reset_media();
  bad_lba = 3;
  assert(run_format("B:", NULL, NULL) == 1);

  /* A reserved user ID list (IDR) is refused before any track is formatted. */
  reset_media();
  work[WORK_BIOSMODE] = BIOSMODE_IDR;
  assert(run_format("B:", NULL, NULL) == 1 && formats_issued == 0);

  /* /Q on a blank disk writes nothing. */
  reset_media();
  memcpy(before, image, sizeof(before));
  assert(run_format("B:", "/Q", NULL) == 1);
  assert(!memcmp(before, image, sizeof(before)) && bios_writes == 0);

  /* /Q keeps the existing 77-cylinder geometry; /T:80 /Q is refused. */
  reset_media();
  assert(run_format("B:", "/T:77", NULL) == 0);
  formats_issued = 0;
  assert(run_format("B:", "/Q", NULL) == 0 && formats_issued == 0);
  assert(m19_validate_bpb(image[0], M19_SECTOR_BYTES, &layout) && layout.cylinders == 77);
  assert(run_format("B:", "/Q", "/T:80") == 1);

  /* Other drives and options are refused. */
  assert(run_format("A:", NULL, NULL) == 2);
  assert(run_format("B:", "/T:40", NULL) == 2);

  puts("M19 FORMAT track and metadata tests: PASS");
  return 0;
}
