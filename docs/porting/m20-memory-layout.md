# M20 conventional memory and boot layout contract

This is the active PC-88VA memory contract for M20. It replaces
[`m17-memory-layout.md`](m17-memory-layout.md) for M20 work and states every
change from it. M13-M19 sizing instructions and results remain history.
It describes project source policy and the layout of the M20 release build;
it contains no firmware contents or private firmware observations, and it is
not a claim that every capacity or workload has passed.

## Unchanged from M17

The following M17 rules apply to M20 without change. The M17 document gives
their full wording.

- **Capacity.** The loader and kernel measure writable conventional RAM at
  boot (one restored sample per KiB from 256 KiB to the 640 KiB cap, plus the
  minimum-capacity guard). Saved BIOS/backup selections never determine,
  cap or replace the measured capacity. Installed RAM, saved selection,
  measured capacity and DOS-free memory are different quantities.
- **`PC88VA_LOADSEG`.** A hexadecimal paragraph address selecting the expanded
  resident kernel base and the consecutive kernel work area. The default is
  1000h (physical 10000h). It is platform policy, not a measured firmware
  footprint; the region below it is not part of the DOS arena.
- **Loader profile.** Stage 1 is entered at physical 30000h and stage 2 is
  loaded at 12000h (`config/m20/loader.json`); these are temporary.
- **Permanent low layout.** Resident code/data, the bounded NEAR work arena,
  resident assembly and final FAR kernel work are consecutive from
  `PC88VA_LOADSEG * 16`. The runtime checks of M17 (resident end equals the
  first system MCB, system MCB end equals the next free MCB, no hole before the
  temporary reservation, coalescing after release) are unchanged.
- **Temporary layout.** For measured RAM end `T`: compressed file and carrier
  at `T - 19000h`, scratch at `T - 9000h`, 4 KiB history ring at `T - 8000h`,
  bridge stack top at `T - 10h`, INIT plus its 4 KiB stack ending at
  `T - 2000h`. INIT follows measured RAM independently of LOADSEG; temporary
  allocations are released and coalesced before the shell starts.
- **Qualification rules.** Two clean builds from pinned public sources with
  identical media, verification of the linked map, descriptor and MZ fixups,
  modelling of unavailable/read-only RAM and stale selections (including
  512 KiB installed with a retained 640 KiB selection), INIT diagnostics with
  SS different from DS, and guest checks of shell startup, COM/MZ execution
  and file write/readback on the exact candidate. M20 uses its own helpers
  under `tools/m20/`.

## Changes from M17

### 1. Machine initialization is not resident

The single-shot machine initialization (machine checks, the conservative
memory map and the interrupt-adoption check) is assembled into its own
segment `M10_BOOT_TEXT`, class `M10BOOT`, in the `PC88VA_PLATFORM` group, so
its near calls and CS-relative state keep the platform frame.

- The class is declared in `kernel/segs.inc` after `M13_INIT_TEXT`, so the
  linker places it after the INIT source and before the bootstrap `_STACK`
  in the expanded image. It runs once, in place, before INIT, and is not part
  of the resident hull.
- It must not lie at the end of the resident hull: the unpack bridge copies
  the resident assembly (HMA text) there before the kernel starts. The first
  M20 candidate placed it there and did not boot; the carrier builder
  (`tools/m20/build_compressed_kernel.py`) now rejects a boot text that is not
  between the end of the INIT source and the stack.
- The 1024-byte interrupt-vector snapshot and the 256-byte conservative arena
  live in the initialization stack frame (1280 bytes below the saved
  registers on the bootstrap stack), not in resident storage. The memory
  record describing that arena is withdrawn when initialization returns.
- The clock service and machine state remain resident.

### 2. Milestone diagnostics are not linked

The M09 console, M11 keyboard and M12 disk qualification diagnostics are
entered only from the compile-only `pc88va/kernel/startup.asm`. With
`PC88VA_M13` they are not assembled into the linked kernel. Flat unit-test
builds keep them.

Together with change 1, the resident PC-88VA platform group shrank from
9,072 to 6,352 bytes.

### 3. Distribution configuration

`config/m20/CONFIG.SYS`:

- `STACKS=0,0`: no hardware-interrupt stack pool (2,048 bytes in M17's
  default configuration).
- `BUFFERS=4`: the common kernel raises the count to its minimum of six
  (upstream behavior, unchanged); each buffer holds one 1024-byte sector.
  Without a `BUFFERS=` line the VA default of ten applies, as in M17.
- `FILES=16`, `LASTDRIVE=E`, `PC88VA_LOADSEG=1000`.

### 4. Interrupt vectors

The common kernel sets INT 23h-3Fh to an empty handler at startup (upstream
behavior). On PC-88VA:

- INT 33h, the ROM mouse BIOS, is saved before that loop and restored
  after it.
- INT 87h (advanced graphics BIOS), INT 88h (animation BIOS), INT 90h
  (V1/V2 supervisor) and INT 95h (its CALLN interface) are pointed at a
  resident handler in the kernel's `CONST` segment that returns with the
  carry flag set. Their RAM work areas or RAM vectors lie in memory that
  holds the kernel at the default `PC88VA_LOADSEG`. This is an availability
  limit of the M20 layout, recorded in the release notes.

Other ROM service vectors are left as the firmware installed them.

### 5. Memory below `PC88VA_LOADSEG`

Unchanged policy: the region is not part of the DOS arena. It holds the
interrupt vector table, firmware data and work areas, and the kernel's root
PSP and its environment (`DOS_PSP` = 0200h, `hdr/mcb.h`).

FreeDOS MEM (system disk) counts everything below the first MCB, including
this region, as SYSTEM. Its PC88VA build takes conventional capacity from the
end of the DOS MCB chain, because INT 12h and INT 15h are not memory services
on PC-88VA.

Returning firmware-unused parts of this region to DOS is not part of M20. The
owner decided to do it in M21 together with the project Japanese front-end
processor, which removes the ROM front-end processor's use of low RAM. That
change must be specified in the M21 layout document, must keep every
remaining firmware work area and interrupt path intact, and must be qualified
with the full capacity and retained-selection matrix.

### 6. Shell placement (system disk)

Not a kernel layout change, but it determines DOS-free memory:

- Menu choice 1 loads `KSSF.COM` low and FreeCOM above it with `/SWAP`.
  While a program started from the prompt runs, FreeCOM is swapped out and
  only its environment, swap state and resident context remain at the top of
  memory (about 4 KB) plus KSSF (928 bytes). Batch files, redirection and
  pipes run without swapping.
- Menu choice 2 loads MS-DOS 4.0 COMMAND.COM (about 6.4 KB resident).

## M20 release build layout

Release candidate 5 system disk, VAEG VA2, 640 KiB installed, startup display
and `MEM /D` (FreeCOM not swapped, MEM loaded):

| Item | Value |
| --- | --- |
| Kernel loaded | 10000h (`PC88VA_LOADSEG=1000h`) |
| Kernel low (resident and work) | 10000h-22CA0h |
| Kernel work | 20F70h-22CA0h (7,456 bytes: buffers 6,272, files, drive table) |
| DOS free begins | 22CB0h |
| Resident assembly | 20500h |
| INIT | 99080h, 16,251 bytes; stack 9D000h-9E000h |
| Staging, carrier | 87000h; scratch 97000h; ring 98000h; bridge stack top 9FFF0h |

`MEM /C` at the prompt reports 507,760 bytes free with FreeCOM swapped and
506,352 bytes with MS-DOS 4 COMMAND.COM. At 256 KiB installed the same disk
starts the shell and leaves about 53 KB free (`MEM` without swapping).

## Qualification performed for M20

HOST: two independent clean builds and a fresh-clone build per published
revision with identical D88 bytes; M20 host tests, linked-placement and
carrier verifiers, source/privacy audit; PC baseline (non-PC88VA kernel equal
to FreeDOS 1.4); native CI.

VAEG (private evidence): VA and VA2 at 640 KiB (shell, assembly, COM/MZ,
write/readback, MEM checks, kswap scenarios), VA2 at 256 KiB, VA at 384 KiB,
VA2 at 512 KiB installed with a retained 640 KiB selection, MS-DOS 4 COMMAND
through the menu, and the INT 33h/87h/88h/90h/95h vector behavior.

Not run for the final layout: F5/F8 startup keys, the utilities and archiver
disks with the final system disk, non-default `PC88VA_LOADSEG` values.
Hardware: NOT RUN by the project (DEFERRED HARDWARE VALIDATION).

## Source and record map

- [M20 report](m20-report.md) and [release notes](../releases/m20.md)
- [Build tools](../../tools/m20/README.md), [carrier builder](../../tools/m20/build_compressed_kernel.py),
  [linked-placement verifier](../../tools/m20/verify_m13_linked_placement.py)
- [Loader profile](../../config/m20/loader.json), [CONFIG.SYS](../../config/m20/CONFIG.SYS)
- Kernel component: `pc88va/kernel/machine_services.asm`,
  `pc88va/kernel/m13_segments.inc`, `kernel/segs.inc`, `kernel/main.c`
  (`setup_int_vectors`), `kernel/kernel.asm`, `hdr/mcb.h`
