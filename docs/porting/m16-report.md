# M16 work checkpoint

Status at this checkpoint: candidate qualification complete; designated archive
and final publication-tip checks are being closed. This is not yet M16 PASS or
HANDOFF READY.

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

The same public formatter also supplies a short BPB followed by IPL code.
The VA adapter now treats only its defined fields as metadata and validates
FAT headers plus the geometry endpoint when the MBR marker is absent. Original
short-BPB fixtures and positive/negative component tests cover the correction;
all 330 component tests pass locally. The preceding corrected-FAT candidate
completed the VA/B: 2HC boundary and fresh-process persistence row, but this
additional kernel change requires renewed exact-candidate guest qualification.

## Boot profiles and exact-candidate new-file verification (2026-09-28)

Parent implementation: `d4552868de2494b6b311c8610d88e71d2732eafa`.
Kernel component: `7883c8fac11fab20cb467ad0a93c8799f35b565a`.
The 512-byte first stage now reads its contiguous stage-2 extent one sector at
a time so the entire reader fits in the ROM-loaded boot sector. The 1024-byte
path retains the shared disk reader. M16 boot profiles use 512-byte sectors for
2D/2DD and 1024-byte sectors for 2HD. The 2HC 1200 KiB profile remains a data
volume; it is not designated as a boot profile.

Each row was built twice from the allowlisted committed inputs in separate
Linux/amd64 containers. The independent artifact manifests and final D88 bytes
matched. Host media readback verified every source payload, including the
multi-cluster kernel file.

| Boot profile | Sector bytes | Candidate D88 bytes | Candidate SHA-256 | VA and VA2 guest result |
| --- | ---: | ---: | --- | --- |
| 2D 320 KiB | 512 | 338608 | `602213713ec4df46255b447813abc2f1c1f06752eeccfd0a58a428b4d0fd5d0b` | boot, DIR, COM/MZ, new-file write/read and fresh-process reopen passed |
| 2D 360 KiB | 512 | 380848 | `69155cc74d7cb4e26ccc73164597a62961d5eb07c228b51aab628b403dd2b63b` | boot, DIR, COM/MZ, new-file write/read and fresh-process reopen passed |
| 2DD 640 KiB | 512 | 676528 | `207ddbd727a2df2cf87ee82cd8b5b302abdc3cf824a35a689d1754dadd2c75fe` | boot, DIR, COM/MZ, new-file write/read and fresh-process reopen passed |
| 2DD 720 KiB | 512 | 761008 | `08c060ecf9c3247d3437ac1c88f2b15f4bb918a1e4343cbe731eabf0d763c035` | boot, DIR, COM/MZ, new-file write/read and fresh-process reopen passed |
| 2HD 1232 KiB | 1024 | 1281968 | `82e8b8606382b5542603ce56bd1377556cba3fe666bd41f54481a0d100a2441d` | boot, DIR, COM/MZ, new-file write/read and fresh-process reopen passed |
| 2HD 1280 KiB control | 1024 | 1331888 | `d4cba918550638bed324128e86fda0bf96d5a19f2371b7dbdf8cbcf55e3fea57` | boot, DIR, COM/MZ, new-file write/read and fresh-process reopen passed |

VA2 screen confirmation for each boot profile:

| Profile | FreeDOS startup screen | `DIR` screen | `COPY` result visible on screen | Result |
| --- | --- | --- | --- | --- |
| 2D 320 KiB (512 B/sector) | FreeDOS prompt shown | Directory listing shown | `RAMCHECK.TXT` appears after `COPY`; `TYPE` shows its contents after a fresh boot | PASS |
| 2D 360 KiB (512 B/sector) | FreeDOS prompt shown | Directory listing shown | `RAMCHECK.TXT` appears after `COPY`; `TYPE` shows its contents after a fresh boot | PASS |
| 2DD 640 KiB (512 B/sector) | FreeDOS prompt shown | Directory listing shown | `RAMCHECK.TXT` appears after `COPY`; `TYPE` shows its contents after a fresh boot | PASS |
| 2DD 720 KiB (512 B/sector) | FreeDOS prompt shown | Directory listing shown | `RAMCHECK.TXT` appears after `COPY`; `TYPE` shows its contents after a fresh boot | PASS |
| 2HD 1232 KiB (1024 B/sector) | FreeDOS prompt shown | Directory listing shown | `RAMCHECK.TXT` appears after `COPY`; `TYPE` shows its contents after a fresh boot | PASS |
| 2HD 1280 KiB control (1024 B/sector) | FreeDOS prompt shown | Directory listing shown | `RAMCHECK.TXT` appears after `COPY`; `TYPE` shows its contents after a fresh boot | PASS |

For each profile/model, the guest booted the pristine candidate with
`RAMCHECK.TXT` absent, created it with DOS `COPY`, and displayed it with
`TYPE`. Host inspection compared its bytes with `COMDATA.TXT`. A separate fresh
VAEG process reopened each VA and VA2 image, displayed the directory and file
contents, and left the image unchanged. COM and relocated MZ output files also
matched their expected bytes. These results bind to the VAEG source commit
`62a597f0ee81e2e036af740a3e79ad3da83e3fb7` and Linux executable SHA-256
`c13cba54f95ae4b575495dd85194a43948bf59713ad1dede0d717dc072482dbf` recorded
in `config/m16/vaeg-candidate.json`.

Scoped **HOST PASS**: six complete two-build profile runs from parent
`d4552868de2494b6b311c8610d88e71d2732eafa`, kernel
`7883c8fac11fab20cb467ad0a93c8799f35b565a`, toolchain image
`sha256:51a0b466cdc32377f3d2bec8e6e5432428fce13813723de3ce185eac989698df`,
and Unicorn wheel SHA-256
`9d6e6dea140560de4ebd8446661f7ef84a357d428c14a3ef09dacd306ec8c239`.
Scoped **VAEG PASS**: the six listed boot profiles on both VA and VA2, plus
fresh-process file readback on both models. VAEG CI run 36277471921 succeeded at
its exact source commit; kernel CI run 36360705941 succeeded at the exact kernel
commit; parent M16 isolated-source-build CI run 36363378815 succeeded at parent
report tip `be712ec153a6b0391fb9d19be0682e9501148bee`. Hardware is NOT RUN.
The boot-profile checks do not complete the remaining console cursor, repeat,
function-key, error-recovery, user-media, and handoff acceptance gates. Overall
M16 remains partial; this is not a designated milestone distribution.

## Data-media and memory regressions (2026-09-28)

The same source-built candidate completed the full data-media matrix on VA and
VA2. Each profile covered physical A: and B:, both BPB variants, cross-drive
copy in both directions, directory and subdirectory operations, preservation
of boot payloads, and fresh-process persistence readback.

| Data profile | Scenarios | Result |
| --- | ---: | --- |
| 2D 320 KiB | 8 | PASS |
| 2D 360 KiB | 8 | PASS |
| 2DD 640 KiB | 8 | PASS |
| 2DD 720 KiB | 8 | PASS |
| 2HC 1200 KiB | 8 | PASS |
| Total | 40 | PASS |

The startup-memory regressions passed with 512 KiB installed and a retained
640 KiB selection on VA and VA2, and with 640 KiB plus
`PC88VA_LOADSEG=2000` through CONFIG.SYS on VA. Captured startup displays show
the runtime-detected memory and effective kernel base; each case reached
FreeDOS and passed COM/MZ and guest file-copy readback checks. These results
qualify the active carrier, loader, and kernel candidate; they do not replace
hardware validation.

The remaining M16 gates at that checkpoint were normal console input/repeat,
GUI cursor/editor, media swap and error-recovery checks, physical B: checks,
the final handoff package, and the designated reproducible distribution archive.
Hardware is NOT RUN.

## Final candidate qualification checkpoint (2026-09-28)

This section supersedes the earlier checkpoint lists of pending guest work.
Those earlier sections remain as dated history. The exact qualified parent
implementation is `d4552868de2494b6b311c8610d88e71d2732eafa`, with kernel
`7883c8fac11fab20cb467ad0a93c8799f35b565a`, FreeCOM
`29bbbc7748e5c1b9a70fbc56c7faa33f6cd84c2e`, COUNTRY.SYS
`23f189cca3420606eae8723884fa92ccd65eb307`, and VAEG
`62a597f0ee81e2e036af740a3e79ad3da83e3fb7`. The exact Linux VAEG executable
SHA-256 is `c13cba54f95ae4b575495dd85194a43948bf59713ad1dede0d717dc072482dbf`.

The M15 starting revision is `1af9974700cd4dd1164cc0df56cc062925376148`.
The qualified implementation, designated artifact, and report do not alter the
M15 component baseline recorded by the M16 lock. The M17 task's preserved
starting revision is `fc891f3cd424c281680dd15b3f269bef4a4d2880`. The exact
publication tip and its post-push CI bindings belong in the post-push handoff;
this report cannot contain its own commit identity.

All guest and host checks below bind to the exact candidate hashes shown in the
boot-profile table above. For each of the six boot profiles, an independent
current-tip pair of clean builds produced byte-identical output and matched its
previously guest-qualified D88. The designated 2HD 1280 KiB image is archived
at `images/milestones/m16/freedos-pc88va-m16-2hd-1280.d88.xz`; the compressed
SHA-256 is `6be8c3e0d85d2182cf5ad2c48cdffba8880b6b29026777c5e1bfc9df721e579b`,
and the extracted D88 SHA-256 is
`d4cba918550638bed324128e86fda0bf96d5a19f2371b7dbdf8cbcf55e3fea57`.
`xz --test` passed, and decompression was compared byte-for-byte with the
source-built candidate. Its reproduction instructions and source/toolchain
binding are in the adjacent `README.md` and `manifest.json`.

The final candidate gates are:

| Gate | Evidence and result |
| --- | --- |
| M16-PLAN / M16-BASE | New M16 numbering is recorded; old M17 storage-contract work remains separately identified. The pinned M15 component baseline and M16 source lineage are retained. PASS |
| M16-MEMORY | Writable RAM probe restores sampled memory; retained stale 640 KiB selection with 512 KiB installed passed on VA and VA2. `PC88VA_LOADSEG=2000h` through CONFIG.SYS passed on VA with 640 KiB. Resident/work adjacency, temporary INIT release, diagnostics, COM/MZ and guest file readback checks passed. PASS |
| M16-VAEG-2D | VAEG commit `62a597f0ee81e2e036af740a3e79ad3da83e3fb7` includes native 2D D88 read/write and writeback coverage plus the VA TSP cursor change. Its CI run 36277471921 succeeded at that exact source revision. PASS |
| M16-FORMATS / M16-B-DRIVE / M16-PERSIST | 2D 320/360, 2DD 640/720 and 2HC 1200 data profiles completed 40/40 combinations across VA/VA2, A:/B: and both BPB layouts. Cross-drive copies, directory operations, payload preservation and fresh-process readback passed. PASS |
| M16-MEDIA | Media replacement/swap read and write checks passed on VA and VA2 for mixed profiles. The corrected not-ready and write-protect recovery matrix passed 12/12; each run returned to DOS, executed another command and preserved the boot/protected images. PASS |
| M16-CURSOR | Real FreeDOS/FreeCOM editing on VA and VA2 showed visible cursor movement and correct logical edits, including cursor-key and history-driven commands. The NEC documentation distinguishes cursor enable from per-sprite switch, but does not establish that cursor enable overrides a cleared sprite switch. That CE/SW=0 interaction remains unqualified; no hardware-level claim is made. Guest behavior gate PASS with this interaction limitation. |
| M16-REPEAT / M16-FKEYS / M16-NORMAL | Automated DOS byte-stream probes matched expected VA and VA2 input/repeat sequences at fast and paced settings. Normal FreeCOM exercised history/editing keys and returned correct commands on both models. PASS |
| M16-REGRESS | M16-maintained placement, loader, media, input, repeat and FreeCOM regressions ran in the clean source build. Kernel CI run 36360705941 succeeded at `7883c8fac11fab20cb467ad0a93c8799f35b565a`. Parent M16 run 36366637101 and scaffold run 36366637125 succeeded at `8253748a2a890d24c32a9eccc3027aad9aba67b3`. PASS for those exact heads. |
| M16-HANDOFF | Exact boot and data images, matching Linux VAEG, static MinGW64 build artifact, checksums, launch commands and test scope are assembled in Git-excluded local evidence storage. Exact publication-tip CI and remote checks are pending. |

The MinGW64 `mingw-release` artifact comes from VAEG CI run 36277471921 and
statically links SDL2 and the configured non-system dependencies. It has not
been run in a Windows guest acceptance session. VAEG guest qualification above
uses the identified Linux executable.

Evidence labels at this checkpoint: **HOST PASS** for the source-built media,
placement and maintained host regressions; **VAEG PASS** for the listed exact
candidate guest checks on VA and VA2. Physical hardware is **NOT RUN** and is
**DEFERRED HARDWARE VALIDATION**. Overall M16 acceptance and HANDOFF READY remain
pending final archive/publication review and exact-tip CI/remote verification.

The committed candidate record and all three strict M16 JSON Schemas are checked by
[`tools/m16/verify_acceptance.py`](../../tools/m16/verify_acceptance.py). Local
and native CI use the same candidate command. Its negative tests cover malformed
and duplicate JSON, invalid schemas, missing and unknown fields, malformed
identities, artifact size/digest drift, stale CI heads, failed jobs, and broken
ancestry. The final publication operation also checks the pushed remote tip,
the bounded diff from the qualified implementation, and exact CI attempts/jobs;
its self-referential publication identity is retained in Git-excluded handoff
metadata after push.
