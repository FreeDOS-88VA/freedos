# M16 work checkpoint

Status: partial implementation; not milestone acceptance or HANDOFF READY.

## Low resident layout revision

The conditional low-INIT experiment has been replaced. The resident kernel
starts at LOADSEG and final kernel work grows consecutively after its resident
hull. Runtime checks bind the resident end, system block, work end and free MCB.
Temporary INIT follows measured RAM top independently of LOADSEG; all INIT
fixups and descriptor fields follow that address. P_0 releases temporary memory
before shell startup. The identities and host verification below bind this
revision. ROM-dependent guest evidence is kept separately in local storage.

## Source identities

- Placement implementation parent: `d1da2bb7aeaf3da9709e6de7e496f9a056aaadc8`.
- Kernel: `58592e45fbe66c74b1b176c472869a4cf414bf40`.
- FreeCOM: `29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e`.
- COUNTRY.SYS: `23f189cca3420606eae8723884fa92ccd65eb307`.
- Toolchain image: `sha256:51a0b466cdc32377f3d2bec8e6e5432428fce13813723de3ce185eac989698df`.
- Unicorn verifier: 2.1.4, wheel SHA-256
  `9d6e6dea140560de4ebd8446661f7ef84a357d428c14a3ef09dacd306ec8c239`.

These are implementation/build identities, not substitutes for the separate
START_SHA, QUALIFIED_IMPLEMENTATION_SHA, PUBLICATION_TIP_SHA, and
DOWNSTREAM_BASE_SHA required at milestone acceptance. Final publication identity
and exact-head CI results must be reported after push; this file cannot contain
its own commit identity.

## Memory and loader correction

The platform measures writable conventional RAM using restored one-byte 00h/FFh
samples at 1 KiB intervals above 256 KiB, with a minimum-capacity guard.
Retained firmware configuration is not a writable-RAM measurement. Stage 2 runs
the probe before reading disk data and derives carrier staging from measured
RAM end. The carrier consumes the measured size and actual staging address.

`PC88VA_LOADSEG` selects the expanded resident kernel's base, including its C
code and data. Resident assembly and the bootstrap stack translate with that
base. The expanded input image must fit wholly below the temporary carrier.
INIT and its stack end at measured RAM top minus 8 KiB independently of LOADSEG.
INIT references and the descriptor receive a separate validated translation.
Final FAR kernel work grows from the resident end, followed by the free MCB.
The runtime invariant rejects a gap or malformed boundary. Early buffers,
INIT and its stack remain reserved until P_0 releases them before the shell.
Startup displays measured RAM, effective placement and the final low work range.
See [the current memory contract](m16-memory-layout.md) for ownership and
qualification, and `tools/m16/README.md` for build/configuration usage.

## Public host verification

Local **HOST PASS**, scoped to the source build and synthetic checks below:

- Two complete builds from allowlisted Git source exports, with historical
  milestone directories absent, produced identical artifact manifests and D88.
- Real stage-2 code measured RAM before its first disk read and selected the
  corresponding file/MZ target at 256, 384, 511, 512 and 640 KiB.
- The actual linked carrier reached the kernel with every final segment fixup,
  placement descriptor, boot record and stack checked at these capacities.
- CONFIG.SYS selector parsing covered default, non-default, malformed and
  duplicate values. Carrier checks covered non-default 2000h through 5000h
  bases at 512 KiB and rejected unavailable/overlapping layouts. Each case
  checked the independent INIT position and every final MZ fixup.
- Linked temporary-release checks verified coalescing into the free arena and
  rejected live-buffer, wrong-stack, bad-owner and malformed-chain cases.
- Memory probes restored sampled bytes and preserved registers/flags without
  bank I/O, including synthetic unavailable RAM and stale saved selections.
- The actual linked INIT formatter produced decimal and hexadecimal values
  with SS different from DS. Its VA-specific far argument/buffer pointers and
  Watcom separate-stack option are both required; the earlier binary fails
  this regression. This corrects the VA layout integration, not upstream DOS.
- The full build also ran the milestone-local carrier, loader, media and
  console regression suites.

Candidate D88: 1,331,888 bytes; SHA-256
`3c6106b93bffa6d323512626aa996a7707bd5ce1bdfa4a2135c9186f594d5109`.
This is a source-built candidate, not a designated milestone distribution.
No generated disk, binary or test log is committed by this checkpoint.

Rebuild from the implementation revision with the documented public toolchain:

```sh
python3 tools/m16/toolchain.py
python3 tools/m16/build_image.py --output build/m16-image
```

The resulting `build.json` binds full source identities, source archives,
toolchain, verifier and artifacts. ROM-dependent validation is separate from
this build and its canonical evidence remains in Git-excluded local storage.
The public host checks alone do not establish VAEG PASS or HARDWARE PASS.

## Remaining acceptance work

- Exact publication-head native CI and remote/source-binding checks.
- Complete M16 acceptance, including the remaining normal-speed console repeat
  and mode-switch investigations; this memory correction is not full acceptance.
- Private guest verification required by the RAM-dependent replacement rule is
  tracked separately; no private traces or derived observations appear here.
- Hardware: **NOT RUN**; **DEFERRED HARDWARE VALIDATION**.

## Resident footprint cleanup (2026-09-27)

Implementation parent: `fa18bba6f9abbd1d8c3b942a8143d324e3171eac`.
Kernel: `9573300a871adfa3d070102c8967cffbad1c5326`.
The component lock records the exact public source archive identity.

The PC-88VA build omits the already-disabled DOS CONFIG.SYS parser, its
menu/INSTALL/line storage and constants, and the unused legacy loader-service
object. The pre-kernel LOADSEG directive remains owned by the loader. Other
platforms retain their existing parser; buffer counts, transfer capacities and
the bounded NEAR work arena are unchanged. No NEAR data is moved across DS groups.
The smaller INIT exposed an incidental code-size dependency in the builder:
M16 now explicitly preserves the nominal 3e000h stack-end anchor and checks
that the exact INIT extent fits above live staging before runtime translation.

Public linked-image accounting, with the same default work allocations:

| Region | Previous bytes | Current bytes |
| --- | ---: | ---: |
| Resident kernel | 76480 | 70032 |
| Final kernel work including allocator metadata | 24144 | 24144 |
| Combined permanent allocation | 100624 | 94176 |
| Temporary INIT code | 16146 | 9939 |

The permanent allocation shrinks by 6448 bytes (6.296875 KiB), to 91.96875 KiB.
Remaining low bootstrap INIT, live fixed data, and transfer buffer sizing are
not changed by this cleanup. This is not an exhaustive lifetime conversion.

Two independent complete builds from allowlisted source exports produced
identical artifact manifests and D88 bytes. The linked-placement/carrier checks
and maintained M16 build gates completed successfully in both containers.
Candidate D88: 1331888 bytes, SHA-256
`e80e918718f5d7c7b21fa5cb6b705a6121d684922c9f6cdc4b6be911c8cf8738`.
Toolchain image: `sha256:51a0b466cdc32377f3d2bec8e6e5432428fce13813723de3ce185eac989698df`.
Rebuild with the documented `tools/m16/build_image.py` entry point at the
implementation revision. This candidate is not a designated milestone archive.

Shrinking DGROUP exposed the VA shell handoff's unreachable F5/F8 command-tail
rewrite, which passed a stack-local buffer to NEAR memory/string helpers while
INIT has SS different from DS. The VA path now omits that inactive rewrite.
Resident release-barrier diagnostics identify the failing lifetime condition
while preserving the error-return contract. Earlier cleanup candidates are
superseded and must not be treated as guest-qualified replacements.

Scoped VAEG PASS: shell startup, COM/MZ execution, file write/readback and
runtime layout checks on the private qualification cases, including the pristine
candidate. Exact machine configurations, retained settings and raw evidence stay
in excluded storage. This does not extend to unrun configurations. Record the
publication tip's own native CI result separately after pushing it.
Hardware is NOT RUN. Overall M16 acceptance remains partial; this cleanup does
not qualify the outstanding console and media matrix.

## Discardable machine banner (2026-09-27)

Implementation parent: `1de6e384d709779d6abb6afee0a2aa53374063a0`.
Kernel: `d4ccada2c5042d584bda672573ae7e2562459e15`.
The boot banner selects VA, VA2/3, VA + verup board (PC-88VA-91), or Unknown
from the public interfaces documented in m16-memory-layout.md. The code,
strings and call site are all discardable INIT inputs. No persistent model
cache is allocated. The linked verifier covers all four branches and checks
ROM-bank, flags and register preservation.

Compared with the preceding cleanup candidate, the resident kernel remains
70032 bytes, final kernel work remains 24144 bytes, and their combined
allocation remains 94176 bytes. At default LOADSEG the free payload still begins
at 26ff0h. INIT alone grows from 9939 to 10139 bytes; its stack-end anchor is
unchanged. This addition therefore consumes no additional conventional memory
after initialization.

Two complete clean exported-source builds produced identical artifacts and
D88 bytes, including successful linked placement, carrier and model-banner
verification. Candidate D88: 1331888 bytes, SHA-256
`f53a2d4f6e88091602498e3eff2995bc36d67c76ddeae52fcbef1f74e66bc2f4`.
The documented build entry point and locked toolchain are unchanged.
This candidate is not a designated milestone archive.

VA and VA2 startup labels were visually confirmed in private emulator runs.
Final guest operation qualification is recorded separately. Upgrade-board
and VA3-specific guest/hardware execution are NOT RUN; synthetic branch checks
do not establish those results. Hardware is NOT RUN. Record native CI against
the publication tip after push. Overall milestone acceptance remains partial.

## Legacy INIT and sector-buffer reduction (2026-09-27)

Implementation parent: `27935afa16b5eaea0e19461dbfef814b2419235b`.
Kernel: `6318d4c435c6f4ff48b5033bca3d910fe261b6f0`.
The legacy INIT_TEXT assembly now joins the discardable M13_INIT_TEXT group;
resident IRQ handlers retain their original lifetime. The resident VA disk
transfer buffer is reduced from 4096 to 1024 bytes with a shared capacity
constant and fail-closed read/write entry checks. The decompressor history
ring and the twenty DOS cache buffers are unchanged.

Linked resident bytes fall from 70032 to 66224. With 24144 bytes of final
kernel work, the combined allocation falls from 94176 to 90368 bytes, or
88.25 KiB: a reduction of 3808 bytes. Temporary INIT grows from 10139 to
10955 bytes, including group alignment, and is released as before. At default
LOADSEG the free payload begins at 26110h.

Two complete clean exported-source builds produce identical artifact manifests
and D88 bytes. The linked verifier confirms the moved assembly lifetimes and
executes both real disk wrappers/cores with synthetic firmware callbacks:
512/1024-byte success, oversized sector/count/capacity rejection, and buffer
canaries. Carrier and maintained build gates also complete successfully.
Candidate D88: 1331888 bytes, SHA-256
`b072cbe825444bfaa28deafe4f74e5fcce0542cfdeea79669f6427cd3d73ee91`.
Reproduce using the documented M16 build entry point and locked toolchain.
This candidate is not a designated milestone distribution archive.

Guest scope is recorded separately against the exact candidate; source-level
and synthetic checks do not establish hardware behavior. Hardware is NOT RUN.
Record native CI against the publication tip after push. Overall M16 acceptance
remains partial.

## Ten KiB disk cache checkpoint (2026-09-27)

Implementation parent: `e512bf33258a590ce72c47842206243cedaca361`.
Kernel: `b17bd5a3a3ca095c194222a1d40cb709c28ef936`.
This supersedes the preceding twenty-buffer candidate. The VA platform default
is now ten 1024-byte cache buffers: 10240 bytes of sector data, 200 bytes of
buffer headers, paragraph alignment and one allocation header, totaling 10464
bytes. Other targets retain their existing default and the upstream cache
algorithm is unchanged.

The resident image remains 66224 bytes. Final kernel work falls from 24144 to
13712 bytes; their total is 79936 bytes (78.0625 KiB), including the disk cache
and 1024-byte firmware transfer buffer. Compared with the machine-banner
checkpoint, the combined INIT, transfer-buffer and cache changes save 14240
bytes (13.90625 KiB). Default LOADSEG gives consecutive resident/work bounds
10000h-202b0h-23840h and free payload beginning at 23850h. Temporary INIT remains
10955 bytes and retains the same stack anchor and release policy.

Two clean exported-source builds produced identical artifact manifests and
D88 bytes. Carrier, linked placement, INIT ownership, real read/write buffer
bounds and the maintained host gates completed successfully. Candidate D88:
1331888 bytes, SHA-256
`b5fec8cc4d0f117ddc8e8cb0cd9c6222b387e2effb274d3f0a9c7adcae03f882`.
Reproduce with the documented M16 build entry point and pinned toolchain.
This is a work checkpoint, not a designated milestone archive.

Native x64 CI run 36308460910, attempt 1, succeeded against the exact
implementation parent above, including the full two-build distribution gate.
Exact-candidate guest qualification and publication-tip CI bindings are retained
separately. Hardware is NOT RUN. Overall M16 acceptance remains partial; this footprint
change does not qualify the outstanding console and full media matrix.

## Legacy native FAT12 recognition candidate

The VA adapter now recognizes the explicit legacy native FAT12 profile without
a boot BPB, using read-only FAT reserved-entry checks in both copies and a read
of the profile endpoint before allowing normal block access. A plausible but
malformed BPB does not fall back to this path. Other targets are unchanged.
Original synthetic tests cover recognition and rejection; all 326 component
tests pass locally with Unicorn 2.1.4. The adapter test harnesses now consume
the production transfer-buffer size definition. Clean media builds, guest
qualification and exact-revision CI for this candidate remain pending.
This is not M16 PASS or HANDOFF READY.

## Corrected 2HC format contract

Public FDFORM/2HCDRV source reconciliation distinguishes the F1h native format
selector from the F9h BPB/FAT descriptor for the selected 15-sector 2HC format.
The M16 adapter and fixture configuration now use the FAT descriptor correctly;
see [the floppy contract](m16-floppy-contract.md) for exact public provenance.
A synthetic production-getbpb test rejected F9h and accepted F1h before the
correction; both positive and negative cases now pass. All 328 component tests
pass locally. Earlier F1h 2HC images do not qualify this corrected contract.
The preceding candidate completed both-model DOS key delivery, ordinary-key
repeat at paced/fast settings, and three VA/B: boundary/persistence rows. These
remain historical candidate results. The changed kernel requires a fresh clean
build and relevant exact-candidate guest qualification before acceptance.
M16 remains in progress; no final PASS or handoff is claimed.
