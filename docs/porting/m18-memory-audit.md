# M18 memory ownership audit (in progress)

This is a source review, not completed M18-MEMORY-MAP or allocator acceptance.
The kernel remains pinned at `e87e8071c355a99a7f34a8758d4a3368b6523f3d`.
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
failure paths; it is not a reimplementation of the Watcom heap manager. Actual
guest validation of this change is pending.

The build record also distinguishes the compact linked-image requirement from
`DosExeLoader`'s initial whole-file-page allocation. That existing FreeDOS
rounding policy is preserved, not changed to match MS-DOS or an estimate.
This is an observer-footprint correction, not evidence of a permanent kernel
leak or proof that a reported maximum block equals practical child capacity.

## Still required

A complete audit needs matched initialization/idle/child/termination snapshots,
byte-accounted permanent and temporary regions, all remaining gaps explained,
real 48h/49h/4Ah boundary/fragmentation/owner tests, practical COM/MZ EXEC limits,
repeated-child stability, supported-capacity and stale-selection regressions,
and measured per-tool/workspace requirements. Successful source review, MEMMAP
output or a single application workflow does not close these gates.
