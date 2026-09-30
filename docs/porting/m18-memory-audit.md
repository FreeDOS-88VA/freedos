# M18 scoped memory ownership audit

This source/lifetime ledger and its separately held matched guest/allocator
checks qualify the owner-scoped M18 memory gates, **not** a measured physical
map or an unsupported kernel memory saving. The kernel remains pinned at
`e87e8071c355a99a7f34a8758d4a3368b6523f3d`.
No kernel allocation, reservation, buffer budget or release policy was changed
in M18. The inherited [memory contract](m17-memory-layout.md) remains applicable.
Private runtime addresses and observations are retained separately.

## Ownership and lifetime ledger

All endpoints below are exclusive. Paragraph allocations include separately
accounted 16-byte MCB headers; byte lengths must not be rounded twice.

| Interval/object | Owner and purpose | Lifetime / source of truth |
| --- | --- | --- |
| Below `PC88VA_LOADSEG * 16` | Platform exclusion policy, including firmware/hardware ownership not enumerated by DOS | Not a free DOS allocation; default lower bound is policy, not measured firmware size |
| Measured physical capacity | Writable native conventional RAM, not necessarily available memory | Native capacity probe; retained backup selection is not its source |
| Resident image through `resident_text_segment` | Kernel DGROUP, resident platform code and bounded near work | Linked placement descriptor and exact linker map; permanent |
| Resident text through `CurrentKernelSegment + ceil(HMAFree/16)` | Resident assembly/common kernel | `PreConfig2()` computes the end; permanent |
| First MCB through `base_seg` | System-owned final FAR buffers, SFT/CDS and configured stacks | `KernelAlloc`, `PostConfig`, `configDone`; permanent, including owned subheaders |
| `base_seg` through `pc88va_boot_mcb` | Initially free DOS arena | `PreConfig2` and `configDone` check exact adjacency; later allocations change ownership |
| `pc88va_boot_mcb` through `pc88va_boot_top` | High temporary reservation: early buffers, INIT and INIT stack | Kept until permanent-stack `P_0` copies required configuration and releases it |
| Loader/staging/carrier/scratch | Native boot and expansion machinery | Carrier/loader live-interval rules; cannot be reclaimed while expanding or executing there |
| FreeCOM PSP and other FreeCOM-owned blocks | Shell, environment and runtime state | Common EXEC plus packaged FreeCOM; not a leak merely because there are multiple blocks |
| Child PSP/environment/runtime allocations | Running DOS child and its libraries | EXEC, allocation/resize calls and process exit; repeated post-warmup checks required |
| Free MCB payload | DOS-allocatable paragraphs | Current chain and common allocator; largest raw free MCB is not necessarily the largest executable |

### End-exclusive source interval equations

Let `L` be the effective `PC88VA_LOADSEG`, `T` the measured RAM top in bytes,
`R` the exact linked resident-text paragraph, `H = ceil(HMAFree/16)`,
`F = R + H` the first MCB paragraph, `B` the post-`KernelAlloc` low free-MCB
paragraph, `I` the actual linked INIT byte extent and `Q` the `lpTop`
paragraph at temporary-arena initialization. Quantities with unknown dynamic
ownership must be taken from the **same** linked map, descriptor and boot
instance; these equations do not turn measured writable RAM into free RAM.

| Source interval `[start, end)` in bytes | Length | Owner and lifetime |
| --- | --- | --- |
| `[0, L*16)` | `L*16` | Firmware/platform exclusion **policy**, not a measured free interval; permanent while DOS runs |
| `[L*16, R*16)` | `(R-L)*16` | Expanded resident image and its near work; becomes permanent at kernel startup |
| `[R*16, F*16)` | `H*16` | Resident assembly/text; permanent, exact linked extent only |
| `[F*16, B*16)` | `(B-F)*16` | First system MCB and final FAR kernel buffers/tables/stacks including owned metadata; permanent |
| `[(B+1)*16, (Q-1)*16)` | `(Q-B-2)*16` | Pre-shell free DOS MCB payload before releasing high INIT; allocation ownership may then change |
| `[(Q-1)*16, T)` | `T-(Q-1)*16` | Terminal high INIT/early-buffer reservation, owned until guarded `P_0` handoff; freed/coalesced only after its live references are gone |
| `[T-0x3000-align16(I), T-0x3000)` | `align16(I)` | Linked INIT image inside high temporary ownership; discarded at release |
| `[T-0x3000, T-0x2000)` | `0x1000` | INIT stack inside the high reservation; discarded after the permanent-stack switch |
| `[T-0x19000, T-0x19000+carrier_bytes)` | `carrier_bytes` | Temporary compressed file/carrier input during expansion; **may overlap the high reservation at different times**, never counted as a separate permanent DOS allocation |
| `[T-0x9000, T-0x8000)` | `0x1000` | Temporary decompressor scratch, from the actual linked carrier placement |
| `[T-0x8000, T-0x7000)` | `0x1000` | Temporary decompressor history ring; **adjacent to** scratch, not contained in it |
| `[T-0x1010, T-0x10)` | `0x1000` | Temporary bridge stack; not live together with the final shell stack |
| `[T, 0x100000)` | `0x100000-T` within the conventional 1-MiB address bound | Not present as writable conventional RAM for this capacity; no DOS MCB entitlement |

The early public loader profile independently bounds stage-2 code in its
`stage2` region and the loader stack in `loader_stack`. Those may overlap the
*later* expanded resident image only after the loader stops using them: interval
arithmetic without a lifetime is not an overlap safety proof. The profile's
firmware regions, native bank mapping, VRAM and ROM are not discoverable from
MEMMAP and are **not** included in its DOS-arena totals. The temporary INIT
image/stack, carrier, ring and scratch rows intentionally overlap their
*enclosing* high reservation in different phases, but the actual scratch and
ring are separate adjacent 4-KiB intervals. The linked INIT start must be
checked beyond the ring's end. Do not sum an enclosing reservation with its
subintervals as distinct concurrent occupied bytes. Actual kernel-work/FAT buffer allocation uses the
exact map, BIOS-measured `T` and configured buffer/file counts; it is not a
hard-coded free-memory promise. Runtime PSPs and environments are independently
checked against each observed MCB chain, and the largest raw MCB remains
separate from a practical EXEC capacity.

### Application demand is not just a linked length

The M18 distribution's package manifest records each DOS MZ utility's actual
source file SHA-256 and the **entry lower bound** derived from its header and
the pinned FreeDOS `DosExeLoader()` source. That loader allocates
`16 + (exPages * 32 - exHeaderSize) + exMinAlloc` paragraphs for the child's
PSP block at minimum; `exPages` rounds the *entire last MZ file page*. Its
header consumes one additional MCB paragraph and its cloned environment needs
a separate allocation. On the current build the lower PSP-block bounds are:

| Source-built tool | Required PSP block at EXEC entry | Observed native capacity scope, not a full peak |
| --- | ---: | --- |
| MORE | 20,896 bytes | `MORE /?` at 256 KiB; 512-KiB VA/VA2 paging and subsequent checked shell command; earlier high-capacity paging |
| MEMMAP | 22,528 bytes | checked MCB traversal at 256, 384, 512 and 640 KiB; its own Watcom heaps are trimmed before the report |
| EDLIN | 35,696 bytes | edit/save/reopen at installed 512 KiB with a stale larger retained setting on both VA and VA2; earlier VA 384-KiB and VA/VA2 640-KiB edit runs; **256-KiB load failed with explicit Watcom OOM/abnormal exit** |
| CHKDSK | 38,112 bytes | read-only 2HD B: check on both VA/VA2 at installed 512 KiB; earlier other-capacity B: checks; A: stdout redirection is issue #12 and NOT PASS |
| FORMAT | 45,072 bytes | destructive 2HD B: operation at installed 512 KiB on both VA/VA2; earlier VA 384-KiB and high-capacity results; 256 KiB insufficient |
| SYS | 68,464 bytes | 2HD B: transfer and exact SYS-produced boot/write/readback at installed 512 KiB on VA/VA2; earlier VA 384-KiB and high-capacity results; 256 KiB insufficient |
| JWASMR | 330,048 bytes | sample COM/MZ builds pass at 640 KiB; at installed 512 KiB in both models DOS rejected the EXEC allocation without executable output and preserved the checked shell/MCB chain; 512-KiB assembly is NOT PASS |

The owner accepts that 256 KiB is too little for EDLIN editing; the qualified
editor workload floor is 384 KiB on VA. The 256-KiB machine remains supported
for the separately qualified DOS shell and small utilities. EDLIN's observed
low-memory failure is not an open port-repair issue. The owner narrowed further
capacity review to installed 512 KiB rather than an exhaustive per-tool minimum
matrix. Existing evidence at other capacities remains scoped history; the
512-KiB JWASMR allocation failure is not silently promoted to a successful
minimum. The owner accepted 640 KiB **installed** as the qualified minimum
among the tested native capacities for the bundled small assembler samples;
this does not guarantee that larger sources fit. Keep functional 512-KiB
boot/editor/native maintenance and assembler safe-failure results separate.

All byte counts above are public-source-derived, **not** private guest-memory
measurements or total installed RAM requirements. A Watcom `exMaxAlloc=FFFFh`
can reserve substantially more than the listed minimum at EXEC. The source
bounds exclude input, environment, filesystem and runtime heap growth; a
successful boot, help banner, or file load alone does not measure an in-program
peak. The owner removed the requirement to establish in-program useful-memory
usage or its runtime peak for M18; **no peak measurement is claimed**. Continue
to qualify functional native-capacity success/failure and stable DOS ownership.
Keep the actual success/failure evidence bound to the exact normal D88,
emulator and RAM setting. The standalone inspector's synthetic negative tests
cover truncated and drifted MZ headers, rounded last pages and bad entry/stack
boundaries. Do not subtract this table from physical capacity to claim a
maximum executable size.

The known source contract does not authorize reclaiming the low policy exclusion
or merging across FreeCOM/system allocations. Hardware holes, unavailable memory
and any unconfirmed region remain outside MEMMAP's physical-memory claim.

## Release barrier reviewed

`kernel/config.c:PreConfig2` checks descriptor version, image/resident placement,
INIT SS, RAM-top arithmetic and a nonoverlapping temporary envelope. It sets
`LoL->first_mcb` at the resident end and creates a separate system-owned terminal
reservation. `PostConfig` allocates final buffers, file tables, CDS and stacks.
`configDone` checks resident/system/free/temporary adjacency; it does not count
padding or headers as free payload.

`kernel/task.c:P_0` copies the shell name/tail to resident storage before calling
`pc88va_release_boot_memory`. The VA exec block uses an explicit SS-based FAR
pointer. `kernel/memmgr.c:pc88va_release_boot_memory` checks the permanent stack,
final buffers/CDS below the temporary limit, the intervening chain, and the
terminal reservation's type, owner and exact end. Failure remains an error, with
a resident diagnostic. Success frees the reservation, clears its remembered MCB,
and joins an adjacent free predecessor. This source path is inconsistent with
assuming that all high INIT memory is intentionally permanent. It is not by
itself proof that every possible retained vector/device pointer has been audited.

`joinMCBs` combines only consecutive free blocks. `DosMemAlloc` calls it while
searching; adjacent free blocks need not already appear merged in a snapshot.
Do not patch the common allocator solely to force an eagerly coalesced display.

## Observer overhead is runtime state

The MEMMAP build verifies linked image, stack and MZ allocation fields, and sets
MZ maximum allocation equal to minimum allocation. That bounds the **initial DOS
EXEC allocation**, not all subsequent C-runtime requests. The exact linked
Open Watcom 1.9 map includes `__CMain_nheapgrow`, `__ExpandDGROUP`, `_nheapgrow`
and far-heap allocation support. The runtime may enlarge its own PSP block and
allocate separate blocks before MEMMAP's observation point.

Consequently:

- Account for all blocks owned by the current MEMMAP PSP, including environment
  and library allocations, rather than substituting the MZ minimum.
- Never manually shrink the process back to the linked minimum after startup
  without establishing current stack/heap ownership; that can free live storage.
- Prime stdout before measurement so its buffering is represented consistently.
- Compare matching redirected/unredirected observation points and warmup state.
- Footprint reduction must use audited runtime ownership, clean source builds
  and exact guest checks. No speculative trimming is accepted here.

The original initial-allocation policy did not meet the goal's runtime trimming
requirement. The next implementation uses the pinned Open Watcom 1.9 C Library
Reference, page 393: `_nheapshrink` and `_fheapshrink` return only free entries at
heap ends to DOS; zero is success and nonzero is error. Both run after stdout
priming and before traversal, with an error exit instead of a validity claim if
trimming fails. No MCB is edited and no numerical linked minimum is passed to
AH=4Ah. A synthetic integration test enforces prime/trim/walk ordering and both
failure paths; it is not a reimplementation of the Watcom heap manager. Later
exact-disk VA/VA2 guest checks independently parsed valid chains and matched
post-warmup ownership across repeated children. They qualify this scoped
observer correction, not an unmeasured in-program memory peak.

The build record also distinguishes the compact linked-image requirement from
`DosExeLoader`'s initial whole-file-page allocation. That existing FreeDOS
rounding policy is preserved, not changed to match MS-DOS or an estimate.
This is an observer-footprint correction, not evidence of a permanent kernel
leak or proof that a reported maximum block equals practical child capacity.

## Later matched private controls

The exact `b772f72` public-input candidate was booted in matched VA and VA2.
Independent DOS-written before/after MCB snapshots keep all address, owner,
size, type, summary and bound fields equal across the editor/assembler and
COM/MZ workflow. Descriptive bytes in MEMMAP's own MCB name vary, so raw
before/after text is **not** falsely described as byte-identical. The
post-warmup snapshots around further repeated COM/MZ execution are byte-identical.
A separate bounded QA application tested DOS allocation, fragmentation,
coalescing and near-limit EXEC at supported low/high configurations, with
stale larger retained memory selection tested separately from installed RAM.
The allocator checks both guard contents and owner links without modifying an
MCB. Source-backed conventional-memory release is unchanged: the adapter's
boot-time temporary reservation is released at its guarded handoff; no further
kernel reclaim has been demonstrated. Private numerical observations and full
runtime records are held separately. The linked footprint, active DOS heap,
MCB payload, and practical executable budget remain different quantities.

## Qualified boundaries and explicit unknowns

Source-bound allocator QA media covered real DOS 48h/49h/4Ah
allocation/free/resize, fragmentation/coalescing, near-boundary COM/MZ EXEC,
owner links, low-memory failure recovery and repeated children without
reclaiming someone else's block. The exact normal disk was separately booted
on VA and VA2: post-warmup and post-repeated-child MCB ownership agreed at
installed 640 KiB; installed 512 KiB with a stale retained larger selection
preserved checked ownership after EDLIN and bounded JWASMR EXEC rejection.
Matched guest results and numbers stay in Git-excluded evidence; the public
carrier descriptor, release barriers, linker map, runtime capacity check and
end-exclusive source equations bind permanent versus temporary owners.

There is **no demonstrated stale permanent reservation** or measured kernel
saving, and no kernel memory code changed. A writable top is not proof that
unknown firmware/VRAM intervals or lower-policy exclusions are allocatable.
The owner accepted 256-KiB EDLIN editing as unavailable and limited further
functional workload review to 512 KiB; the small edit/assemble/run workflow
needs 640 KiB *installed*, not just retained. The owner removed in-program
useful-memory usage and instantaneous disk-workspace peak measurements as M18
gates; both remain **NOT MEASURED**. MZ EXEC-entry floors and settled FAT
workspace snapshots are not relabeled as peaks. No complete physical map,
arbitrary-source assembler capacity or real-hardware result is claimed.
