/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Native PC-88VA 2HD FORMAT for drive B: only.
 *
 * The default operation formats every track through the VA floppy BIOS
 * (INT 80h AH=03h, disk mode 23h: 8 x 1024-byte MFM sectors), verifies every
 * sector, marks unreadable data clusters bad and writes a fresh FAT12 volume.
 * /Q only rewrites FAT12 metadata on a disk that already carries a valid
 * native BPB. /T:80 (default) and /T:77 select the cylinder count. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "volume.h"

#define TARGET_UNIT 1U
#define DISK_MODE_2HD_1024 0x23U
#define FILL_BYTE 0xe5U
#define N_1024_MFM 0x03U
#define BIOS_FORMAT_TRACK 0x03U
#define BIOS_READ_NO_RETRY 0x81U
#define BIOS_WRITE 0x02U
#define BIOS_SET_MODE 0x0aU
/* Documented floppy BIOS work area (segment 0063h): disk modes at +0/+1,
   [SURFMODE] at +4 and [BIOSMODE] at +5. */
#define BIOS_WORK_SEGMENT 0x0063U
#define WORK_SURFMODE 4U
#define WORK_BIOSMODE 5U
#define BIOSMODE_IDR 0x04U

static struct m19_volume volume;
static struct m19_check_report report;
static unsigned char sector[M19_SECTOR_BYTES];
static unsigned char verify[M19_SECTOR_BYTES];
static unsigned cylinders = 80;
static int quick;
static int geometry_given;

static void put16(unsigned char *p, unsigned value)
{
  p[0] = (unsigned char)value;
  p[1] = (unsigned char)(value >> 8);
}

static void put32(unsigned char *p, unsigned long value)
{
  put16(p, (unsigned)value);
  put16(p + 2, (unsigned)(value >> 16));
}

static unsigned total_sectors(void)
{
  return cylinders * M19_SECTORS_PER_TRACK * M19_HEADS;
}

/* A per-format serial from the DOS date and time, as DOS FORMAT does. */
static unsigned long volume_serial(void)
{
  union REGS in, date, time;
  memset(&in, 0, sizeof(in));
  in.h.ah = 0x2a;
  intdos(&in, &date);
  in.h.ah = 0x2c;
  intdos(&in, &time);
  return ((unsigned long)(date.x.dx + time.x.dx) << 16) |
         (unsigned)(date.x.cx + time.x.cx);
}

static void make_boot(void)
{
  memset(sector, 0, sizeof(sector));
  sector[0] = 0xeb;
  sector[1] = 0xfe;
  sector[2] = 0x90;
  memcpy(sector + 3, "FDPC88VA", 8);
  put16(sector + 11, M19_SECTOR_BYTES);
  sector[13] = 1;
  put16(sector + 14, 1);
  sector[16] = 2;
  put16(sector + 17, M19_ROOT_ENTRIES);
  put16(sector + 19, total_sectors());
  sector[21] = 0xfe;
  put16(sector + 22, 2);
  put16(sector + 24, M19_SECTORS_PER_TRACK);
  put16(sector + 26, M19_HEADS);
  sector[38] = 0x29;
  put32(sector + 39, volume_serial());
  memcpy(sector + 43, "NO NAME    ", 11);
  memcpy(sector + 54, "FAT12   ", 8);
  sector[510] = 0x55;
  sector[511] = 0xaa;
  sector[1022] = 0x55;
  sector[1023] = 0xaa;
}

static int write_verified_dos(unsigned lba, unsigned char *data)
{
  return m19_write_sector(TARGET_UNIT, lba, data) &&
         m19_read_sector(TARGET_UNIT, lba, verify) &&
         memcmp(data, verify, M19_SECTOR_BYTES) == 0;
}

/* LBA to the VA BIOS logical track (cylinder * 2 + head) and sector ID. */
static unsigned bios_track(unsigned lba)
{
  return lba / M19_SECTORS_PER_TRACK;
}

static unsigned bios_sector(unsigned lba)
{
  return lba % M19_SECTORS_PER_TRACK + 1U;
}

static int bios_transfer(unsigned function, unsigned lba, void *buffer)
{
  unsigned cx = (TARGET_UNIT << 8) | bios_track(lba);
  unsigned dx = (bios_sector(lba) << 8) | N_1024_MFM;
  return m19_fdd_bios((function << 8) | 1U, cx, dx, buffer) == 0;
}

static int write_verified_bios(unsigned lba, unsigned char *data)
{
  return bios_transfer(BIOS_WRITE, lba, data) &&
         bios_transfer(BIOS_READ_NO_RETRY, lba, verify) &&
         memcmp(data, verify, M19_SECTOR_BYTES) == 0;
}

/* Require a default ID list (IDR clear) and a double-sided drive 1. */
static int bios_prepare(void)
{
  unsigned char __far *work;

  if (m19_fdd_bios((BIOS_SET_MODE << 8) | DISK_MODE_2HD_1024,
                   TARGET_UNIT << 8, 0, sector) != 0)
    return 0;
  work = (unsigned char __far *)MK_FP(BIOS_WORK_SEGMENT, 0);
  if (work[TARGET_UNIT] != DISK_MODE_2HD_1024 ||
      (work[WORK_BIOSMODE] & BIOSMODE_IDR) ||
      !(work[WORK_SURFMODE] & (1U << TARGET_UNIT)))
    return 0;
  return 1;
}

static void set_fat(unsigned cluster, unsigned value)
{
  unsigned offset = cluster + cluster / 2U;
  unsigned packed = volume.fat[offset] | ((unsigned)volume.fat[offset + 1U] << 8);
  if (cluster & 1U)
    packed = (packed & 0x000fU) | (value << 4);
  else
    packed = (packed & 0xf000U) | value;
  volume.fat[offset] = (unsigned char)packed;
  volume.fat[offset + 1U] = (unsigned char)(packed >> 8);
}

/* Format and surface-check every track. System-area errors are fatal;
   unreadable data sectors become bad clusters (FF7h). */
static int format_tracks(void)
{
  unsigned track, n, lba;
  for (track = 0; track < cylinders * M19_HEADS; ++track) {
    if (track % 8U == 0) {
      printf("\rFormatting cylinder %u of %u", track / M19_HEADS + 1U, cylinders);
      fflush(stdout);
    }
    if (m19_fdd_bios((BIOS_FORMAT_TRACK << 8) | FILL_BYTE,
                     (TARGET_UNIT << 8) | track, N_1024_MFM, sector) != 0) {
      printf("\n");
      return 0;
    }
    for (n = 0; n < M19_SECTORS_PER_TRACK; ++n) {
      lba = track * M19_SECTORS_PER_TRACK + n;
      if (bios_transfer(BIOS_READ_NO_RETRY, lba, verify))
        continue;
      if (lba < M19_FIRST_DATA_SECTOR) {
        printf("\n");
        return 0;
      }
      set_fat(lba - M19_FIRST_DATA_SECTOR + 2U, 0xff7U);
    }
  }
  printf("\rFormatted %u cylinders.            \n", cylinders);
  return 1;
}

static int parse_arguments(int argc, char **argv)
{
  int i, drive = 0;
  for (i = 1; i < argc; ++i) {
    const char *a = argv[i];
    if (!strcmp(a, "B:") || !strcmp(a, "b:"))
      ++drive;
    else if (!strcmp(a, "/Q") || !strcmp(a, "/q"))
      quick = 1;
    else if (!strcmp(a, "/T:80") || !strcmp(a, "/t:80")) {
      cylinders = 80;
      geometry_given = 1;
    } else if (!strcmp(a, "/T:77") || !strcmp(a, "/t:77")) {
      cylinders = 77;
      geometry_given = 1;
    } else
      return 0;
  }
  return drive == 1;
}

static int confirm_format(void)
{
  char line[32];
  if (quick)
    puts("Quick format: rewrites FAT12 metadata only; old data sectors remain.");
  else
    printf("Formats every track of B: as native 2HD (%u cylinders x 2 x 8 x 1024).\n",
           cylinders);
  puts("All existing B: directory entries and files will be lost.");
  fputs("Type YES to format B: (anything else cancels): ", stdout);
  fflush(stdout);
  if (!fgets(line, sizeof(line), stdin))
    return 0;
  line[strcspn(line, "\r\n")] = 0;
  return strcmp(line, "YES") == 0;
}

static void usage(void)
{
  puts("FORMAT - format a native PC-88VA 2HD disk in drive B:");
  puts("Usage: FORMAT B: [/T:80 | /T:77] [/Q]");
  puts("  /T:80  80 cylinders, 1280 sectors (default, FreeDOS distribution)");
  puts("  /T:77  77 cylinders, 1232 sectors (NEC-compatible 2HD)");
  puts("  /Q     quick: keep the tracks of a disk with a valid native BPB and");
  puts("         rewrite only the FAT12 metadata");
  puts("Without /Q every track is formatted and verified; this is destructive.");
}

int main(int argc, char **argv)
{
  unsigned i;
  void (__interrupt __far *old24)(void);
  int good = 1;

  if (argc == 2 && (!strcmp(argv[1], "/?") || !strcmp(argv[1], "-?"))) {
    usage();
    return 0;
  }
  if (!parse_arguments(argc, argv)) {
    fputs("FORMAT: use FORMAT B: [/T:80 | /T:77] [/Q]; other drives are refused.\n", stderr);
    return 2;
  }

  old24 = _dos_getvect(0x24);
  _dos_setvect(0x24, m19_critical);
  if (quick) {
    struct m19_layout existing;
    if (!m19_bind_volume(TARGET_UNIT) || !m19_read_sector(TARGET_UNIT, 0, verify) ||
        !m19_validate_bpb(verify, sizeof(verify), &existing) ||
        (geometry_given && existing.cylinders != cylinders)) {
      fputs("FORMAT: /Q needs a valid native 2HD BPB of the selected geometry on B:;\n"
            "        run FORMAT B: without /Q for a blank disk. Nothing was written.\n",
            stderr);
      _dos_setvect(0x24, old24);
      return 1;
    }
    cylinders = existing.cylinders;
  }
  if (!confirm_format()) {
    puts("FORMAT: cancelled; B: was not changed.");
    _dos_setvect(0x24, old24);
    return 1;
  }

  memset(volume.fat, 0, sizeof(volume.fat));
  volume.fat[0] = 0xfe;
  volume.fat[1] = 0xff;
  volume.fat[2] = 0xff;
  memset(volume.root, 0, sizeof(volume.root));
  make_boot();

  m19_reset_disk();
  if (!quick) {
    good = bios_prepare();
    if (!good)
      fputs("FORMAT: the VA floppy BIOS refused 2HD mode for B:; nothing was written.\n",
            stderr);
    if (good && !format_tracks()) {
      good = 0;
      fputs("FORMAT: track format or system-area verification failed.\n", stderr);
    }
    /* The DOS media binding cannot describe a blank disk; write the new
       metadata through the BIOS, boot sector last, then let DOS rebind. */
    for (i = 0; i < 2U * 2U && good; ++i)
      good = write_verified_bios(1U + i, volume.fat + (i % 2U) * M19_SECTOR_BYTES);
    for (i = 0; i < M19_ROOT_BYTES / M19_SECTOR_BYTES && good; ++i)
      good = write_verified_bios(5U + i, volume.root + i * M19_SECTOR_BYTES);
    if (good)
      good = write_verified_bios(0, sector);
  } else {
    for (i = 0; i < 2U * 2U && good; ++i)
      good = write_verified_dos(1U + i, volume.fat + (i % 2U) * M19_SECTOR_BYTES);
    for (i = 0; i < M19_ROOT_BYTES / M19_SECTOR_BYTES && good; ++i)
      good = write_verified_dos(5U + i, volume.root + i * M19_SECTOR_BYTES);
    if (good)
      good = write_verified_dos(0, sector);
  }
  m19_reset_disk();
  if (good)
    good = m19_load_volume(TARGET_UNIT, &volume) &&
           m19_check_allocations(TARGET_UNIT, &volume, &report) &&
           volume.layout.cylinders == cylinders &&
           report.free_clusters + report.bad_clusters == volume.layout.data_clusters;

  if (good) {
    printf("FORMAT: %u-cylinder native 2HD FAT12 volume ready on B:.\n", cylinders);
    printf("%lu bytes available", (unsigned long)report.free_clusters * M19_SECTOR_BYTES);
    if (report.bad_clusters)
      printf("; %lu bytes in bad sectors", (unsigned long)report.bad_clusters * M19_SECTOR_BYTES);
    puts(".");
    puts("B: is a data disk; use SYS A: B: to transfer the boot system.");
  } else {
    fputs("FORMAT: format, write/readback or filesystem validation failed; B: may be unusable.\n",
          stderr);
  }
  _dos_setvect(0x24, old24);
  return good ? 0 : 1;
}
