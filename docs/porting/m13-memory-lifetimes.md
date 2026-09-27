# M13 memory lifetime convergence

Historical M13 design snapshot: references below to the then-current worktree,
fixed placement or unresolved lifetime dependencies describe that stage only.
For active M16 behavior and qualification, use [the M16 memory contract](m16-memory-layout.md).
Historical status and results below are preserved, not transferred to M16.

This is a source-level design note, not milestone acceptance. Private runtime
qualification and hardware results are not published here.

## Adopt the IBM-PC lifetime model, not its physical addresses

The common kernel separates permanent DOS state from temporary initialization
state. Its IBM-PC build compiles `dyninit`, `initdisk`, and other initializers
with `INITCFLAGS`. The common `PreConfig2` uses `DynLast()` and the actual
conventional-memory ceiling to construct an MCB arena. Without HMA loading,
the resident code must also fit below that ceiling; its lifetime does not end
when initialization completes.

PC88VA should follow these ownership rules:

1. Preserve the platform-owned low-memory intervals, with explicit owners.
2. Place the permanent kernel and its live NEAR data contiguously above them.
3. Start the DOS arena after the entire live resident extent, paragraph-aligned.
4. Keep temporary initialization code, stack, and early buffers owned until
   their last uses. Release their valid MCB only after switching stacks and
   copying every required value to permanent storage.
5. Coalesce the released region into the adjacent free MCB. Never count the
   initial loaded image, its retired copies, and the final resident image as
   three permanent reservations.

The current split-placement implementation already performs steps 2-5, with
a conservative low-memory floor. The code named `HMA_TEXT` remains conventional
memory in this PC88VA configuration; its name is not permission to use A20/HMA.

## Implemented initializer classification

The PC88VA makefile now selects `INIT_CFLAGS` for `dyninit.obj` and
`initdisk.obj`, matching their source-level lifetimes. The allocated DDT/DPB
objects remain resident. Moving the allocation *code* does not free its output.
The runtime disk implementation is `dsk.c`, not `initdisk.c`.

The actual linked-image verifier checks disposable and resident entry points
against the end-exclusive INIT interval using linear addresses. It rejects
missing symbols, an initializer left resident, and a permanent consumer placed
inside reclaimed INIT. Synthetic tests include aliasing segment:offset pairs
and invalid boundary cases. The existing bridge test verifies every enumerated
relocation at its final destination.

## Why IBM-PC layout cannot be copied verbatim

| Boundary | IBM-PC source contract | PC88VA constraint / action |
| --- | --- | --- |
| RAM ceiling | `init_oem`, INT 12h, optional EBDA handling | Use the platform memory-size contract. The loader placement ceiling must agree before any placement at the top of RAM. |
| Low reserved region | Platform IVT/BDA and the chosen load/PSP layout | The current floor is a conservative loader policy, not proof that every byte is firmware-owned. Qualify ownership before lowering it. |
| Initializer code | Common makefile uses `INITCFLAGS` | Move proven initializer modules into the existing disposable code group; keep FAR-call relocation checks. |
| Initializer data | Watcom INIT flags include `-ndI`, plus target INIT machinery | PC88VA uses a shared NEAR DGROUP. A wholesale `-ndI` change would change DS/pointer contracts. Split only after auditing users. |
| `DynLast()` | Marks the final dynamically allocated NEAR data | Other permanent PC88VA code follows the original Dyn/HMA area. Using DynLast as the arena base now would expose live code. |
| Root PSP/environment | Reuses the kernel's initial discardable prefix | PC88VA currently uses separate low workspace. Audit all PSP/environment users and prefix lifetimes before consolidating ownership. |
| Fatal output | Initialization formatter is normally disposable | PC88VA resident `init_fatal` still calls the INIT formatter. Keep that formatter live until the dependency is explicitly removed. |

The comparison above is source structure, not evidence that another machine's
firmware addresses, memory-size interrupt, or HMA behavior apply to PC88VA.

## Auditing the conservative low-memory floor

Treat the low prefix as several ownership classes, not one allocation:

- CPU vectors: persistent while interrupts may occur.
- Platform data, buffers, interrupt state, and any RAM-resident service code:
  persistent for every retained service and hardware-interrupt path.
- Kernel-owned process-zero PSP/environment: persistent kernel ownership,
  not firmware ownership.
- Loader-only workspace: potentially reclaimable after its final return,
  provided it is disjoint from every persistent owner.
- Unclassified padding or gaps: candidates for investigation, not free memory.

An absence of writes, zero bytes, or one successful boot does not establish
that an interval is reusable. An ownership record must include full physical
end-exclusive bounds, initialization producer, last consumer, and model/boot
configuration applicability. Outward paragraph rounding protects live ranges;
inward rounding determines allocatable gaps.

Once the persistent prefix bound is established, use one shared platform
placement contract to place the resident kernel immediately above it. Prefer
this contiguous arena to inventing disconnected free MCB chains. Rebind the
carrier, kernel placement descriptor, arena validation, and public synthetic
checks together. Do not simply lower a guard or import the IBM-PC load address.

The current low floor remains unchanged pending that ownership proof.

## Remaining implementation order

1. Close platform low-memory ownership, including asynchronous users and
   RAM-resident code. Keep any concrete private findings out of this document.
2. Consolidate process-zero PSP/environment into explicitly kernel-owned
   storage, if its full lifetime and call contracts permit it.
3. Derive the common placement floor from the qualified platform contract and
   validate before unpacking; do not rely on a later C check alone.
4. Separately partition INIT-only data and remove resident-to-INIT dependencies.
   Preserve shared device objects and active DOS stacks.
5. Re-run maximum-block allocation/fill/free, device I/O, repeated real shell
   commands, COM/MZ return, negative cases, and unchanged-media checks.

None of these later changes is claimed implemented by this note. Complete
M13 acceptance, CI closure, and hardware qualification remain separate gates.
