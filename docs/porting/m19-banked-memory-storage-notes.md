# PC-88VA banked memory and EMS as off-arena storage

Status: research/design note only; no implementation or new qualification.

## Public references

- VA FAQ article 5, section 1.4, "Ways to use expansion RAM":
  <http://www.pc88.gr.jp/vafaq/view.php/article/88va/vafaq/5>
- VA FAQ article 36, section 4.1, "Memory boards usable on VA":
  <http://www.pc88.gr.jp/vafaq/view.php/article/88va/vafaq/36>
- Related VA FAQ article 39, section 4.4.1, "Bank-switching ports":
  <http://www.pc88.gr.jp/vafaq/view.php/article/88va/vafaq/39>

All three articles display a publication date of 1995-11-01. The following is
an original summary, not a verbatim republication. Historical compatibility,
software-library locations and availability statements are not current advice
or project PASS results. No private manuals, ROM contents or runtime traces
are reproduced.

## Article 5: two expansion-RAM models on VA

The FAQ describes two usable expansion-RAM models: I/O-banked memory and EMS.
It states that both can coexist.

### I/O-banked memory

- The bank window is the main-memory range `80000h–9FFFFh`; switching the bank
  number exposes another 128-KiB expansion bank there.
- Bank 0 is automatically used to fill VA main memory.
- Reported uses: RAM disk, disk cache, and (original VA only) a back-scroll
  buffer. On VA2/VA3 that back-scroll utility instead used an unused part of
  TVRAM.

### EMS

- EMS accesses expansion RAM through a window in the expansion-ROM area,
  normally four contiguous 16-KiB pages, 64 KiB in total.
- **On VA, the window commonly used is `C0000h` up to `D0000h`** (that is,
  `C0000h–CFFFFh`).
- An EMM driver must be registered in CONFIG.SYS. PC-98 commercial EMM drivers
  were used on VA by wrapping them between VA adapter drivers distributed in
  the VA user library. The article's example wraps a PC-98 I-O DATA EMM driver
  between two adapter drivers and passes a window-candidate list beginning at
  `C0` and extending through `D4` segment-high values. The list of candidates
  is a driver option, not proof that every listed address is safe on VA.
- Reported uses: EMS RAM disk; **swap space for an RSWAP utility that saves
  the parent process to EMS or a file while a child runs and restores it on
  return**; editor buffers/swap; and lower resident size or EMS history
  buffers for various tools.

### Memory wait states

The article reports that, on VA2/VA3, `80000h–9FFFFh` (when expanded from
512 KiB to 640 KiB) has a memory wait, about a 10% speed difference in its
benchmark. On the original VA, only slot-expanded memory had a wait and
`00000h–3FFFFh` was no-wait. These are historical measurements, not project
benchmarks.

## Article 36: memory-board compatibility

The FAQ reports use of both VA-specific boards and various PC-98 boards on VA,
and describes PC-98 boards as the basis for EMS expansion.

Reported board families include:

- NEC PC-9801-02N with PC-9805K, and PC-9801-31 with PC-9801-21N:
  main-memory expansion only.
- I-O DATA PIO-9234/G/P, PIO-9X34/P, PIO-9834 and PIO-PC34 families.
- Melco XCE and EMJ.
- NEOS NE-EMS and NS-EMS.

The article identifies PIO-PC34, EMJ, NE-EMS and NS-EMS as also usable for
EMS. VA-specific examples are NEC PC-88VA-01/-02, with 256 KiB increments, and
I-O DATA PIO-88VA-2MD, with 2 MiB; these are described as banked memory rather
than EMS boards.

It warns about slot power limits and software-configured boards, and reports
PIO-PC34R as unsuitable. These are historical reports, not universal guarantees
for every board revision, configuration or driver.

## Source discrepancy: do not silently choose a port

Article 36 gives `0ECh` for PC-98-style bank switching and `1DCh` for VA-style
switching. Article 39 instead gives `1D0h` for the VA-specific boards, including
its programming example; it also gives `0ECh` for PC-98 I/O-banked boards.

Retain this discrepancy. Establish the actual board/driver interface before
implementing a backend; neither article alone is a sufficient port contract.

## Bank window versus EMS page frame

- I/O bank window: `80000h–9FFFFh`, inside conventional memory. Selecting
  another bank hides bank 0, including any DOS code or data located there.
  Article 39 warns that switching code, interrupt targets and stacks must not
  live in the window and recommends disabling interrupts while switched.
- EMS page frame: commonly `C0000h–CFFFFh` on VA, above conventional memory.
  Article 39 says EMS pages must be selected through the EMS driver, not by
  touching board page registers directly.

On VA, `C0000h–CFFFFh` also lies within the bank-selected system-memory area
used for display and font access. Confirm with the chosen adapter/driver how
the EMS window coexists with those mappings, and never treat an apparently
unused range as free, writable RAM without that contract.

A page frame is a mapping window into backing storage, not extra permanently
resident conventional RAM. Backing capacity, installed conventional RAM and
retained BIOS selections are separate quantities.

## Intended FreeDOS use: XMS-like storage, not an XMS claim

The goal is to release conventional memory by storing suitable contents in
EMS/banked backing memory and copying them back when required. "XMS-like" here
means off-arena storage and move/copy operations; it does not claim an XMS
manager, XMS API compatibility or directly addressable linear memory above
1 MiB on the VA CPU.

The RSWAP use in article 5 is the closest historical precedent: it is the
same idea as the FreeCOM kernel-swap path, with EMS instead of conventional
memory or a file as the backing store.

Candidate contents include shell state, caches and explicitly owned buffers.
Cold code would require a separately designed overlay/reload contract. A saved
copy alone releases no memory: the corresponding conventional allocation must
actually be freed or reduced safely.

This is different from simply placing the whole kernel in a switchable frame.
Interrupt handlers, mapping/copy code, live stacks and all unmediated near/far
references must remain valid. Kernel or DGROUP objects must not be moved merely
because their bytes can be copied; such changes require explicit ownership,
pointer, placement and lifetime contracts while preserving the selected
FreeDOS baseline behavior.

## Required checks before implementation or acceptance

1. Identify the supported board, driver/adapter, frame address and backing
   allocation interface; resolve the port discrepancy for that configuration.
2. Reserve backing storage without colliding with other EMS users, firmware,
   display/font mappings or extension devices.
3. Keep mapping/copy routines and their stacks outside any window they replace;
   preserve registers, flags and prior mappings. Define interrupt/reentrancy
   handling rather than assuming CLI excludes every possible interruption.
4. Detect absent memory or drivers and allocation/map/copy failures safely,
   falling back to the existing conventional-memory behavior. Retained BIOS
   RAM selections must not supply or cap conventional capacity.
5. Measure actual conventional allocations released, restoration correctness,
   MCB integrity and application execution, not only backing-store capacity.
6. Rebuild and requalify the linked placement/carrier/layout contract if kernel
   bytes or placement change. Independently validate each supported RAM/board
   configuration; no emulator or hardware PASS is implied by this note.

Implementations belong in the appropriate pinned component repository. Public
build/media orchestration remains milestone-local under `tools/m19/`, with
settings and tests under `config/m19/` and `tests/m19/`. Existing releases and
qualified artifacts remain unchanged until separate acceptance.
