# M16 conventional memory and boot layout contract

This is the current project-authored memory contract for M16, incorporating the
owner's 2026-09-27 RAM measurement and low resident-layout instructions. It
supersedes earlier sizing and placement instructions when maintaining M16.
Historical milestone identities, acceptance records and results remain unchanged.
This document describes source policy, not private firmware observations or a
claim that every capacity/workload has passed.

## Capacity, ownership and addresses

- Measure writable conventional RAM at boot. Restore one sampled byte after
  writing 00h/FFh per KiB from 256 KiB up to the 640 KiB cap, and check the final
  byte below 256 KiB as a minimum-capacity guard. This is capacity sampling,
  not an exhaustive integrity test or a discovery of free memory.
- Stage 2 measures before its first disk request and passes measured KiB and
  actual staging to the carrier. Kernel sizing uses the same native probe.
  Saved BIOS/backup selections must not determine or override the result.
- Installed RAM, saved selection, measured capacity and DOS-free memory are
  different quantities. In particular, writable RAM may still have an owner.
- `PC88VA_LOADSEG` is a hexadecimal paragraph address. It selects the expanded
  resident kernel base and the consecutive kernel work area. The default is
  1000h, physical 10000h. This lower bound is explicit platform policy, not a
  measured firmware footprint. A higher selection also excludes the region
  below it from the DOS arena; measurement does not reclaim that region.
- The current loader profile enters its first stage at physical 30000h and
  loads stage 2 at 12000h. These are temporary boot locations, not the final
  kernel base. Stage-1 and stage-2 stack/metadata ownership ends only at the
  corresponding handoff. Preserve the matched loader/carrier profile.
- IBM-PC INT 12h reports conventional capacity, not its free lower bound;
  INT 1Ah is not the memory-sizing interface used by common FreeDOS. The VA
  adapter does not synthesize IBM INT 12h/15h services. Common DOS MCB logic
  owns allocation and release; a BIOS service does not decide INIT's lifetime.

## Permanent low layout

Starting at `PC88VA_LOADSEG * 16`, retain consecutive resident code/data,
including the bounded NEAR work arena, then resident assembly and final FAR
kernel work. Buffer/file/drive tables and configured stacks use the common
system-block/sub-MCB allocator. Paragraph alignment and owned MCB/sub-MCB
headers are required structure, not unexplained reserved gaps.

The active runtime checks establish:

1. Resident end equals the first system MCB.
2. System MCB end equals the next free MCB, after all kernel-work allocations.
3. The initial free MCB reaches the temporary reservation without a hole.
4. After temporary release, adjoining free blocks coalesce before shell startup.

The startup diagnostics show measured memory, resident base, staging, carrier,
resident assembly, INIT and both temporary stacks. `Kernel low` and `Kernel work`
are end-exclusive ranges. `DOS free begins` is the address after the free MCB
header at that stage; it is not a guarantee that later child allocations cannot
change free memory. Resident assembly is one part of the kernel, not another
interpretation of LOADSEG.

## Temporary layout and release

For measured RAM end `T` (the first byte beyond RAM), the matched M16 profile is:

| Temporary object | Placement rule |
| --- | --- |
| Compressed file and in-place MZ carrier | `T - 19000h` |
| Scratch segment base | `T - 9000h` |
| 4 KiB decompression history ring | `T - 8000h` |
| Bridge stack top | `T - 10h` |
| INIT plus its 4 KiB stack, end exclusive | `T - 2000h` |
| INIT start | `T - 2000h - 1000h - align16(linked_INIT_bytes)` |

INIT is temporary and follows measured RAM independently of LOADSEG. All INIT
segment fixups and descriptor fields receive the same effective translation.
Resident references and the bootstrap stack instead follow the resident-base
delta. Reject wrapping or overlapping layouts before expanding the requested
target. Check all simultaneous loader, compressed input, expanded image,
bootstrap stack, ring, INIT and bridge-stack lifetimes; a single final-image
size is insufficient.

Early filesystem buffers are temporarily allocated below INIT. Final buffers
and tables replace them in the consecutive low work block. P_0 copies required
configuration, switches to its permanent stack, checks that no retained buffer
or drive table points into the reservation, then releases and coalesces the
reserved MCB before starting COMMAND.COM. INIT, retired images and old loader
workspaces must not become permanent holes. Moving INIT alone does not reduce
the permanent kernel/work footprint.

## Required qualification and evidence

- Clean-build the matched components, loader, carrier and complete media from
  pinned public sources twice; compare final artifacts. Use only M16 helpers.
- Verify the actual linked map, descriptor, every MZ fixup and each live interval.
  Exercise default and non-default LOADSEG through the real CONFIG.SYS path.
- Model unavailable/read-only RAM and stale saved selections. Include installed
  512 KiB with retained 640 KiB; verify byte/register/flag restoration and no
  bank-mapping changes. Synthetic boundary sizes do not establish hardware support.
- Cover the linked INIT formatter with SS different from DS. VA INIT requires
  qualified stack pointers and the Watcom separate-stack compilation option;
  plausible labels with zero/incorrect numeric arguments are not valid diagnostics.
- Check final low-work adjacency, MCB release/coalescing, wrong-stack/live-buffer
  rejection, shell startup, COM/MZ execution and guest file write/readback on
  the exact replacement candidate in the reported failing configuration.
- Record model, installed/retained capacities, LOADSEG and exact source/media
  identities separately. Test affected alternate models and a working-capacity
  control. Preserve workload failures, including low-memory resource shortages;
  a host placement pass or a historical capacity pass does not qualify the guest.
- Keep private runtime details in Git-excluded evidence. Distinguish HOST PASS,
  VAEG PASS, HARDWARE PASS and DEFERRED HARDWARE VALIDATION. Hardware not run is
  NOT RUN. Memory correction alone is not complete M16 acceptance.

## Source and record map

- [Build and placement usage](../../tools/m16/README.md)
- [Active M16 task](../tasks/M16-floppy-formats-console-input-goal-Codex.md)
- [Checkpoint/source identities](m16-report.md)
- [Component loader ABI](../../components/fdkernel/pc88va/boot/loader-abi.md)
- [Runtime carrier](../../components/fdkernel/pc88va/kernel/m16_runtime.inc)
- [RAM probe](../../components/fdkernel/pc88va/kernel/m16_memory_probe.inc)
- [Kernel allocation](../../components/fdkernel/kernel/config.c)
- [Temporary release](../../components/fdkernel/kernel/memmgr.c)
- [Linked-image verifier](../../tools/m16/verify_m13_linked_placement.py)

### Resident footprint policy

The VA build does not retain storage or handlers for the DOS CONFIG.SYS parser
while that parser is disabled. Its no-op DoConfig/DoInstall entry points retain
the existing behavior; the loader's PC88VA_LOADSEG handling remains separate.
The unused legacy loader-service object is excluded from the resident link.
Disk cache counts, transfer buffer capacities and the NEAR arena are unchanged.

The nominal M16 INIT stack end is 3e000h, translated with measured RAM at
runtime. Derive INIT start from its exact linked extent below that fixed stack
anchor, and reject overlap with staging. Shrinking INIT must not move the anchor
or depend on incidental rounding of the former INIT size.

### Boot machine banner

The model banner and its strings live entirely in M13_INIT_TEXT. The startup
call is also in INIT. No model string, cache or detector remains in DGROUP or
the resident platform group. The banner preserves registers, flags and ROM bank
selection; it restores the original bank before calling console firmware.

The interface precedent is public VAEG revision
`62a597f0ee81e2e036af740a3e79ad3da83e3fb7`,
[`generic/np2info.c`](https://github.com/nakatamaho/vaeg/blob/62a597f0ee81e2e036af740a3e79ad3da83e3fb7/generic/np2info.c),
[`io/memctrlva.c`](https://github.com/nakatamaho/vaeg/blob/62a597f0ee81e2e036af740a3e79ad3da83e3fb7/io/memctrlva.c), and
[`io/va91.c`](https://github.com/nakatamaho/vaeg/blob/62a597f0ee81e2e036af740a3e79ad3da83e3fb7/io/va91.c).
Internal ROM1 bank zero's identification word distinguishes VA from VA2/3;
the shared ROM-bank-status port identifies the VA upgrade board. Unrecognized
identification words display Unknown. This does not distinguish VA2 from VA3.
The linked verifier exercises synthetic VA, VA2/3, upgrade and unknown cases,
including bank and register restoration. Such checks are not hardware evidence.

### Legacy INIT assembly and the resident transfer buffer

The VA assembler segment declarations redirect legacy INIT_TEXT sections to
M13_INIT_TEXT after declaring the historical TGROUP. Startup, INIT interrupt
wrappers, CPU probing and interrupt-stack installation therefore share the
same relocated and discarded INIT lifetime as C initialization. Their resident
interrupt handlers stay in the low code group. Do not put the new INIT segment
in TGROUP or retain near calls across these independently placed groups.

The resident firmware transfer buffer is one 1024-byte sector, with a shared
assembly bound used by all request producers and the allocation. Read/write
entry points reject capacities exceeding this storage before the shared core
checks transfer lengths. DOS multi-sector requests are still split into
single-sector operations; 512-byte and 1024-byte sectors remain supported.
The decompressor's separate 4096-byte history ring is unaffected. The linked
verifier checks INIT ownership and read/write success and rejection cases with
buffer canaries. The ordinary DOS disk cache count remains twenty.
