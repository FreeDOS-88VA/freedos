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
See `tools/m16/README.md` for the formulas and configuration syntax.

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
